# =========================================================
# UPDATED ANALYZE SCRIPT
# =========================================================
#
# services/charts/cloud_api/analyze_db.py
#
# =========================================================

"""
SQLite Telemetry Analysis
=========================

Loads telemetry directly from SQLite and produces
basic analytics and charts.
"""

import matplotlib.pyplot as plt
import pandas as pd

from services.solax.storage.db import (
    get_connection,
)

# =========================================================
# LOAD DATA
# =========================================================

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

# =========================================================
# PARSE TIMESTAMPS
# =========================================================

df["timestamp"] = pd.to_datetime(
    df["timestamp"]
)

df["upload_time"] = pd.to_datetime(
    df["upload_time"]
)

# =========================================================
# SUMMARY
# =========================================================

print(df.tail())

print("\n")

print(df.describe())

# =========================================================
# CHARTS
# =========================================================

plt.figure(figsize=(12, 6))

plt.plot(
    df["timestamp"],
    df["pv_power_w"],
    label="PV Power",
)

plt.plot(
    df["timestamp"],
    df["battery_power_w"],
    label="Battery Power",
)

plt.plot(
    df["timestamp"],
    df["grid_power_w"],
    label="Grid Power",
)

plt.plot(
    df["timestamp"],
    df["house_load_w"],
    label="House Load",
)

plt.legend()

plt.xlabel("Time")

plt.ylabel("Power (W)")

plt.title("SolaX Energy Flows")

plt.xticks(rotation=45)

plt.tight_layout()

plt.show()