"""JIRA-specific handlers and operations."""

import threading
from typing import Optional
import pandas as pd
from pandasql import sqldf
from data.jira_issues import query_issues
from logger_config import log_refresh_start, log_refresh_complete
import os


class JiraHandler:
    """Handler for JIRA-related operations."""
    
    def __init__(self, logger):
        self.logger = logger
        self.data: Optional[pd.DataFrame] = pd.DataFrame()  # Initialize with empty DataFrame
        self.data_lock = threading.RLock()
        
        # Try to load from cache immediately if available
        self._try_load_cache()
    
    def _try_load_cache(self):
        """Try to load data from cache file if it exists."""
        cache_file = "jira_issues_cache.parquet"
        if os.path.exists(cache_file):
            try:
                self.logger.info("📤 Loading JIRA data from cache on startup...")
                data = pd.read_parquet(cache_file)
                with self.data_lock:
                    self.data = data
                self.logger.info(f"✅ Loaded {len(data)} issues from cache")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to load cache on startup: {e}")
                self.data = pd.DataFrame()
        else:
            self.logger.info("📭 No JIRA cache file found on startup")
    
    def load_data(self):
        """Load JIRA data from cache without forcing refresh."""
        try:
            self.logger.info("📋 Loading JIRA data...")
            new_data = query_issues(force_refresh=False)
            with self.data_lock:
                self.data = new_data
            if self.data is not None:
                self.logger.info(f"✅ JIRA data loaded ({len(self.data)} issues)")
            else:
                self.logger.warning("⚠️ No JIRA data available")
        except Exception as e:
            self.logger.error(f"Error loading JIRA data: {e}")
            self.data = pd.DataFrame()  # Empty DataFrame as fallback
    
    def refresh_data(self, force: bool = True):
        """Refresh JIRA data with thread safety."""
        try:
            log_refresh_start(self.logger, "JIRA")
            new_data = query_issues(force_refresh=force)
            with self.data_lock:
                self.data = new_data
            log_refresh_complete(self.logger, "JIRA", len(new_data))
        except Exception as e:
            self.logger.error(f"Error refreshing JIRA data: {e}")
            raise
    
    def query_demands(self, excomai_sql: str) -> str:
        """Execute a SQL query on the Jira demands dataframe and return the result as a JSON string.

        These demands are sourced from the Jira system based on a predefined JQL filter.
        The dataframe contains demand-related information such as status, priority, dates, and metadata.

        Parameters
        ----------
        excomai_sql : str
            The panda SQL query to execute on the Jira demands dataframe.

        Returns
        -------
        str
            The result of the SQL query as a JSON string.

        Example
        -------
        >>> query_jira_demands("SELECT * FROM df WHERE Status = 'READY TO ACCEPT'")
        '[{"Status": "READY TO ACCEPT", ...}, ...]'
        """

        # Check if data is loaded
        with self.data_lock:
            if self.data is None or self.data.empty:
                self.logger.warning("⚠️ JIRA data not yet loaded. Returning empty result.")
                return "[]"

        # Define a function to use pandasql with the dataframe
        def pysqldf(q):
            # Use thread-safe access - expose as 'df' for SQL queries
            with self.data_lock:
                return sqldf(q, {"df": self.data})

        # Execute the SQL query and return the result as a JSON string
        result_df = pysqldf(excomai_sql)
        if result_df is None:
            return "[]"  # Return empty JSON array if query returns None
        return result_df.to_json(index=False)
    
    def get_record_count(self) -> int:
        """Get the number of records currently loaded."""
        with self.data_lock:
            return len(self.data) if self.data is not None else 0

    def get_status(self) -> dict:
        """Get the current status of JIRA data."""
        with self.data_lock:
            record_count = len(self.data) if self.data is not None else 0
            return {
                "status": "available" if record_count > 0 else "no_data",
                "record_count": record_count,
                "cache_file": "jira_issues_cache.parquet"
            }