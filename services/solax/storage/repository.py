import json
import sqlite3

from pathlib import Path

from services.solax.telemetry.models import (
    PowerFlowSnapshot,
)


DB_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "telemetry.db"
)


class TelemetryRepository:

    def __init__(self):

        DB_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self.connection = sqlite3.connect(
            DB_PATH,
            check_same_thread=False,
        )

        self.connection.row_factory = (
            sqlite3.Row
        )

        self.create_tables()

    def create_tables(self):

        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS telemetry_snapshots (

                timestamp TEXT PRIMARY KEY,

                solar_w INTEGER,
                inverter_w INTEGER,

                battery_w INTEGER,
                battery_soc_pct REAL,

                grid_w INTEGER,
                consumption_w INTEGER,

                pv1_w INTEGER,
                pv2_w INTEGER,

                raw_json TEXT
            )
            """
        )

        self.connection.commit()

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
            start: str,
            end: str,

    ):
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