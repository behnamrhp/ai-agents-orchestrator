"""
Logging configuration for the AI Orchestrator.

Provides structured logging with levels, timestamps, and stacktraces.
"""

from __future__ import annotations

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(
    log_level: str | int = logging.INFO,
    log_file: str | Path | None = None,
    enable_console: bool = True,
) -> None:
    """
    Configure Python logging with level-based logs, timestamps, and stacktraces.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) or int
        log_file: Optional path to log file. If None, logs only to console.
        enable_console: Whether to output logs to console (stdout/stderr)
    """
    # Convert string level to int if needed
    if isinstance(log_level, str):
        level = getattr(logging, log_level.upper(), logging.INFO)
    else:
        level = log_level

    # Create formatter with timestamp, level, logger name, and message
    # Include stacktrace for exceptions
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Detailed formatter for file logs (includes stacktraces automatically via exc_info)
    detailed_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handlers: list[logging.Handler] = []

    # Console handler (stderr for errors, stdout for info)
    if enable_console:
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        handlers.append(console_handler)

    # File handler with rotation
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(detailed_formatter)
        handlers.append(file_handler)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # Add our handlers
    for handler in handlers:
        root_logger.addHandler(handler)

    # Set levels for third-party loggers to reduce noise
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

