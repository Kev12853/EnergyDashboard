import sqlite3

from pathlib import Path


DB_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "telemetry.db"
)


class TelemetryAggregator:

    def __init__(self):
        self.connection = sqlite3.connect(
            DB_PATH,
            check_same_thread=False,
            timeout=30,
        )

        self.connection.execute(
            "PRAGMA journal_mode=WAL"
        )

        self.connection.execute(
            "PRAGMA synchronous=NORMAL"
        )

        self.create_tables()

    def create_tables(self):

        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS telemetry_1m (

                bucket_start TEXT PRIMARY KEY,

                avg_solar_w REAL,
                max_solar_w INTEGER,
                min_solar_w INTEGER,

                avg_consumption_w REAL,
                max_consumption_w INTEGER,
                min_consumption_w INTEGER,

                avg_grid_w REAL,

                avg_battery_w REAL
            )
            """
        )

        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS telemetry_30m (

                bucket_start TEXT PRIMARY KEY,

                avg_solar_w REAL,
                max_solar_w INTEGER,
                min_solar_w INTEGER,

                avg_consumption_w REAL,
                max_consumption_w INTEGER,
                min_consumption_w INTEGER,

                avg_grid_w REAL,

                avg_battery_w REAL
            )
            """
        )

        self.connection.commit()

    def rebuild_1m(self):

        self.connection.execute(
            """
            DELETE FROM telemetry_1m
            """
        )

        self.connection.execute(
            """
            INSERT INTO telemetry_1m

            SELECT

               strftime(
    '%Y-%m-%d %H:%M:00',
    timestamp,
    'localtime'
) AS bucket_start,

                AVG(solar_w),
                MAX(solar_w),
                MIN(solar_w),

                AVG(consumption_w),
                MAX(consumption_w),
                MIN(consumption_w),

                AVG(grid_w),

                AVG(battery_w)

            FROM telemetry_snapshots

            GROUP BY bucket_start
            """
        )

        self.connection.commit()

    def rebuild_30m(self):

        self.connection.execute(
            """
            DELETE FROM telemetry_30m
            """
        )

        self.connection.execute(
            """
            INSERT INTO telemetry_30m

            SELECT

                strftime(
                    '%Y-%m-%d %H:',
                    timestamp,
                    'localtime'
                )
                ||
                CASE

                    WHEN CAST(
                        strftime(
                            '%M',
                            timestamp
                        ) AS INTEGER
                    ) < 30

                    THEN '00:00'

                    ELSE '30:00'

                END
                AS bucket_start,

                AVG(solar_w),
                MAX(solar_w),
                MIN(solar_w),

                AVG(consumption_w),
                MAX(consumption_w),
                MIN(consumption_w),

                AVG(grid_w),

                AVG(battery_w)

            FROM telemetry_snapshots

            GROUP BY bucket_start
            """
        )

        self.connection.commit()

    def cleanup_raw_telemetry(self):

        self.connection.execute(
            """
            DELETE FROM telemetry_snapshots

            WHERE timestamp < datetime(
                'now',
                '-1 day'
            )
            """
        )

        self.connection.commit()