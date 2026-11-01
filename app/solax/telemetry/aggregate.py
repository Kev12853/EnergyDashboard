"""Rebuild one-minute and thirty-minute telemetry aggregates and prune raw history in SQLite. This maintenance service transforms stored data and does not communicate with the inverter."""


class TelemetryAggregator:
    """Read raw telemetry and persist derived aggregates in SQLite."""

    def __init__(self, connection):
        self.connection = connection

    def rebuild_1m(self):
        """Rebuild minute buckets from stored raw snapshots and commit aggregate rows."""
        self.connection.execute(
            """
                INSERT OR REPLACE INTO telemetry_1m
                (
                    bucket_start,
                    sample_count,
                    avg_solar_w,
                    max_solar_w,
                    min_solar_w,
                    avg_consumption_w,
                    max_consumption_w,
                    min_consumption_w,
                    avg_grid_w,
                    avg_battery_w,
                    battery_soc_pct
                )
                SELECT
                    strftime(
                        '%Y-%m-%d %H:%M:00',
                        timestamp,
                        'localtime'
                    ) AS bucket1m_start,
                    COUNT(*) AS sample_count,
                    AVG(solar_w),
                    MAX(solar_w),
                    MIN(solar_w),
                    AVG(consumption_w),
                    MAX(consumption_w),
                    MIN(consumption_w),
                    AVG(grid_w),
                    AVG(battery_w),
                    (
                        SELECT raw.battery_soc_pct
                        FROM telemetry_snapshots AS raw
                        WHERE raw.battery_soc_pct IS NOT NULL
                          AND strftime('%Y-%m-%d %H:%M:00', raw.timestamp, 'localtime')
                              = strftime(
                                    '%Y-%m-%d %H:%M:00',
                                    telemetry_snapshots.timestamp,
                                    'localtime'
                                )
                        ORDER BY raw.timestamp DESC
                        LIMIT 1
                    )
                FROM telemetry_snapshots
                WHERE timestamp >=
                (
                    SELECT
                        COALESCE(
                            datetime(MAX(bucket_start), '-1 minute'),
                            '1970-01-01 00:00:00'
                        )
                    FROM telemetry_1m
                )
                GROUP BY bucket1m_start;
            """
        )

        self.connection.commit()

    def rebuild_30m(self):
        """Rebuild half-hour buckets from stored telemetry and commit aggregate rows."""
        self.connection.execute(
            """
                INSERT OR REPLACE INTO telemetry_30m
                (
                    bucket_start,
                    avg_solar_w,
                    max_solar_w,
                    min_solar_w,
                    avg_consumption_w,
                    max_consumption_w,
                    min_consumption_w,
                    avg_grid_w,
                    avg_battery_w,
                    battery_soc_pct
                )
                SELECT
                    strftime(
                        '%Y-%m-%d %H:',
                        bucket_start
                    )
                    ||
                    CASE
                        WHEN CAST(strftime('%M', bucket_start) AS INTEGER) < 30
                        THEN '00:00'
                        ELSE '30:00'
                    END
                    AS bucket30_start,
                    AVG(avg_solar_w),
                    MAX(max_solar_w),
                    MIN(min_solar_w),
                    AVG(avg_consumption_w),
                    MAX(max_consumption_w),
                    MIN(min_consumption_w),
                    AVG(avg_grid_w),
                    AVG(avg_battery_w),
                    (
                        SELECT minute.battery_soc_pct
                        FROM telemetry_1m AS minute
                        WHERE minute.battery_soc_pct IS NOT NULL
                          AND minute.bucket_start >= (
                                strftime('%Y-%m-%d %H:', telemetry_1m.bucket_start)
                                || CASE
                                    WHEN CAST(strftime('%M', telemetry_1m.bucket_start) AS INTEGER) < 30
                                    THEN '00:00'
                                    ELSE '30:00'
                                END
                              )
                          AND minute.bucket_start < datetime(
                                strftime('%Y-%m-%d %H:', telemetry_1m.bucket_start)
                                || CASE
                                    WHEN CAST(strftime('%M', telemetry_1m.bucket_start) AS INTEGER) < 30
                                    THEN '00:00'
                                    ELSE '30:00'
                                END,
                                '+30 minutes'
                              )
                        ORDER BY minute.bucket_start DESC
                        LIMIT 1
                    )
                FROM telemetry_1m
                WHERE bucket_start >=
                (
                    SELECT
                        COALESCE(
                            datetime(MAX(bucket_start), '-1 hour'),
                            '1970-01-01 00:00:00'
                        )
                    FROM telemetry_30m
                )
                GROUP BY bucket30_start;
            """
        )
        self.connection.commit()

    def cleanup_raw_telemetry(self):
        """Delete raw samples older than the configured retention boundary and commit the deletion."""
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
