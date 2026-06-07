# =========================================================
# LOAD SOLAX DATA
# =========================================================
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from datetime import timedelta

from app.solax.storage import repository
# =========================================================
# SOLAX REPOSITORY
# =========================================================

from app.solax.storage.repository import TelemetryRepository

# =========================================================
# SOLAX ANALYTICS
# =========================================================

from app.solax.analytics.settlement import (
    calculate_half_hour_energy,
)

# end = pd.Timestamp.now(tz=ZoneInfo("Europe/London"))
#
# start = end - timedelta(hours=hours)
#
# latest = repository.get_latest_snapshot()
# if latest is None:
#     st.warning("No telemetry data available.")
#
#     st.stop()
#
# latest = dict(latest)
#
# latest["pv_power_w"] = latest["solar_w"]
# latest["battery_power_w"] = latest["battery_w"]
# latest["grid_power_w"] = latest["grid_w"]
# latest["consumption_power_w"] = latest["consumption_w"]
#
# latest["pv1_power_w"] = latest["pv1_w"]
# latest["pv2_power_w"] = latest["pv2_w"]
# latest["house_load_w"] = latest["consumption_w"]
