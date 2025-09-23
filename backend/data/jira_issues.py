"""Fetch issues from JIRA and cache them locally."""

import os
import time
from typing import Any, Dict, List, Optional, cast
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dotenv
import pandas as pd
from jira import JIRA, Issue

from logger_config import (
    setup_logging, log_success, log_data_loaded,
    log_error_with_retry, log_progress
)

dotenv.load_dotenv()

# Set up logging
logger = setup_logging("tamkeen.jira", use_color=True)

# Constants
CACHE_FILE = "jira_issues_cache.parquet"
CACHE_METADATA_FILE = "jira_issues_cache_metadata.json"
DEFAULT_BATCH_SIZE = 100
DEFAULT_CACHE_DURATION_HOURS = 24

# Environment variables
JIRA_SERVER = os.getenv("JIRA_SERVER")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_JQL = os.getenv("JIRA_JQL")
JIRA_EMAIL = os.getenv("JIRA_EMAIL")


def get_jira_client() -> JIRA:
    """Create and return a JIRA client with authentication."""
    if not all([JIRA_SERVER, JIRA_EMAIL, JIRA_API_TOKEN]):
        raise ValueError("Missing required JIRA environment variables")

    # Type assertions since we've validated they're not None above
    assert JIRA_SERVER is not None
    assert JIRA_EMAIL is not None
    assert JIRA_API_TOKEN is not None

    return JIRA(server=JIRA_SERVER, basic_auth=(JIRA_EMAIL, JIRA_API_TOKEN))


def is_cache_valid(cache_duration_hours: int = DEFAULT_CACHE_DURATION_HOURS) -> bool:
    """Check if the cache is still valid based on age."""
    if not os.path.exists(CACHE_FILE):
        return False

    # Check cache age
    cache_age = time.time() - os.path.getmtime(CACHE_FILE)
    max_age_seconds = cache_duration_hours * 3600
    
    if cache_age >= max_age_seconds:
        logger.info(f"⏰ JIRA cache is {cache_age / 3600:.1f} hours old, refreshing...")
        return False
    
    return True


def query_issues(
    jql: Optional[str] = None, force_refresh: bool = False
) -> pd.DataFrame:
    """
    Fetch issues from JIRA and cache them locally using a Parquet file.

    Parameters
    ----------
    jql : str, optional
        JQL query string. If None, uses JIRA_JQL environment variable.
    force_refresh : bool, optional
        Force refresh the cache even if it's still valid.

    Returns
    -------
    pd.DataFrame
        DataFrame containing JIRA issues.
    """
    if not force_refresh and is_cache_valid():
        logger.info("📤 Reading JIRA issues from cache...")
        df = pd.read_parquet(CACHE_FILE)
        log_data_loaded(logger, "JIRA issues", len(df), "cache")
        return df

    # Use provided JQL or fall back to environment variable
    jql_query = jql or JIRA_JQL
    if not jql_query:
        raise ValueError("No JQL query provided")
    logger.info(f"🔍 Using JQL query: {jql_query}")
    try:
        jira_client = get_jira_client()
        all_issues = fetch_all_issues(jira_client, jql_query)
        all_issues_df = prepare_dataset(all_issues, jira_client)

        # Save to cache
        all_issues_df.to_parquet(CACHE_FILE)

        return all_issues_df
    except Exception as e:
        # If cache exists and there's an error, return cached data
        if os.path.exists(CACHE_FILE):
            logger.warning(f"Error fetching fresh data, using cache: {e}")
            return pd.read_parquet(CACHE_FILE)
        raise


def fetch_all_issues(
    jira_client: JIRA,
    jql: str,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_retries: int = 3,
) -> List[Issue]:
    """
    Fetch all issues from JIRA with pagination and retry logic.

    Parameters
    ----------
    jira_client : JIRA
        Authenticated JIRA client.
    jql : str
        JQL query string.
    batch_size : int, optional
        Number of issues to fetch per request.
    max_retries : int, optional
        Maximum number of retries for failed requests.

    Returns
    -------
    List[Issue]
        List of JIRA issues.
    """
    next_page_token = None
    all_issues: List[Issue] = []

    while True:
        for attempt in range(max_retries):
            try:
                issues = jira_client.enhanced_search_issues(
                    jql, nextPageToken=next_page_token, maxResults=batch_size
                )
                # Cast to List[Issue] since we expect a list of Issues from enhanced_search_issues
                issues_list = cast(List[Issue], issues)
                all_issues.extend(issues_list)
                
                # Check if there's a next page token for pagination
                if hasattr(issues, 'nextPageToken') and issues.nextPageToken:
                    next_page_token = issues.nextPageToken
                else:
                    break
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                log_error_with_retry(logger, e, attempt + 1, max_retries)
                time.sleep(2**attempt)  # Exponential backoff

        # Break if no more issues are returned or no next page token
        if len(issues_list) < batch_size or not next_page_token:
            break

        log_progress(logger, len(all_issues), -1, "issues fetched")

    return all_issues


def prepare_dataset(all_issues: List[Issue], jira_client: JIRA) -> pd.DataFrame:
    """
    Prepare the dataset from JIRA issues.

    Parameters
    ----------
    all_issues : List[Issue]
        List of JIRA issues.
    jira_client : JIRA
        JIRA client for field mapping.

    Returns
    -------
    pd.DataFrame
        DataFrame with processed issue data.
    """
    # Get a mapping from field ID to unique human-readable field name
    field_id_map = {
        field["id"]: f"{field['name']} ({field['id']})"
        for field in jira_client.fields()
    }

    def extract_fields_from_issue(issue: Issue) -> Dict[str, Any]:
        """Extract all fields from a JIRA issue."""
        result = {"Key": issue.key, "Jira": issue.key}

        for field_id, value in issue.fields.__dict__.items():
            if field_id in field_id_map:
                result[field_id_map[field_id]] = value

        return result

    # Create DataFrame from issues
    df = pd.DataFrame(
        [extract_fields_from_issue(issue) for issue in all_issues]
    ).set_index("Key")

    # Convert all columns to string for consistency
    # Using map instead of deprecated applymap
    for col in df.columns:
        df[col] = df[col].map(lambda x: str(x) if x is not None else "")

    return df


def get_field_id_map(jira_client: JIRA) -> Dict[str, str]:
    """
    Return a mapping from field name to field ID.

    Parameters
    ----------
    jira_client : JIRA
        Authenticated JIRA client.

    Returns
    -------
    Dict[str, str]
        Mapping from field name to field ID.
    """
    return {field["name"]: field["id"] for field in jira_client.fields()}
