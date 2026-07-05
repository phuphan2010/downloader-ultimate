"""Structured JSON logging setup using structlog.

All logs are emitted as JSON with a consistent schema:
  - timestamp, level, event, logger, request_id, job_id, user_id
"""
import logging
import sys
from typing import Optional

import structlog

from app.core.config import settings


def setup_logging() -> None:
    """Configure structlog for structured JSON logging.

    In development (DEBUG=True), uses human-readable colored output.
    In production, emits pure JSON for log aggregation.
    """
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
    ]

    if settings.DEBUG:
        # Development: pretty colored output
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]
    else:
        # Production: JSON output
        processors = shared_processors + [
            structlog.processors.dict_tracebacks,
            structlog.processors.JSONRenderer(),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.DEBUG if settings.DEBUG else logging.INFO
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Also configure stdlib logging to go through structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
    )


def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Get a bound logger instance with optional name.

    Usage:
        logger = get_logger(__name__)
        logger.info("job_started", job_id="abc", user_id="u1")
    """
    return structlog.get_logger(name)


# Module-level logger for convenience
logger = get_logger(__name__)
