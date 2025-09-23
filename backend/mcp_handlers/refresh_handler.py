"""Data refresh handlers and operations."""

import os
import time
import threading
from typing import List, Tuple, Optional
from datetime import datetime


class RefreshHandler:
    """Handler for data refresh operations."""
    
    def __init__(self, logger, jira_handler, freshservice_handler, queue_initial_load=True):
        self.logger = logger
        self.jira_handler = jira_handler
        self.freshservice_handler = freshservice_handler
        
        # Configuration for refresh intervals (in seconds)
        self.jira_refresh_interval = int(os.getenv("JIRA_REFRESH_INTERVAL", "3600"))
        self.freshservice_refresh_interval = int(os.getenv("FRESHSERVICE_REFRESH_INTERVAL", "3600"))
        
        # Async refresh queue
        self.refresh_queue: List[Tuple[str, bool]] = []
        self.queue_lock = threading.Lock()
        
        # Queue initial data loads if requested
        if queue_initial_load:
            self.logger.info("📥 Queuing initial data loads...")
            self.refresh_queue.append(("jira", False))  # Use cache if available
            self.refresh_queue.append(("freshservice", False))  # Use cache if available
        
        # Start background threads
        self._start_background_threads()
    
    def _start_background_threads(self):
        """Start the refresh queue processor and periodic refresh threads."""
        # Start the refresh queue processor thread
        queue_thread = threading.Thread(
            target=self._process_refresh_queue,
            daemon=True,
            name="RefreshQueueProcessor"
        )
        queue_thread.start()
        self.logger.info("⚡ Refresh queue processor started")
        
        # Start the periodic refresh thread
        refresh_thread = threading.Thread(
            target=self._periodic_refresh,
            daemon=True,
            name="PeriodicRefresh"
        )
        refresh_thread.start()
        
        from logger_config import log_thread_started
        log_thread_started(self.logger, "Background refresh", {
            "JIRA": self.jira_refresh_interval,
            "Freshservice": self.freshservice_refresh_interval
        })
    
    def _process_refresh_queue(self):
        """Process async refresh requests from the queue."""
        self.logger.info("🔄 Refresh queue processor started")
        while True:
            with self.queue_lock:
                if self.refresh_queue:
                    task = self.refresh_queue.pop(0)
                    remaining = len(self.refresh_queue)
                else:
                    task = None
                    remaining = 0
            
            if task:
                source, force = task
                self.logger.info(f"🎯 Processing {source} refresh (force={force}, {remaining} remaining in queue)")
                try:
                    if source == "jira":
                        self.jira_handler.refresh_data(force=force)
                    elif source == "freshservice":
                        self.freshservice_handler.refresh_data(force=force)
                except Exception as e:
                    self.logger.error(f"Error processing refresh for {source}: {e}")
            
            time.sleep(1)  # Check queue every second
    
    def _periodic_refresh(self):
        """Periodically refresh data from both sources."""
        jira_last_refresh = 0
        freshservice_last_refresh = 0
        
        while True:
            current_time = time.time()
            
            # Check if JIRA needs refresh
            if current_time - jira_last_refresh >= self.jira_refresh_interval:
                with self.queue_lock:
                    self.refresh_queue.append(("jira", False))  # Use cache if valid
                jira_last_refresh = current_time
            
            # Check if Freshservice needs refresh
            if current_time - freshservice_last_refresh >= self.freshservice_refresh_interval:
                with self.queue_lock:
                    self.refresh_queue.append(("freshservice", False))  # Use cache if valid
                freshservice_last_refresh = current_time
            
            # Sleep for a short interval before checking again
            time.sleep(60)  # Check every minute
    
    def queue_jira_refresh(self, force: bool = True) -> str:
        """Queue a JIRA refresh request."""
        try:
            with self.queue_lock:
                # Check if already in queue
                if any(task[0] == "jira" and task[1] for task in self.refresh_queue):
                    return "⏳ JIRA refresh already queued"
                
                self.refresh_queue.append(("jira", force))
                queue_size = len(self.refresh_queue)
            
            self.logger.info("🔄 Force refresh queued for JIRA data")
            return f"✅ JIRA refresh queued (position: {queue_size}). Check status with get_data_status()."
        except Exception as e:
            error_msg = f"❌ Failed to queue JIRA refresh: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
    
    def queue_freshservice_refresh(self, force: bool = True) -> str:
        """Queue a Freshservice refresh request."""
        try:
            with self.queue_lock:
                # Check if already in queue
                if any(task[0] == "freshservice" and task[1] for task in self.refresh_queue):
                    return "⏳ Freshservice refresh already queued"
                
                self.refresh_queue.append(("freshservice", force))
                queue_size = len(self.refresh_queue)
            
            self.logger.info("🔄 Force refresh queued for Freshservice data")
            return f"✅ Freshservice refresh queued (position: {queue_size}). Check status with get_data_status()."
        except Exception as e:
            error_msg = f"❌ Failed to queue Freshservice refresh: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
    
    def get_queue_status(self) -> dict:
        """Get the current status of the refresh queue."""
        with self.queue_lock:
            queue_copy = self.refresh_queue.copy()
            jira_queued = any(task[0] == "jira" for task in queue_copy)
            freshservice_queued = any(task[0] == "freshservice" for task in queue_copy)
        
        return {
            "size": len(queue_copy),
            "items": [{"source": task[0], "force": task[1]} for task in queue_copy],
            "jira_queued": jira_queued,
            "freshservice_queued": freshservice_queued
        }