# app/backend/storage/solax_schema.py

# SOLAX TABLES
def create_telemetry_tables(
    connection,
):

    connection.execute(
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
                raw_json TEXT,
                work_mode TEXT
            )
        """
    )

    connection.execute(
        """
            CREATE TABLE IF NOT EXISTS telemetry_1m (
                bucket_start TEXT PRIMARY KEY,
                sample_count INTEGER,
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

    connection.execute(
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

    connection.execute(
        """
            CREATE TABLE IF NOT EXISTS service_heartbeat (
                service_name TEXT PRIMARY KEY,
                last_seen TEXT NOT NULL,
                status TEXT,
                message TEXT
            )
        """
    )

    connection.commit()


def create_automation_tables(
    connection,
):
    connection.execute(
        """
            CREATE TABLE IF NOT EXISTS schedule_periods (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                source TEXT NOT NULL,
                enabled INTEGER NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                mode TEXT NOT NULL,
                priority INTEGER NOT NULL DEFAULT 10,
                updated_at TEXT NOT NULL
            )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS inverter_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            requested_work_mode INTEGER,
            requested_manual_mode INTEGER,
            restore_work_mode_to INTEGER,
            restore_manual_mode_to INTEGER,
            underlying_work_mode INTEGER,
            underlying_manual_mode INTEGER,
            active INTEGER NOT NULL DEFAULT 0,
            phase TEXT NOT NULL,
            source TEXT,
            updated_at TEXT
        )
        """
    )

    columns = {
        row[1]
        for row in connection.execute("PRAGMA table_info(inverter_state)").fetchall()
    }

    if "underlying_work_mode" not in columns:
        connection.execute(
            """
            ALTER TABLE inverter_state
            ADD COLUMN underlying_work_mode INTEGER
            """
        )

    if "underlying_manual_mode" not in columns:
        connection.execute(
            """
            ALTER TABLE inverter_state
            ADD COLUMN underlying_manual_mode INTEGER
            """
        )
    connection.commit()


# OCTOPUS TABLES


def create_solax_tables(
    connection,
):
    create_telemetry_tables(connection)

    create_automation_tables(connection)

    # create_octopus_tables(connection)


def create_octopus_tables(connection):
    """Compatibility wrapper for the canonical Octopus schema creator."""
    from app.octopus.storage.octopus_schema import (
        create_octopus_tables as create_tables,
    )

    return create_tables(connection)
