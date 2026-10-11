import sqlite3

from app.config.project_paths import DB_PATH


def get_connection() -> sqlite3.Connection:

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
