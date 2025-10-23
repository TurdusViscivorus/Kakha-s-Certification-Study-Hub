"""Database bootstrapping utilities."""
from __future__ import annotations

from sqlalchemy import inspect

from .database import Base, get_engine
from .models import entities  # noqa: F401 - ensure models are registered


def ensure_database() -> None:
    """Create tables if they do not already exist."""
    engine = get_engine()
    inspector = inspect(engine)
    if not inspector.has_table("users"):
        Base.metadata.create_all(engine)


__all__ = ["ensure_database"]
