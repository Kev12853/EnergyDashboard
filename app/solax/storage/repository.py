import json

from app.solax.telemetry.models import (
    PowerFlowSnapshot,
)

from app.backend.storage.db import (
    get_connection,
)

class TelemetryRepository:

    def __init__(
        self,
        connection,
    ):

        self.connection = (
            connection
        )

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

                raw_json

            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                json.dumps(
                    snapshot.raw_registers
                ),
            ),
        )

        self.connection.commit()

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

            WHERE bucket_start
                      BETWEEN ? AND ?

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

            WHERE bucket_start
                      BETWEEN ? AND ?

            ORDER BY bucket_start
            """,
            (
                start,
                end,
            ),
        )

        return cursor.fetchall()