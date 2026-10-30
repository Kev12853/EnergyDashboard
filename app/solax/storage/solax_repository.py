"""Legacy-facing telemetry repository for saving snapshots and querying time-series data from SQLite. It is used by monitoring/reporting, not to issue inverter commands."""

import json
from datetime import datetime

from app.solax.telemetry.models import (
    PowerFlowSnapshot,
)


class TelemetryRepository:
    """Persist/query telemetry snapshots, history and heartbeat rows using the injected SQLite connection."""
    def __init__(
        self,
        connection,
    ):

        self.connection = connection

    def save_snapshot(
        self,
        snapshot: PowerFlowSnapshot,
        source: str = "modbus",
    ):
        """Save Modbus and cloud snapshots separately.

        Cloud samples arrive at five-minute intervals and must not be mixed into
        the high-resolution Modbus history used by energy-cost calculations.
        """
        if source.lower() == "cloud":
            table = "telemetry_cloud_snapshots"
            source_name = "Cloud"
        else:
            table = "telemetry_snapshots"
            source_name = "Modbus"

        self.connection.execute(
            f"""
                INSERT OR REPLACE INTO {table} (
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
                    raw_json,
                    telemetry_source
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                source_name,
            ),
        )
        self.connection.commit()

    def save_heartbeat(
        self,
        service_name: str,
        status: str = "Running",
        message: str | None = None,
    ):
        """Upsert a service_heartbeat record and commit it on the injected connection."""
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

        """Read one heartbeat timestamp from service_heartbeat and return a datetime, or None if absent."""
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
        """Return the newest reading from either telemetry source."""
        cursor = self.connection.execute(
            """
                SELECT * FROM (
                    SELECT
                        timestamp, solar_w, inverter_w, battery_w,
                        battery_soc_pct, grid_w, consumption_w,
                        pv1_w, pv2_w, work_mode, raw_json,
                        telemetry_source
                    FROM telemetry_snapshots

                    UNION ALL

                    SELECT
                        timestamp, solar_w, inverter_w, battery_w,
                        battery_soc_pct, grid_w, consumption_w,
                        pv1_w, pv2_w, work_mode, raw_json,
                        telemetry_source
                    FROM telemetry_cloud_snapshots
                )
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
        """Read telemetry_1m buckets between the supplied endpoints in chronological order."""
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
        """Read telemetry_30m buckets between the supplied endpoints in chronological order."""
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
