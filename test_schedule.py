from app.backend.storage.db import (
    get_connection,
)

connection = get_connection()

print(
    connection.execute(
        "SELECT 1"
    ).fetchone()[0]
)