"""Compatibility import for the canonical shared database connection."""
from app.connections.connection import get_connection
from app.config.project_paths import DB_PATH

__all__ = ["DB_PATH", "get_connection"]
