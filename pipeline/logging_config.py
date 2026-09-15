"""
Centralized structured logging configuration for Website Updater Studio.
Provides clean console output and rotating file log at `clients/pipeline.log`.
"""

import os
import sys
import logging
from logging.handlers import RotatingFileHandler

LOG_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "clients"))
LOG_FILE = os.path.join(LOG_DIR, "pipeline.log")

_initialized = False


def setup_logging(level: int = logging.INFO, log_file: str = LOG_FILE) -> None:
    """Configures root logger with console and rotating file handlers."""
    global _initialized
    if _initialized:
        return

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    root_logger = logging.getLogger("pipeline")
    root_logger.setLevel(level)

    # Console Handler (clean user-friendly)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter("[%(levelname)s] [%(name)s] %(message)s")
    console_handler.setFormatter(console_format)
    root_logger.addHandler(console_handler)

    # Rotating File Handler (detailed with timestamp for auditing)
    try:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=3,
            encoding="utf-8"
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter("%(asctime)s [%(levelname)s] [%(name)s:%(lineno)d] %(message)s")
        file_handler.setFormatter(file_format)
        root_logger.addHandler(file_handler)
    except Exception:
        pass

    _initialized = True


def get_logger(name: str) -> logging.Logger:
    """Returns a namespaced logger under the 'pipeline' hierarchy."""
    if not _initialized:
        setup_logging()
    if name.startswith("pipeline."):
        return logging.getLogger(name)
    return logging.getLogger(f"pipeline.{name}")
