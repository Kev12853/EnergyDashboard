# app/backend/storage/schema.py

# SOLAX TABLES
def create_telemetry_tables(
    connection,
):

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS
        telemetry_snapshots (

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
        CREATE TABLE IF NOT EXISTS
        telemetry_1m (

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
        CREATE TABLE IF NOT EXISTS
        telemetry_30m (

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

            id INTEGER PRIMARY KEY,

            desired_work_mode INTEGER,

            desired_manual_mode INTEGER,

            source TEXT NOT NULL,

            updated_at TEXT NOT NULL

        )
        """
    )

    connection.commit()


# OCTOPUS TABLES
def create_octopus_tables(
    connection,
):
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS
            octopus_accounts
        (

            id
            INTEGER
            PRIMARY
            KEY
            AUTOINCREMENT,

            account_number
            TEXT
            NOT
            NULL
            UNIQUE,

            is_active
            INTEGER
            NOT
            NULL
            DEFAULT
            1,

            created_at
            TEXT
            NOT
            NULL
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS
            octopus_agreements
        (

            id
            INTEGER
            PRIMARY
            KEY
            AUTOINCREMENT,

            account_number
            TEXT
            NOT
            NULL,

            mpan
            TEXT
            NOT
            NULL,

            agreement_type
            TEXT
            NOT
            NULL,

            tariff_type
            TEXT
            NOT
            NULL,

            product_code
            TEXT
            NOT
            NULL,

            tariff_code
            TEXT
            NOT
            NULL,

            valid_from
            TEXT
            NOT
            NULL,

            valid_to
            TEXT,

            created_at
            TEXT
            NOT
            NULL,

            UNIQUE
        (

            account_number,

            mpan,

            tariff_code,

            valid_from

        )
            )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS
            octopus_tariffs
        (

            id
            INTEGER
            PRIMARY
            KEY
            AUTOINCREMENT,

            tariff_code
            TEXT
            NOT
            NULL,

            slot_start
            TEXT,

            slot_end
            TEXT,

            unit_rate_gbp_per_kwh
            REAL
            NOT
            NULL,

            created_at
            TEXT
            NOT
            NULL,

            UNIQUE
        (

            tariff_code,

            slot_start,

            slot_end

        )
            )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS
        octopus_dispatches (

            id INTEGER PRIMARY KEY,

            dispatch_start TEXT NOT NULL,
            dispatch_end TEXT NOT NULL,

            scheduled_energy_kwh REAL,

            status TEXT NOT NULL,

            last_seen TEXT NOT NULL,

            UNIQUE(
                dispatch_start,
                dispatch_end,
                status
            )
        )
        """
    )

    connection.commit()


def create_all_tables(
    connection,
):
    create_telemetry_tables(connection)

    create_automation_tables(connection)

    create_octopus_tables(connection)
