# =========================================================
# FILE
# =========================================================
#
# services/charts/storage/repository.py
#
# =========================================================

"""
Telemetry Repository
====================

Purpose
-------
Encapsulates telemetry database access.

This module acts as the persistence abstraction layer
between application logic and SQLite storage.

Responsibilities
----------------
- insert telemetry
- retrieve telemetry
- query historical ranges
- retrieve latest snapshots

Design Notes
------------
Higher-level code should NOT directly execute SQL.

All database interaction should flow through
repository functions.
"""

from services.solax.analytics.calculations import (
    calculate_house_load_w,
)

from services.solax.models import (
    PowerFlowSnapshot,
)

from services.db import (
    get_connection,
)

# =========================================================
# INSERT SNAPSHOT
# =========================================================


def insert_snapshot(
    snapshot: PowerFlowSnapshot,
):
    """
    Insert telemetry snapshot into database.

    Duplicate upload_time rows are ignored.
    """

    connection = get_connection()

    cursor = connection.cursor()

    # =====================================================
    # DERIVED METRICS
    # =====================================================

    house_load_w = calculate_house_load_w(
        pv_power_w=snapshot.pv_power_w,
        grid_power_w=snapshot.grid_power_w,
        battery_power_w=snapshot.battery_power_w,
    )

    # =====================================================
    # INSERT
    # =====================================================

    cursor.execute(
        """
        INSERT OR IGNORE INTO telemetry (

            upload_time,
            timestamp,

            pv_power_w,
            pv1_power_w,
            pv2_power_w,

            battery_soc_pct,
            battery_power_w,
            battery_status,

            grid_power_w,

            ac_power_w,

            house_load_w,

            inverter_status,
            inverter_serial

        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            snapshot.upload_time,
            snapshot.timestamp.isoformat(),

            snapshot.pv_power_w,
            snapshot.pv1_power_w,
            snapshot.pv2_power_w,

            snapshot.battery_soc_pct,
            snapshot.battery_power_w,
            snapshot.battery_status,

            snapshot.grid_power_w,

            snapshot.ac_power_w,

            house_load_w,

            snapshot.inverter_status,
            snapshot.inverter_serial,
        ),
    )

    connection.commit()

    connection.close()


# =========================================================
# GET LATEST SNAPSHOT
# =========================================================


def get_latest_snapshot():
    """
    Retrieve most recent telemetry row.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM telemetry
        ORDER BY upload_time DESC
        LIMIT 1
        """
    )

    row = cursor.fetchone()

    connection.close()

    return row


# =========================================================
# GET SNAPSHOTS BETWEEN
# =========================================================


def get_snapshots_between(
    start_time,
    end_time,
):
    """
    Retrieve telemetry rows between timestamps.
    """

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT *
        FROM telemetry
        WHERE upload_time BETWEEN ? AND ?
        ORDER BY upload_time
        """,
        (
            start_time,
            end_time,
        ),
    )

    rows = cursor.fetchall()

    connection.close()

    return rows


# =========================================================
# LOAD TELEMETRY DATAFRAME
# =========================================================

import pandas as pd


def get_telemetry_dataframe():

    connection = get_connection()

    df = pd.read_sql_query(
        """
        SELECT *
        FROM telemetry
        ORDER BY upload_time
        """,
        connection,
    )

    connection.close()

    df["upload_time"] = pd.to_datetime(
        df["upload_time"]
    )

    return df

# =========================================================
# GET LATEST SNAPSHOT DATAFRAME ROW
# =========================================================

def get_latest_snapshot_row():

    connection = get_connection()

    df = pd.read_sql_query(
        """
        SELECT *
        FROM telemetry
        ORDER BY upload_time DESC
        LIMIT 1
        """,
        connection,
    )

    connection.close()

    df["upload_time"] = pd.to_datetime(
        df["upload_time"]
    )

    return df.iloc[0]

# =========================================================
# LOAD RECENT TELEMETRY
# =========================================================

def get_recent_telemetry_dataframe(
    hours: int,
):

    connection = get_connection()

    df = pd.read_sql_query(
        f"""
        SELECT *
        FROM telemetry
        WHERE upload_time >= datetime(
            'now',
            '-{hours} hours'
        )
        ORDER BY upload_time
        """,
        connection,
    )

    connection.close()

    df["upload_time"] = pd.to_datetime(
        df["upload_time"]
    )

    return df