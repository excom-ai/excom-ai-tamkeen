# Load all from freshservice

import json
import os
import time
from datetime import datetime, timedelta

import dotenv
import pandas as pd
import requests
import requests.exceptions
from pandas.api.types import is_list_like
from requests.auth import HTTPBasicAuth

from logger_config import log_progress, log_success, setup_logging

dotenv.load_dotenv()

# Set up logging
logger = setup_logging("tamkeen.freshservice", use_color=True)

FRESHSERVICE_DOMAIN = os.getenv("FRESHSERVICE_DOMAIN")
API_KEY = os.getenv("FRESHSERVICE_API_KEY", "")
CACHE_FILE = "fresh_service_tickets.parquet"
CACHE_DURATION_HOURS = int(os.getenv("FRESHSERVICE_CACHE_HOURS", "24"))


def prepare_df_for_pandasql(df):
    """
    Prepare a DataFrame for use with pandasql by converting all list-like columns to JSON strings.
    """
    df_copy = df.copy()

    for column in df_copy.columns:
        # Check if this column contains any list-like values
        if any(is_list_like(x) for x in df_copy[column].dropna()):
            # Convert all list-like values to JSON strings
            df_copy[column] = df_copy[column].apply(
                lambda x: json.dumps(x) if is_list_like(x) else x
            )

    return df_copy


def is_cache_valid():
    """Check if cache file exists and is still valid."""
    if not os.path.exists(CACHE_FILE):
        return False

    # Check cache age
    cache_time = datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
    cache_age = datetime.now() - cache_time

    if cache_age > timedelta(hours=CACHE_DURATION_HOURS):
        logger.info(
            f"⏰ Cache is {cache_age.total_seconds() / 3600:.1f} hours old, refreshing..."
        )
        return False

    return True


ticket_status_map = {
    2: "Open",
    13: "Under Review",
    6: "Waiting for approvals",
    12: "In Development",
    11: "Waiting IT Action",
    3: "Pending",
    4: "Resolved",
    5: "Closed",
    10: "Awaiting External Support",
    8: "Request Evaluation",
    9: "Procurement Stage",
    14: "Waiting reviewer approval",
    15: "Waiting solution approval",
    16: "Waiting another department action",
    17: "Modification Needed",
    18: "Scheduled Action",
    19: "Pending Internal Processing",
    20: "Waiting initial approval",
}


def fetch_freshservice_tickets():
    """Fetch all tickets from Freshservice API."""
    logger.info("🎫 Fetching tickets from Freshservice...")

    tickets = get_api(
        "tickets", params={"include": "requester,department,requested_for,stats"}
    )

    agents = get_api("agents")
    # merge agents into tickets
    agents["responder_name"] = agents["first_name"] + " " + agents["last_name"]

    tickets = tickets.merge(
        agents[["id", "responder_name"]],
        how="left",
        left_on="responder_id",
        right_on="id",
    )

    # Drop *_id keys
    id_columns = [col for col in tickets.columns if col.endswith("_id")]
    tickets = tickets.drop(columns=id_columns)
    tickets = tickets.drop(columns=["id_y"])  # If you only need one
    tickets.rename(columns={"id_x": "ticket_id"}, inplace=True)

    tickets["status"] = tickets["status"].map(ticket_status_map).fillna("Unknown")
    tickets = prepare_df_for_pandasql(tickets)
    return tickets


def get_freshservice_tickets(force_refresh=False):
    """Get Freshservice tickets, using cache if available and valid."""
    if force_refresh or not is_cache_valid():
        df = fetch_freshservice_tickets()
        df.to_parquet(CACHE_FILE, index=False)
        logger.info(f"💾 Saved {len(df)} tickets to {CACHE_FILE}")
    else:
        logger.info("📤 Reading from cache...")
        df = pd.read_parquet(CACHE_FILE)
        log_success(logger, f"Loaded {len(df)} tickets from cache")

    return df


def get_api(endpoint, params=None):
    """Generic function to fetch paginated data from Freshservice API with optional query parameters."""
    url = f"https://{FRESHSERVICE_DOMAIN}/api/v2/{endpoint}"
    all_data = []
    page = 1
    per_page = 100  # Max allowed

    # Use a copy of params to avoid mutating the caller's dictionary
    query_params = params.copy() if params else {}
    query_params.update({"page": page, "per_page": per_page})

    while True:
        query_params["page"] = page
        try:
            while True:
                response = requests.get(
                    url,
                    auth=HTTPBasicAuth(API_KEY, "X"),
                    params=query_params,
                    timeout=60,
                )

                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", "60"))
                    logger.warning(
                        f"🔄 Rate limit hit. Retrying page {page} after {retry_after} seconds..."
                    )
                    time.sleep(retry_after)
                    continue  # Retry the same request

                break  # Exit retry loop on success

            if response.status_code != 200:
                logger.error(f"Error {response.status_code}: {response.text}")
                break

            response_json = response.json()
            page_data = response_json.get(endpoint, [])

            if not isinstance(page_data, list):
                logger.error("⚠️ Unexpected response format.")
                break

            all_data.extend(page_data)
            log_progress(logger, len(all_data), -1, f"{endpoint} page {page}")
            page += 1

            if (
                "link" not in response.headers
                or 'rel="next"' not in response.headers["link"]
            ):
                logger.info("✅ Last page reached (no next link).")
                break

        except requests.exceptions.RequestException as e:
            logger.error(f"🚨 Request failed: {e}")
            break

    log_success(logger, f"Retrieved {len(all_data)} records from {endpoint}")
    for data in all_data:
        if data["id"] == 19309:
            print(data)

    return pd.json_normalize(all_data)


def get_single_ticket(ticket: str) -> dict:
    url = f"https://{FRESHSERVICE_DOMAIN}/api/v2/tickets/{ticket}"
    query_params={"include":"conversations"}
    response = requests.get(
        url,
        auth=HTTPBasicAuth(API_KEY, "X"),
        params=query_params,
        timeout=60,
    )
    return response.json()


if __name__ == "__main__":
    print(get_single_ticket("19382"))
    df = get_freshservice_tickets(force_refresh=False)
    print(df[df["ticket_id"] == 19309])
#
# print("" "Freshservice tickets with departments:")
