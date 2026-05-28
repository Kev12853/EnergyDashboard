# =========================================================
# FILE
# =========================================================
#
# services/charts/storage/db.py
#
# =========================================================

"""
SQLite Database Connection Helpers
==================================

Purpose
-------
Centralized database connection management for the
EnergyDashboard telemetry platform.

This module provides:

- SQLite connection creation
- database file location management
- common connection configuration

Design Notes
------------
All database access should go through this module.

This ensures:

- consistent configuration
- easier future migration
- centralized path handling
"""

import sqlite3

from pathlib import Path

# =========================================================
# PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "energy_dashboard.db"

# =========================================================
# CONNECTIONS
# =========================================================


def get_connection() -> sqlite3.Connection:
    """
    Create configured SQLite connection.
    """

    connection = sqlite3.connect(DB_PATH)

    #
    # Return rows as dict-like objects
    #

    connection.row_factory = sqlite3.Row

    return connection