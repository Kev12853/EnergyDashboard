# =========================================================
# FILE
# =========================================================
#
# poller/charts/storage/schema.py
#
# =========================================================

"""
Database Schema Management
==========================

Purpose
-------
Creates and maintains SQLite database schema for
EnergyDashboard telemetry storage.

Current Tables
--------------
telemetry
    Historical normalized inverter telemetry

Design Notes
------------
Schema creation is idempotent.

Safe to run multiple times.
"""

from app.backend.storage.db import (
    get_connection,
)

# =========================================================
# CREATE SCHEMA
# =========================================================


def create_schema():
    """
    Create database tables if they do not exist.
    """

    connection = get_connection()

    cursor = connection.cursor()

    # =====================================================
    # TELEMETRY
    # =====================================================

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS telemetry (

            upload_time TEXT PRIMARY KEY,

            timestamp TEXT,

            pv_power_w REAL,
            pv1_power_w REAL,
            pv2_power_w REAL,

            battery_soc_pct REAL,
            battery_power_w REAL,
            battery_status TEXT,

            grid_power_w REAL,

            ac_power_w REAL,

            house_load_w REAL,

            inverter_status TEXT,
            inverter_serial TEXT
        )
        """
    )


    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS automation_rules (

    id INTEGER PRIMARY KEY,

    name TEXT NOT NULL,

    enabled INTEGER NOT NULL,

    start_time TEXT NOT NULL,

    end_time TEXT NOT NULL,

    action TEXT NOT NULL,

    updated_at TEXT NOT NULL

)
        """
    )

    connection.commit()

    connection.close()


# =========================================================
# SCRIPT ENTRY
# =========================================================

if __name__ == "__main__":

    create_schema()

    print("Database schema created.")

