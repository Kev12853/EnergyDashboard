import json
from datetime import datetime

from app.backend.storage.db import (
    get_connection,
)
from app.solax.telemetry.models import (
    PowerFlowSnapshot,
)


class TelemetryRepository:
    def __init__(
        self,
        connection,
    ):

        self.connection = connection

    def save_snapshot(
        self,
        snapshot: PowerFlowSnapshot,
    ):

        self.connection.execute(
            """
                INSERT INTO telemetry_snapshots (
                    timestamp,
                    solar_w,
                    inverter_w,
                    battery_w,
                    battery_soc_pct,
                    grid_w,
                    consumption_w,
                    pv1_w,
                    pv2_w,
                    work_mode,
                    raw_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                snapshot.timestamp.isoformat(),
                snapshot.pv_power_w,
                snapshot.ac_power_w,
                snapshot.battery_power_w,
                snapshot.battery_soc_pct,
                snapshot.grid_power_w,
                snapshot.consumption_power_w,
                snapshot.pv1_power_w,
                snapshot.pv2_power_w,
                snapshot.work_mode,
                json.dumps(snapshot.raw_registers),
            ),
        )
        self.connection.commit()

    def save_heartbeat(
        self,
        service_name: str,
        status: str = "Running",
        message: str | None = None,
    ):
        self.connection.execute(
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

        self.connection.commit()

    from datetime import datetime

    def get_heartbeat(self, service_name: str) -> datetime | None:

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

        return datetime.fromisoformat(row["last_seen"])

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
        start = start.strftime("%Y-%m-%d %H:%M:%S")

        end = end.strftime("%Y-%m-%d %H:%M:%S")

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
