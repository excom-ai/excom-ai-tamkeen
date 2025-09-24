"""Fetch issues from JIRA using Atlassian Python API v3 and cache them locally."""

import os
import time
import json
from typing import Any, Dict, List, Optional
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dotenv
import pandas as pd
from atlassian import Jira

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


def get_jira_client() -> Jira:
    """Create and return a JIRA client with authentication for Jira Cloud."""
    if not all([JIRA_SERVER, JIRA_EMAIL, JIRA_API_TOKEN]):
        raise ValueError("Missing required JIRA environment variables")

    # Type assertions since we've validated they're not None above
    assert JIRA_SERVER is not None
    assert JIRA_EMAIL is not None
    assert JIRA_API_TOKEN is not None

    # Create Jira client for Cloud (v3 API)
    return Jira(
        url=JIRA_SERVER,
        username=JIRA_EMAIL,
        password=JIRA_API_TOKEN,
        cloud=True  # Important: This enables Jira Cloud mode and v3 API
    )


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
    jira_client: Jira,
    jql: str,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_retries: int = 3,
) -> List[Dict[str, Any]]:
    """
    Fetch all issues from JIRA using the enhanced_jql method with pagination.

    Parameters
    ----------
    jira_client : Jira
        Authenticated JIRA client.
    jql : str
        JQL query string.
    batch_size : int, optional
        Number of issues to fetch per request.
    max_retries : int, optional
        Maximum number of retries for failed requests.

    Returns
    -------
    List[Dict[str, Any]]
        List of JIRA issues as dictionaries.
    """
    all_issues: List[Dict[str, Any]] = []
    next_page_token = None
    total_fetched = 0
    total = 0
    batch_num = 0

    while True:
        for attempt in range(max_retries):
            try:
                # Use enhanced_jql for Jira Cloud v3 API
                result = jira_client.enhanced_jql(
                    jql=jql,
                    limit=batch_size,
                    nextPageToken=next_page_token,
                    fields="*all"
                )

                # Extract issues from the result
                if isinstance(result, dict):
                    issues = result.get('issues', [])
                    total = result.get('total', 0)
                    next_page_token = result.get('nextPageToken', None)

                    # Log details about the response structure for debugging
                    if batch_num == 0:
                        logger.debug(f"Response keys: {result.keys()}")
                        if issues:
                            logger.debug(f"First issue keys: {issues[0].keys()}")
                else:
                    logger.warning(f"Unexpected result type: {type(result)}")
                    issues = []
                    total = 0
                    next_page_token = None

                # Add issues to our list
                all_issues.extend(issues)
                total_fetched += len(issues)
                batch_num += 1

                # Log progress
                if total > 0:
                    log_progress(logger, total_fetched, total, "issues fetched")
                else:
                    logger.info(f"📊 Fetched {len(issues)} issues (batch {batch_num})")

                # Check if we've fetched all issues
                if not next_page_token or len(issues) < batch_size or total_fetched >= total:
                    logger.info(f"✅ Fetched all {total_fetched} issues")
                    return all_issues

                break

            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"Failed to fetch issues after {max_retries} attempts: {e}")
                    raise
                log_error_with_retry(logger, e, attempt + 1, max_retries)
                time.sleep(2**attempt)  # Exponential backoff

    return all_issues


def prepare_dataset(all_issues: List[Dict[str, Any]], jira_client: Jira) -> pd.DataFrame:
    """
    Prepare the dataset from JIRA issues.

    Parameters
    ----------
    all_issues : List[Dict[str, Any]]
        List of JIRA issues as dictionaries.
    jira_client : Jira
        JIRA client for field mapping.

    Returns
    -------
    pd.DataFrame
        DataFrame with processed issue data.
    """
    if not all_issues:
        logger.warning("No issues to process")
        return pd.DataFrame()

    # Get a mapping from field ID to unique human-readable field name
    field_id_map = get_field_id_map(jira_client)

    def extract_fields_from_issue(issue: Dict[str, Any]) -> Dict[str, Any]:
        """Extract all fields from a JIRA issue dictionary."""
        # Get the issue key
        issue_key = issue.get('key', '')
        result = {"Key": issue_key, "Jira": issue_key}

        # Extract fields
        fields = issue.get('fields', {})
        for field_id, value in fields.items():
            if field_id in field_id_map and field_id_map[field_id]:
                # Use the human-readable name with ID for uniqueness
                field_name = f"{field_id_map[field_id]} ({field_id})"
                result[field_name] = value
            else:
                # If field not in map, use the ID directly
                result[field_id] = value

        return result

    # Create DataFrame from issues
    df = pd.DataFrame(
        [extract_fields_from_issue(issue) for issue in all_issues]
    )

    # Set index if Key column exists
    if 'Key' in df.columns and not df.empty:
        df = df.set_index('Key')

    # Convert all columns to string for consistency
    for col in df.columns:
        df[col] = df[col].map(lambda x: str(x) if x is not None else "")

    logger.info(f"📊 Prepared dataset with {len(df)} issues and {len(df.columns)} fields")

    return df


def get_field_id_map(jira_client: Jira) -> Dict[str, str]:
    """
    Return a mapping from field ID to field name.

    Parameters
    ----------
    jira_client : Jira
        Authenticated JIRA client.

    Returns
    -------
    Dict[str, str]
        Mapping from field ID to field name.
    """
    try:
        # Try to get all fields from Jira
        fields = jira_client.get_all_fields()

        if isinstance(fields, list):
            # Create mapping from field ID to name
            field_map = {}
            for field in fields:
                if isinstance(field, dict):
                    field_id = field.get("id", "")
                    field_name = field.get("name", "")
                    if field_id:
                        field_map[field_id] = field_name
            logger.debug(f"Created field mapping with {len(field_map)} fields")
            return field_map
        else:
            logger.warning(f"Unexpected response format from get_all_fields: {type(fields)}")
            return {}
    except Exception as e:
        logger.warning(f"Error fetching field mapping: {e}")
        # Return empty mapping as fallback
        return {}