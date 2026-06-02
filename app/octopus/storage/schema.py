import sqlite3

import pandas as pd

from app.backend.storage.db import get_connection


def create_dispatches_table(
    conn: sqlite3.Connection,
):

    conn.execute(
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

    conn.commit()


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

            slot_start TEXT,
            
            slot_end TEXT,

            unit_rate_gbp_per_kwh REAL
                NOT NULL,

            created_at TEXT NOT NULL,

            UNIQUE(

                tariff_code,

                slot_start,

                slot_end

            )
        )
        """
    )

    conn.commit()

from datetime import datetime, UTC


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
            INSERT
            OR IGNORE INTO
            octopus_tariffs (

                valid_from,
                valid_to,
                import_rate_gbp_per_kwh,
                created_at

            )
            VALUES (?, ?, ?, ?)
            """,
            (
                row[
                    "valid_from"
                ].isoformat(),

                row[
                    "valid_to"
                ].isoformat(),

                row[
                    "import_rate_gbp_per_kwh"
                ],

                now,
            ),
        )

    conn.commit()

# def create_accounts_table(
#     conn: sqlite3.Connection,
# ):
#     conn.execute(
#         """
#         CREATE TABLE IF NOT EXISTS
#         octopus_accounts (
#
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#
#             account_number TEXT NOT NULL UNIQUE,
#
#             is_active INTEGER NOT NULL
#                 DEFAULT 1,
#
#             created_at TEXT NOT NULL
#         )
#         """
#     )
#
#     conn.commit()

# def create_agreements_table(
#     conn: sqlite3.Connection,
# ):
#
#     conn.execute(
#         """
#         CREATE TABLE IF NOT EXISTS
#         octopus_agreements (
#
#             id INTEGER PRIMARY KEY
#                 AUTOINCREMENT,
#
#             account_number TEXT NOT NULL,
#
#             mpan TEXT NOT NULL,
#
#             agreement_type TEXT NOT NULL,
#
#             tariff_type TEXT NOT NULL,
#
#             product_code TEXT NOT NULL,
#
#             tariff_code TEXT NOT NULL,
#
#             valid_from TEXT NOT NULL,
#
#             valid_to TEXT,
#
#             created_at TEXT NOT NULL,
#
#             UNIQUE(
#
#                 account_number,
#
#                 mpan,
#
#                 tariff_code,
#
#                 valid_from
#
#             )
#         )
#         """
#     )
#
#     conn.commit()

