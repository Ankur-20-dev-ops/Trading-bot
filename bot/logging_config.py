"""
Logging configuration for the trading bot.
Sets up structured logging to both console and file.
"""

import logging
import logging.handlers
import os
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FILE = LOG_DIR / "trading_bot.log"


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure and return the root logger with file and console handlers.

    Args:
        log_level: Logging level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).

    Returns:
        Configured logger instance.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    logger = logging.getLogger("trading_bot")
    logger.setLevel(numeric_level)

    # Avoid duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    fmt = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    formatter = logging.Formatter(fmt=fmt, datefmt=datefmt)

    # --- File handler (rotating, max 5 MB × 3 backups) ---
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # --- Console handler ---
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)   # keep terminal clean
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
