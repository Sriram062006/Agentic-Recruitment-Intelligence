"""
Core logging configuration.
Sets up structured Python logging with timestamps, levels, module names,
and support for contextual request tracing.
"""

import logging
import sys
from typing import Optional


class StructuredFormatter(logging.Formatter):
    """Standardized formatter for structured console output."""

    def format(self, record: logging.LogRecord) -> str:
        # Support optional request_id from record extras
        request_id = getattr(record, "request_id", None)
        request_tag = f" [{request_id}]" if request_id else ""
        record.request_tag = request_tag
        return super().format(record)


def configure_logging(level: str = "INFO") -> logging.Logger:
    """Configures the root and application logger."""
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    log_format = "%(asctime)s | %(levelname)-7s | %(name)s%(request_tag)s | %(message)s"
    formatter = StructuredFormatter(fmt=log_format, datefmt="%Y-%m-%d %H:%M:%S")

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Avoid duplicate handlers if re-invoked
    if not root_logger.handlers:
        root_logger.addHandler(handler)
    else:
        root_logger.handlers = [handler]

    # Silence overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)

    logger = logging.getLogger("recruitment_intelligence")
    logger.setLevel(numeric_level)
    return logger


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Returns a namespaced logger instance."""
    if name:
        return logging.getLogger(f"recruitment_intelligence.{name}")
    return logging.getLogger("recruitment_intelligence")
