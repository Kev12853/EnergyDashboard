"""Create SQLite connections using the shared EnergyDashboard path resolver.

SolaX poller, control, automation and storage repositories use this connection
factory to share one database. The factory creates the parent directory,
enables WAL mode and returns rows addressable by column name.
"""

import sqlite3

from app.config.project_paths import DB_PATH


def get_connection() -> sqlite3.Connection:

    """Open the configured SQLite database, create its parent directory if needed, enable WAL and normal synchronous mode, and return a row-mapped connection. Filesystem or SQLite errors propagate to the caller."""
    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False,
        timeout=30,
    )

    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")

    connection.row_factory = sqlite3.Row

    return connection
