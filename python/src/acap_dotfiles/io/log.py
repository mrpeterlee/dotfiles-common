"""structlog setup for dots. TTY-aware color, NO_COLOR honored, JSON in non-TTY."""

from __future__ import annotations

import logging
import os
import sys

import structlog


def configure(verbose: int = 0) -> None:
    """Initialize structlog. Idempotent — safe to call repeatedly."""
    level = logging.WARNING
    if verbose >= 1:
        level = logging.INFO
    if verbose >= 2:
        level = logging.DEBUG

    logging.basicConfig(level=level, format="%(message)s", stream=sys.stderr)

    no_color = bool(os.environ.get("NO_COLOR"))
    is_tty = sys.stderr.isatty()

    processors: list[object] = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
    ]
    if is_tty and not no_color:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))
    elif is_tty:
        processors.append(structlog.dev.ConsoleRenderer(colors=False))
    else:
        processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=processors,  # type: ignore[arg-type]
        wrapper_class=structlog.make_filtering_bound_logger(level),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    logger: structlog.stdlib.BoundLogger = structlog.get_logger(name)
    return logger
