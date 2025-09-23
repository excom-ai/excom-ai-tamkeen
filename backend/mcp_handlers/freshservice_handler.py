"""Freshservice-specific handlers and operations."""

import threading
from typing import Optional
import pandas as pd
from pandasql import sqldf
from freshservice import get_freshservice_tickets, get_single_ticket
from logger_config import log_refresh_start, log_refresh_complete
import os


class FreshserviceHandler:
    """Handler for Freshservice-related operations."""

    def __init__(self, logger):
        self.logger = logger
        self.data: Optional[pd.DataFrame] = pd.DataFrame()  # Initialize with empty DataFrame
        self.data_lock = threading.RLock()
        
        # Try to load from cache immediately if available
        self._try_load_cache()
    
    def _try_load_cache(self):
        """Try to load data from cache file if it exists."""
        cache_file = "fresh_service_tickets.parquet"
        if os.path.exists(cache_file):
            try:
                self.logger.info("📤 Loading Freshservice data from cache on startup...")
                data = pd.read_parquet(cache_file)
                with self.data_lock:
                    self.data = data
                self.logger.info(f"✅ Loaded {len(data)} tickets from cache")
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to load cache on startup: {e}")
                self.data = pd.DataFrame()
        else:
            self.logger.info("📭 No Freshservice cache file found on startup")

    def load_data(self):
        """Load Freshservice data from cache without forcing refresh."""
        try:
            self.logger.info("🎫 Loading Freshservice data...")
            new_data = get_freshservice_tickets(force_refresh=False)
            with self.data_lock:
                self.data = new_data
            if self.data is not None:
                self.logger.info(f"✅ Freshservice data loaded ({len(self.data)} tickets)")
            else:
                self.logger.warning("⚠️ No Freshservice data available")
        except Exception as e:

            self.logger.error(f"Error loading Freshservice data: {e}")
            self.data = pd.DataFrame()  # Empty DataFrame as fallback

    def refresh_data(self, force: bool = True):
        """Refresh Freshservice data with thread safety."""
        try:
            log_refresh_start(self.logger, "Freshservice")
            new_data = get_freshservice_tickets(force_refresh=force)
            with self.data_lock:
                self.data = new_data
            log_refresh_complete(self.logger, "Freshservice", len(new_data))
        except Exception as e:
            self.logger.error(f"Error refreshing Freshservice data: {e}")
            raise

    def query_tickets(self, excomai_sql: str) -> str:
        """Execute a SQL query on the Freshservice dataframe and return the result as a JSON string.

        Parameters
        ----------
        excomai_sql : str
            The SQL query to execute on the Freshservice dataframe.

        Returns
        -------
        str
            The result of the SQL query as a JSON string.

        Example
        -------
        >>> query_fresh_service_tickets("SELECT subject, priority FROM fresh_service_tickets WHERE priority = 'High'")
        '[{"subject": "Login issue", "priority": "High"}, ...]'
        """

        # Check if data is loaded
        with self.data_lock:
            if self.data is None or self.data.empty:
                self.logger.warning("⚠️ Freshservice data not yet loaded. Returning empty result.")
                return "[]"

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

    def get_single_ticket(self, ticket_id: str) -> dict:
        return get_single_ticket(ticket_id)

    def get_status(self) -> dict:
        """Get the current status of Freshservice data."""
        with self.data_lock:
            record_count = len(self.data) if self.data is not None else 0
            return {
                "status": "available" if record_count > 0 else "no_data",
                "record_count": record_count,
                "cache_file": "fresh_service_tickets.parquet"
            }
