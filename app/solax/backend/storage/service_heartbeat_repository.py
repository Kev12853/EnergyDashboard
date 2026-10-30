"""Persist poller and control service liveness records in SQLite for status and stale-service detection. Methods write heartbeat rows but do not touch inverter state."""

from datetime import datetime

from app.connections.connection import get_connection


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
        """Upsert one service_heartbeat row with current local timestamp, status and message; commits and closes the connection only when it created that connection."""
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
