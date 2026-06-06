# =========================================================
# SQLITE TELEMETRY ANALYSIS
# =========================================================

"""
Analyze telemetry stored in SQLite.
"""

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd

from app.backend.storage.db import (
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

df["timestamp"] = pd.to_datetime(df["timestamp"])

df["upload_time"] = pd.to_datetime(df["upload_time"])

# =========================================================
# BASIC INFO
# =========================================================

print("\nLATEST ROW\n")

print(df.tail(1))

print("\n")

print("=" * 80)

print("SUMMARY STATS")

print("=" * 80)

print(
    df[
        [
            "pv_power_w",
            "battery_soc_pct",
            "battery_power_w",
            "grid_power_w",
            "house_load_w",
        ]
    ].describe()
)

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

# =========================================================
# TIME AXIS FORMATTING
# =========================================================

ax = plt.gca()

ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M"))

ax.xaxis.set_major_locator(mdates.AutoDateLocator())

plt.tight_layout()

plt.show()
