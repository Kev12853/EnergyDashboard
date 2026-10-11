import sqlite3
from datetime import UTC, datetime

import pandas as pd

from app.connections.connection import get_connection


def create_dispatches_table(
    conn: sqlite3.Connection,
):

    conn.execute(
        """
            CREATE TABLE IF NOT EXISTS octopus_dispatches (
                id INTEGER PRIMARY KEY,
                dispatch_start TEXT NOT NULL,
                dispatch_end TEXT NOT NULL,
                scheduled_energy_kwh REAL,
                status TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                first_seen TEXT NOT NULL,
                UNIQUE(
                    dispatch_start,
                    dispatch_end,
                    status
                )
            )
        """
    )


def create_consumption_costs_table(
    conn: sqlite3.Connection,
):
    conn.execute(
        """
       CREATE TABLE IF NOT EXISTS octopus_consumption_costs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    interval_start TEXT NOT NULL,
    interval_end TEXT NOT NULL,

    consumption_kwh REAL NOT NULL,

    tou_bucket TEXT NOT NULL,

    rate_p_per_kwh REAL NOT NULL,

    cost_excl_vat_p REAL NOT NULL,

    cost_incl_vat_p REAL NOT NULL,

    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,

    UNIQUE(
        interval_start,
        interval_end
    )
)
        """
    )

def create_tariffs_table(
    conn: sqlite3.Connection,
):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS
        octopus_tariffs (

            id INTEGER PRIMARY KEY
                AUTOINCREMENT,

            tariff_code TEXT NOT NULL,

            value_exc_vat REAL NOT NULL,

            value_inc_vat REAL NOT NULL,

            valid_from TEXT NOT NULL,

            valid_to TEXT,

            payment_method TEXT,

            created_at TEXT NOT NULL,

            UNIQUE(
                tariff_code,
                valid_from,
                valid_to
            )
        )
        """
    )

def create_four_rate_tariffs_table(
    conn: sqlite3.Connection,
):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS
        octopus_four_rate_tariffs (

            id INTEGER PRIMARY KEY
                AUTOINCREMENT,

            tariff_code TEXT NOT NULL,

            rate_type TEXT NOT NULL,

            value_exc_vat REAL NOT NULL,

            value_inc_vat REAL NOT NULL,

            valid_from TEXT NOT NULL,

            valid_to TEXT,

            payment_method TEXT,

            created_at TEXT NOT NULL,

            UNIQUE(
                tariff_code,
                rate_type,
                valid_from,
                valid_to
            )
        )
        """
    )

def create_accounts_table(
    conn: sqlite3.Connection,
):
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS
        octopus_accounts (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            account_number TEXT NOT NULL UNIQUE,

            is_active INTEGER NOT NULL
                DEFAULT 1,

            created_at TEXT NOT NULL
        )
        """
    )


def create_agreements_table(
    conn: sqlite3.Connection,
):

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS
        octopus_agreements (

            id INTEGER PRIMARY KEY
                AUTOINCREMENT,

            account_number TEXT NOT NULL,

            mpan TEXT NOT NULL,

            agreement_type TEXT NOT NULL,

            tariff_type TEXT NOT NULL,

            product_code TEXT NOT NULL,

            tariff_code TEXT NOT NULL,

            valid_from TEXT NOT NULL,

            valid_to TEXT,

            created_at TEXT NOT NULL,

            UNIQUE(

                account_number,

                mpan,

                tariff_code,

                valid_from

            )
        )
        """
    )

##delete
def upsert_tariffs(
    tariff_df: pd.DataFrame,
):

    if tariff_df.empty:
        return

    conn = get_connection()

    now = datetime.now(UTC).isoformat()

    for _, row in tariff_df.iterrows():
        conn.execute(
            """
                INSERT OR IGNORE INTO octopus_tariffs (
                    valid_from,
                    valid_to,
                    import_rate_gbp_per_kwh,
                    created_at
                )
                VALUES (?, ?, ?, ?)
            """,
            (
                row["valid_from"].isoformat(),
                row["valid_to"].isoformat(),
                row["import_rate_gbp_per_kwh"],
                now,
            ),
        )


##used by old dashboard app
def create_octopus_tables(connection):
    create_tariffs_table(connection)
    create_four_rate_tariffs_table(connection)
