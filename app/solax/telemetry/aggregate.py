from app.backend.storage.db import (
    get_connection,
)

class TelemetryAggregator:

    def __init__(self):
        self.connection = (
            get_connection()
        )

        self.connection.execute(
            "PRAGMA journal_mode=WAL"
        )

        self.connection.execute(
            "PRAGMA synchronous=NORMAL"
        )

        self.create_tables()

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