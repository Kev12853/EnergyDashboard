from datetime import datetime

class TelemetryRepository:

    def __init__(self, connection) -> None:

        self.connection = connection

    def get_heartbeat(
        self,
        service_name: str,
    ) -> datetime | None:

        cursor = self.connection.execute(
            """
            SELECT
                last_seen
            FROM service_heartbeat
            WHERE service_name = ?
            """,
            (service_name,),
        )

        row = cursor.fetchone()

        if row is None:
            return None

        return datetime.fromisoformat(
            row["last_seen"]
        )

    def get_latest_snapshot(self):

        cursor = self.connection.execute(
            """
            SELECT *
            FROM telemetry_snapshots
            ORDER BY timestamp DESC
            LIMIT 1
            """
        )

        return cursor.fetchone()

    def get_1m_history(
        self,
        start,
        end,
    ):

        start = start.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        end = end.strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        cursor = self.connection.execute(
            """
            SELECT *
            FROM telemetry_1m
            WHERE bucket_start BETWEEN ? AND ?
            ORDER BY bucket_start
            """,
            (
                start,
                end,
            ),
        )

        return cursor.fetchall()

    def get_30m_history(
        self,
        start: str,
        end: str,
    ):

        cursor = self.connection.execute(
            """
            SELECT *
            FROM telemetry_30m
            WHERE bucket_start BETWEEN ? AND ?
            ORDER BY bucket_start
            """,
            (
                start,
                end,
            ),
        )

        return cursor.fetchall()