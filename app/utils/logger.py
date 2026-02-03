"""
Logging configuration for FidelioPro FastAPI application.
"""

import logging
import logging.handlers
import os
import sys
from pathlib import Path
from typing import Any, Dict

import structlog
from structlog.typing import FilteringBoundLogger

from ..config import settings


class CompactFormatter(logging.Formatter):
    """Custom formatter for compact single-line log output."""
    
    def format(self, record):
        # For our compact format, just return the message as-is
        return record.getMessage()


def setup_logging() -> FilteringBoundLogger:
    """
    Setup structured logging with both file and console handlers.

    Returns:
        Configured structlog logger
    """
    # Ensure logs directory exists
    log_dir = Path(settings.log_file).parent
    log_dir.mkdir(exist_ok=True)

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level.upper()),
    )

    # Create file handler with rotation
    file_handler = logging.handlers.RotatingFileHandler(
        settings.log_file,
        maxBytes=settings.log_max_size,
        backupCount=settings.log_backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(getattr(logging, settings.log_level.upper()))

    # Create console handler with compact formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, settings.log_level.upper()))
    console_handler.setFormatter(CompactFormatter())

    # Configure structlog for simple message passing
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # Simple processor that just passes the message through
            lambda logger, method_name, event_dict: event_dict.get("event", ""),
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Get the root logger and add handlers
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return structlog.get_logger("fideliopro")


def safe_log_data(data: Any) -> Dict[str, Any]:
    """
    Safely prepare data for logging, handling encoding issues.

    Args:
        data: Data to be logged

    Returns:
        Safe dictionary for logging
    """
    if isinstance(data, dict):
        safe_data = {}
        for key, value in data.items():
            try:
                safe_key = str(key).encode("utf-8", errors="replace").decode("utf-8")
                safe_value = safe_log_value(value)
                safe_data[safe_key] = safe_value
            except Exception:
                safe_data[f"error_key_{id(key)}"] = "encoding_error"
        return safe_data
    else:
        return {"data": safe_log_value(data)}


def safe_log_value(value: Any) -> str:
    """
    Safely convert value to string for logging.

    Args:
        value: Value to convert

    Returns:
        Safe string representation
    """
    try:
        if isinstance(value, str):
            return value.encode("utf-8", errors="replace").decode("utf-8")
        else:
            return str(value).encode("utf-8", errors="replace").decode("utf-8")
    except Exception:
        return f"<encoding_error_{type(value).__name__}>"


# Initialize logger
logger = setup_logging()
