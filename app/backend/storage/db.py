import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DB_PATH = PROJECT_ROOT / "data" / "energy_dashboard.db"


def get_connection():

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
