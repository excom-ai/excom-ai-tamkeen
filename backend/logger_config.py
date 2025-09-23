"""Colorful logging configuration with emojis for the Tamkeen MCP server."""

import logging
import sys
from typing import Optional


class ColorfulFormatter(logging.Formatter):
    """Custom formatter that adds colors and emojis to log messages."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    
    # Emoji prefixes for different log levels
    EMOJIS = {
        'DEBUG': '🐛',
        'INFO': '💬',
        'WARNING': '⚠️',
        'ERROR': '❌',
        'CRITICAL': '🔥',
    }
    
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def __init__(self, *args, use_color: bool = True, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_color = use_color
    
    def format(self, record: logging.LogRecord) -> str:
        """Format the log record with colors and emojis."""
        # Save the original values
        levelname = record.levelname
        msg = record.msg
        
        if self.use_color and levelname in self.COLORS:
            # Add color and emoji
            color = self.COLORS[levelname]
            emoji = self.EMOJIS.get(levelname, '')
            record.levelname = f"{color}{self.BOLD}{emoji} {levelname}{self.RESET}"
            record.msg = f"{color}{msg}{self.RESET}"
        else:
            # Just add emoji without color
            emoji = self.EMOJIS.get(levelname, '')
            if emoji:
                record.levelname = f"{emoji} {levelname}"
        
        # Format the message
        result = super().format(record)
        
        # Restore original values
        record.levelname = levelname
        record.msg = msg
        
        return result


def setup_logging(
    name: Optional[str] = None,
    level: int = logging.INFO,
    use_color: bool = True,
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Set up a colorful logger with emojis.
    
    Parameters
    ----------
    name : str, optional
        Logger name. If None, returns the root logger.
    level : int, optional
        Logging level (default: INFO).
    use_color : bool, optional
        Whether to use colors in console output.
    log_file : str, optional
        If provided, also log to this file (without colors).
    
    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    logger.handlers = []
    
    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    
    # Format with timestamp and module name
    console_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    console_formatter = ColorfulFormatter(
        console_format,
        datefmt='%H:%M:%S',
        use_color=use_color
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler without colors (if requested)
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(level)
        file_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        file_formatter = logging.Formatter(file_format)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    return logger


# Convenience functions for special log messages
def log_banner(logger: logging.Logger, title: str, width: int = 60):
    """Log a banner with decorative borders."""
    logger.info("=" * width)
    logger.info(f"🚀 {title.center(width - 4)} 🚀")
    logger.info("=" * width)


def log_section(logger: logging.Logger, title: str, emoji: str = "📌"):
    """Log a section header."""
    logger.info("")
    logger.info(f"{emoji} {title}")
    logger.info("─" * 40)


def log_success(logger: logging.Logger, message: str):
    """Log a success message with a checkmark."""
    logger.info(f"✅ {message}")


def log_progress(logger: logging.Logger, current: int, total: int, message: str = ""):
    """Log progress information."""
    percentage = (current / total * 100) if total > 0 else 0
    progress_msg = f"📊 Progress: {current}/{total} ({percentage:.1f}%)"
    if message:
        progress_msg += f" - {message}"
    logger.info(progress_msg)


def log_data_loaded(logger: logging.Logger, data_type: str, count: int, source: str = "cache"):
    """Log data loading information."""
    emoji = "📤" if source == "cache" else "🌐"
    logger.info(f"{emoji} Loaded {count:,} {data_type} from {source}")


def log_refresh_start(logger: logging.Logger, data_type: str):
    """Log the start of a data refresh."""
    logger.info(f"🔄 Refreshing {data_type} data...")


def log_refresh_complete(logger: logging.Logger, data_type: str, count: int):
    """Log the completion of a data refresh."""
    logger.info(f"✅ {data_type} data refreshed successfully ({count:,} records)")


def log_error_with_retry(logger: logging.Logger, error: Exception, retry_count: int, max_retries: int):
    """Log an error with retry information."""
    logger.warning(f"🔁 Retry {retry_count}/{max_retries} after error: {error}")


def log_thread_started(logger: logging.Logger, thread_name: str, intervals: dict):
    """Log thread startup with interval information."""
    logger.info(f"⚡ {thread_name} thread started!")
    for name, seconds in intervals.items():
        minutes = seconds / 60
        logger.info(f"   🔄 {name} refresh interval: {seconds}s ({minutes:.0f} minutes)")