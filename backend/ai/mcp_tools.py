"""MCP Tools for Tamkeen - LangChain Integration."""

import os
import json
import logging
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from langchain_core.tools import tool

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

try:
    import sys
    import os
    # Add parent directory to path to allow imports
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from mcp_handlers import JiraHandler, FreshserviceHandler, RefreshHandler
    from logger_config import setup_logging
except ImportError as e:
    print(f"Warning: MCP handlers not available ({e}). Tools will return mock data.")
    JiraHandler = None
    FreshserviceHandler = None
    RefreshHandler = None

# Initialize handlers if available
logger = None
jira_handler = None
freshservice_handler = None
refresh_handler = None

def initialize_handlers():
    """Initialize MCP handlers if not already initialized."""
    global logger, jira_handler, freshservice_handler, refresh_handler

    if logger is None and JiraHandler is not None:
        logger = setup_logging("tamkeen.tools", use_color=False)
        jira_handler = JiraHandler(logger)
        freshservice_handler = FreshserviceHandler(logger)
        refresh_handler = RefreshHandler(
            logger, jira_handler, freshservice_handler, queue_initial_load=True
        )

# Initialize on module import
initialize_handlers()

@tool
def force_refresh_fresh_service() -> str:
    """Force refresh Freshservice data from the API, bypassing cache.

    This tool queues a refresh request and returns immediately.
    The actual refresh happens asynchronously in the background.

    Returns:
        Status message indicating the refresh has been queued.
    """
    if refresh_handler is None:
        return "MCP handlers not available. Please ensure mcp_handlers are properly configured."
    return refresh_handler.queue_freshservice_refresh(force=True)

@tool
def force_refresh_jira() -> str:
    """Force refresh JIRA data from the API, bypassing cache.

    This tool queues a refresh request and returns immediately.
    The actual refresh happens asynchronously in the background.

    Returns:
        Status message indicating the refresh has been queued.
    """
    if refresh_handler is None:
        return "MCP handlers not available. Please ensure mcp_handlers are properly configured."
    return refresh_handler.queue_jira_refresh(force=True)

@tool
def get_data_status() -> Dict[str, Any]:
    """Get the current status of cached data for both JIRA and Freshservice.

    logger.info("[TOOL] get_data_status called")

    Returns information about:
    - Number of records currently loaded
    - Cache file ages
    - Last refresh times
    - Next scheduled refresh times

    Returns:
        Status information for both data sources.
    """
    if refresh_handler is None or jira_handler is None or freshservice_handler is None:
        return {
            "error": "MCP handlers not available",
            "jira": {"status": "unavailable"},
            "freshservice": {"status": "unavailable"}
        }

    # Get queue status from refresh handler
    queue_status = refresh_handler.get_queue_status()

    status = {
        "jira": jira_handler.get_status(),
        "freshservice": freshservice_handler.get_status(),
        "queue": queue_status,
        "current_time": datetime.now(timezone.utc).isoformat()
    }

    logger.info(f"[TOOL] Data status: JIRA={status['jira'].get('record_count', 0)} records, FS={status['freshservice'].get('record_count', 0)} records")
    return status

@tool
def get_single_ticket(ticket_id: str) -> Dict[str, Any]:
    """Retrieve a single Freshservice ticket by its ID.

    Args:
        ticket_id: The ID of the ticket to retrieve

    Returns:
        Ticket data as a dictionary
    """
    if freshservice_handler is None:
        return {"error": "Freshservice handler not available"}

    return freshservice_handler.get_single_ticket(ticket_id)

@tool
def query_fresh_service_tickets(excomai_sql: str) -> str:
    """Execute a SQL query on the Freshservice tickets dataframe.

    IMPORTANT: The dataframe is referenced as 'df' in SQL queries.

    Example queries:
    - Count all tickets: SELECT COUNT(*) FROM df
    - Get recent tickets: SELECT * FROM df ORDER BY created_at DESC LIMIT 10
    - Filter by status: SELECT * FROM df WHERE status = 'Open'
    - Get specific columns: SELECT ticket_id, subject, status FROM df

    Args:
        excomai_sql: SQL query string using 'df' as the table name

    Returns:
        JSON string containing query results
    """
    logger.info(f"[TOOL] query_fresh_service_tickets called with SQL: {excomai_sql}")

    if freshservice_handler is None:
        logger.error("Freshservice handler not available")
        return json.dumps({"error": "Freshservice handler not available"})

    try:
        result = freshservice_handler.query_tickets(excomai_sql)
        logger.info(f"[TOOL] Freshservice query returned {len(result)} chars")
        logger.debug(f"[TOOL] Result preview: {result[:200]}..." if len(result) > 200 else f"[TOOL] Result: {result}")
        return result
    except Exception as e:
        logger.error(f"[TOOL] Freshservice query error: {e}")
        return json.dumps({"error": str(e)})

@tool
def query_jira_demands(excomai_sql: str) -> str:
    """Execute a SQL query on the JIRA demands dataframe.

    IMPORTANT: The dataframe is referenced as 'df' in SQL queries.

    Example queries:
    - Count all demands: SELECT COUNT(*) FROM df
    - Get recent demands: SELECT * FROM df ORDER BY created DESC LIMIT 10
    - Filter by status: SELECT * FROM df WHERE status = 'In Progress'
    - Get specific columns: SELECT key, summary, status, priority FROM df

    Args:
        excomai_sql: SQL query string using 'df' as the table name

    Returns:
        JSON string containing query results
    """
    logger.info(f"[TOOL] query_jira_demands called with SQL: {excomai_sql}")

    if jira_handler is None:
        logger.error("JIRA handler not available")
        return json.dumps({"error": "JIRA handler not available"})

    try:
        result = jira_handler.query_demands(excomai_sql)
        logger.info(f"[TOOL] JIRA query returned {len(result)} chars")
        logger.debug(f"[TOOL] Result preview: {result[:200]}..." if len(result) > 200 else f"[TOOL] Result: {result}")
        return result
    except Exception as e:
        logger.error(f"[TOOL] JIRA query error: {e}")
        return json.dumps({"error": str(e)})

@tool
def get_current_time() -> str:
    """Retrieve the current Coordinated Universal Time (UTC).

    Returns:
        Current UTC time as ISO format string
    """
    return datetime.now(timezone.utc).isoformat()

def get_all_mcp_tools():
    """Get all MCP tools for use with LangChain.

    Returns:
        List of tool functions that can be used with LangChain
    """
    return [
        force_refresh_fresh_service,
        force_refresh_jira,
        get_data_status,
        get_single_ticket,
        query_fresh_service_tickets,
        query_jira_demands,
        get_current_time
    ]