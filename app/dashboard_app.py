import sys
from pathlib import Path

import pandas as pd
import streamlit as st

from datetime import timedelta

from streamlit_autorefresh import (
    st_autorefresh,
)

# =========================================================
# SOLAX REPOSITORY
# =========================================================

from app.solax.storage.repository import TelemetryRepository

# =========================================================
# OCTOPUS STORAGE
# =========================================================


from app.octopus.storage.repository import (
    get_recent_tariffs,
    get_all_tariffs,
    get_dispatch_history,
)

# =========================================================
# SOLAX ANALYTICS
# =========================================================

from app.solax.analytics.settlement import (
    calculate_half_hour_energy,
)

# =========================================================
# OCTOPUS ANALYTICS
# =========================================================

from app.octopus.analytics.dispatch_matching import (
    apply_dispatch_flags,
)

from app.octopus.analytics.costs import (
    apply_import_costs,
)

# =========================================================
# PAGE IMPORTS
# =========================================================

from app.dashboard.pages import (
    automation,
    octopus,
    energy_data,
    energy_costs,
    diagnostics,
    overview,
)
from app.dashboard.components.sidebar import (
    render_sidebar,
)
# =========================================================
# STARTUP
# =========================================================

from app.backend.bootstrap import (
    start_services,
)

from app.backend.storage.db import (
    get_connection,
)

# =========================================================
# APP CONFIG
# =========================================================

st.set_page_config(
    page_title="Dashboard",
    layout="wide",
)

st_autorefresh(
    interval=30 * 1000,  # 30 seconds
    key="dashboard_refresh",
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown(
    """
    <style>

    section[data-testid="stSidebar"] {
        width: 300px !important;
    }

    section[data-testid="stSidebar"] > div {
        width: 300px !important;
    }

    .sidebar-heading {
        font-size: 20px;
        font-weight: 600;
        margin-top: 10px;
        margin-bottom: 5px;
    }

    div[data-baseweb="select"] * {
        cursor: pointer !important;
    }

    div[role="radiogroup"] label {
        cursor: pointer !important;
    }

    div[data-baseweb="select"] {
        width: 160px !important;
    }

    div[data-baseweb="popover"] {
        width: 160px !important;
    }

    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 1rem;
        padding-left: 2rem;
        padding-right: 2rem;
    }

    .kpi-card {

        background: #0E1B2A;

        border: 1px solid rgba(
            0,
            212,
            255,
            0.15
        );

        border-radius: 12px;

        padding: 18px;

        box-shadow:
            0 0 10px rgba(
                0,
                212,
                255,
                0.05
            );
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# SIDEBAR
# =========================================================
page, hours = render_sidebar()

# =========================================================
# DATABASE INITIALISATION
# =========================================================

connection = get_connection()

from app.backend.storage.schema import (
    create_all_tables,
)

create_all_tables(connection)


@st.cache_resource
def initialise_services():

    start_services()
    return True


initialise_services()
# =========================================================
# REPOSITORY
# =========================================================

repository = TelemetryRepository(connection)

from app.backend.automation.repository import (
    AutomationRepository,
)

automation_repo = AutomationRepository(connection)

automation_rule = automation_repo.get_periods()

from datetime import datetime

from app.backend.automation.models import (
    SchedulePeriod,
)

if automation_rule is None:
    automation_rule = SchedulePeriod(
        id=None,
        name="New Period",
        source="MANUAL",
        enabled=False,
        start_time="16:00",
        end_time="19:00",
        mode="SELF_USE",
        priority=10,
        updated_at=datetime.now(),
    )

# =========================================================
# LOAD SOLAX DATA
# =========================================================

from zoneinfo import ZoneInfo

end = pd.Timestamp.now(tz=ZoneInfo("Europe/London"))

start = end - timedelta(hours=hours)

latest = repository.get_latest_snapshot()
if latest is None:
    st.warning("No telemetry data available.")
    st.stop()

latest = dict(latest)

latest["pv_power_w"] = latest["solar_w"]
latest["battery_power_w"] = latest["battery_w"]
latest["grid_power_w"] = latest["grid_w"]
latest["consumption_power_w"] = latest["consumption_w"]

latest["pv1_power_w"] = latest["pv1_w"]
latest["pv2_power_w"] = latest["pv2_w"]
latest["house_load_w"] = latest["consumption_w"]
# =========================================================
# EMPTY STATE
# =========================================================


# =========================================================
# LOAD HISTORY
# =========================================================

try:
    history_1m = repository.get_1m_history(
        start=start,
        end=end,
    )

    df = pd.DataFrame([dict(row) for row in history_1m])
    if not df.empty:
        df["upload_time"] = pd.to_datetime(df["bucket_start"])

        df["timestamp"] = df["upload_time"]

        df["pv_power_w"] = df["avg_solar_w"]

        df["house_load_w"] = df["avg_consumption_w"]

        df["consumption_power_w"] = df["avg_consumption_w"]

        df["grid_power_w"] = df["avg_grid_w"]

        df["battery_power_w"] = df["avg_battery_w"]
        df.drop(
            columns=["bucket_start"],
            inplace=True,
        )

except Exception:
    #
    # Temporary fallback until
    # aggregation pipeline fully wired
    #

    df = pd.DataFrame()

# =========================================================
# DATA FRESHNESS
# =========================================================

latest_timestamp = latest["timestamp"]

data_age_minutes = (
    pd.Timestamp.now("UTC") - pd.Timestamp(latest_timestamp)
).total_seconds() / 60

# =========================================================
# LOAD OCTOPUS DATA
# =========================================================

tariff_df = get_recent_tariffs()
dispatch_history_df = get_dispatch_history(days=7)
# =========================================================
# ENERGY COST ANALYTICS
# =========================================================

if not df.empty:
    settlement_df = calculate_half_hour_energy(df)

    full_tariff_df = get_all_tariffs()

    settlement_df = apply_import_costs(
        settlement_df,
        full_tariff_df,
    )

    settlement_df = apply_dispatch_flags(
        settlement_df,
        dispatch_history_df,
    )

else:
    settlement_df = pd.DataFrame()

# =========================================================
# PAGE ROUTING
# =========================================================

if page == "Overview":
    overview.render(
        latest=latest,
        df=df,
        settlement_df=settlement_df,
        latest_upload_time=latest_timestamp,
        data_age_minutes=data_age_minutes,
    )

elif page == "Energy Costs":
    energy_costs.render(
        settlement_df=settlement_df,
    )

elif page == "Octopus":
    octopus.render(
        dispatch_history_df=dispatch_history_df,
        tariff_df=tariff_df,
    )

elif page == "Energy Data":
    energy_data.render(
        df=df,
    )

elif page == "Diagnostics":
    diagnostics.render(
        latest_upload_time=latest_timestamp,
        data_age_minutes=data_age_minutes,
        df=df,
        settlement_df=settlement_df,
        dispatch_history_df=dispatch_history_df,
    )
elif page == "Automation":
    automation.render(
        repo=automation_repo,
    )
