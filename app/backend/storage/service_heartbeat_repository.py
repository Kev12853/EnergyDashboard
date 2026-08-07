from datetime import datetime

from app.backend.storage.db import get_connection


class ServiceHeartbeatRepository:
    """Persistence access for service heartbeat records."""

    def __init__(self, connection=None):
        self._connection = connection

    def save_heartbeat(
        self,
        service_name: str,
        status: str = "Running",
        message: str | None = None,
    ):
        connection = self._connection or get_connection()

        connection.execute(
            """
            INSERT INTO service_heartbeat (
                service_name,
                last_seen,
                status,
                message
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(service_name) DO UPDATE SET
                last_seen = excluded.last_seen,
                status = excluded.status,
                message = excluded.message
            """,
            (
                service_name,
                datetime.now().isoformat(),
                status,
                message,
            ),
        )

        connection.commit()

        if self._connection is None:
            connection.close()
