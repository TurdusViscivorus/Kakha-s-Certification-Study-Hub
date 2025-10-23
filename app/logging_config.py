"""Logging helpers for the Study Hub application."""
from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from .config import paths


def configure_logging() -> None:
    """Configure application-wide logging."""
    paths.root.mkdir(parents=True, exist_ok=True)
    log_path = paths.log_file
    handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=3, encoding="utf-8")

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s - %(message)s", "%Y-%m-%d %H:%M:%S"
    )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    if not root_logger.handlers:
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)


__all__ = ["configure_logging"]
