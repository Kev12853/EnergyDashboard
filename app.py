import pandas as pd
import streamlit as st

from streamlit_autorefresh import (
    st_autorefresh,
)

# =========================================================
# DATABASE
# =========================================================

from services.db import (
    get_connection,
)

from services.octopus.storage.schema import (
    create_dispatches_table, create_tariffs_table, create_agreements_table, create_accounts_table,
)

# =========================================================
# SOLAX DATA
# =========================================================

from services.solax.storage.repository import (
    get_latest_snapshot_row,
    get_recent_telemetry_dataframe,
)


from services.octopus.storage.repository import (
    get_recent_tariffs,
)

# =========================================================
# SOLAX ANALYTICS
# =========================================================

from services.solax.analytics.summary import (
    calculate_daily_summary,
)

from services.solax.analytics.energy import (
    calculate_daily_energy_summary,
)

from services.solax.analytics.settlement import (
    calculate_half_hour_energy,
)

# =========================================================
# OCTOPUS API
# =========================================================

from services.octopus.api.octopus_api import (
    get_intelligent_dispatches,
)

# =========================================================
# OCTOPUS ANALYTICS
# =========================================================

from services.octopus.analytics.dispatches import (
    normalize_dispatches,
)

from services.octopus.analytics.dispatch_matching import (
    apply_dispatch_flags,
)

from services.octopus.analytics.costs import (
    apply_import_costs,
)

from services.octopus.storage.repository import (
    get_all_tariffs,
)

# =========================================================
# OCTOPUS STORAGE
# =========================================================

from services.octopus.storage.repository import (
    upsert_dispatches,
    get_dispatch_history,
)

# =========================================================
# SOLAX COMPONENTS
# =========================================================

from components.solax.charts.solax_charts import (
    render_solar_chart,
    render_battery_chart,
)

from components.solax.kpis.solax_kpis import (
    render_kpi_row,
    render_settlement_kpis,
)

from components.solax.tables.solax_tables import (
    render_daily_summary_table,
    render_daily_energy_summary_table,
    render_settlement_table,
    render_raw_data_table,
)

# =========================================================
# OCTOPUS COMPONENTS
# =========================================================

from components.octopus.charts.octopus_dispatch_charts import (
    render_dispatch_timeline,
)

from components.octopus.tables.octopus_tables import (
    render_tariff_table,
    render_dispatch_history_table,
)

# region ** config **
# =========================================================
# APP CONFIG
# =========================================================

st.set_page_config(
    page_title="Dashboard",
    layout="wide",
)

st_autorefresh(
    interval=30_000,
    key="dashboard_refresh",
)
# endregion ** config **

# region ** CSS **
# =========================================================
# CUSTOM STYLING
# =========================================================

st.markdown(
    """
    <style>

    section[data-testid="stSidebar"] {
        width: 300px !important;
    }

    section[data-testid="stSidebar"] > div {
        width: 300 !important;
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

    /* Selectbox sizing */
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

#endregion ** CSS **

#region ** Navigation **
# =========================================================
# SIDEBAR NAVIGATION
# =========================================================

with st.sidebar:

    st.title(
        "⚡ Energy Dashboard"
    )

    st.divider()

    st.markdown(
        (
            '<div class="sidebar-heading">'
            'Navigation'
            '</div>'
        ),
        unsafe_allow_html=True,
    )

    page = st.radio(
        "Navigation Menu",
        [
            "Overview",
            "Energy Costs",
            "Octopus",
            "Energy Data",
            "Diagnostics",
        ],
        label_visibility="collapsed",
    )

    st.divider()

    hours = st.selectbox(
        "Time Window",
        options=[1, 6, 12, 24, 48],
        index=3,
        key="time_window_selector",
        format_func=lambda x: f"{x} Hours",
    )
# endregion ** Navigation **

#region ** Initialisation **
# =========================================================
# DATABASE INITIALISATION
# =========================================================

from services.startup import (
    start_services,
)

connection = get_connection()

create_dispatches_table(
    connection
)

create_tariffs_table(
    connection
)

create_agreements_table(
    connection
)

create_accounts_table(
    connection
)


start_services()


#endregion ** Initialisation **

# region ** SOLAX Data **
# =========================================================
# LOAD SOLAX DATA
# =========================================================

df = get_recent_telemetry_dataframe(
    hours=hours
)

latest = get_latest_snapshot_row()

# =========================================================
# EMPTY STATE
# =========================================================

if latest is None or df.empty:

    st.warning(
        "No telemetry data available."
    )

    st.stop()

# =========================================================
# DATA FRESHNESS
# =========================================================

latest_upload_time = latest[
    "upload_time"
]

data_age_minutes = (
    pd.Timestamp.now()
    - latest_upload_time
).total_seconds() / 60

# endregion ** SOLAX Data **

# region ** OCTOPUS Data **
# =========================================================
# LOAD OCTOPUS DATA
# =========================================================


tariff_df = (
    get_recent_tariffs()
)

dispatch_history_df = (
    get_dispatch_history(
        days=7
    )
)

# =========================================================
# Energy Costs ANALYTICS
# =========================================================

settlement_df = (
    calculate_half_hour_energy(df)
)

full_tariff_df = (
    get_all_tariffs()
)

settlement_df = (
    apply_import_costs(
        settlement_df,
        full_tariff_df,
    )
)

settlement_df = (
    apply_dispatch_flags(
        settlement_df,
        dispatch_history_df,
    )
)
# endregion ** OCTOPUS Data **

#region ** Overview **
# =========================================================
# OVERVIEW
# =========================================================

if page == "Overview":

    st.title(
        "Energy Dashboard"
    )

    st.caption(
        f"Latest inverter update: "
        f"{latest_upload_time}"
    )

    st.caption(
        f"Data age: "
        f"{data_age_minutes:.1f} minutes"
    )

    with st.container(
            border=True
    ):
        render_kpi_row(latest)

    with st.container(
        border=True):
        render_solar_chart(df)

    with st.container(
            border=True):
        render_battery_chart(df)

    with st.container(
            border=True):
        render_settlement_kpis(
            settlement_df
        )
#endregion ** Overview **

#region ** Energy Costs **
# =========================================================
# ENERGY COSTS
# =========================================================

elif page == "Energy Costs":

    st.title(
        "Energy Costs"
    )


    with st.container(
            border=True
    ):
        render_settlement_kpis(
            settlement_df
        )

    with st.container(
            border=True
    ):
        render_settlement_table(
            settlement_df
        )

    total_import_cost = (
        settlement_df[
            "import_cost_gbp"
        ].sum()
    )

    st.metric(
        "Import Cost",
        f"£{total_import_cost:.2f}",
    )

#endregion ** Energy Costs **

#region ** Octopus **
# =========================================================
# OCTOPUS
# =========================================================

elif page == "Octopus":

    st.title(
        "Octopus Energy"
    )

    render_dispatch_timeline(
        dispatch_history_df
    )

    with st.container(
            border=True
    ):
        with st.expander(
                "Dispatch History",
                expanded=False,
        ):
            render_dispatch_history_table(
                dispatch_history_df
            )

        with st.expander(
                "Tariffs",
                expanded=False,
        ):
            render_tariff_table(
                tariff_df
            )
#endregion ** Octopus **

#region ** Energy Data **
# =========================================================
# Energy Data
# =========================================================

elif page == "Energy Data":

    st.title(
        "Energy Data"
    )

    summary_df = (
        calculate_daily_summary(df)
    )

    with st.container(
            border=True
    ):
        render_daily_summary_table(
            summary_df
        )

    energy_summary_df = (
        calculate_daily_energy_summary(df)
    )

    with st.container(
            border=True
    ):
        render_daily_energy_summary_table(
            energy_summary_df
        )

    with st.container(
            border=True
    ):
        st.subheader("Data")

        with st.expander(
                "Raw Telemetry Data",
                expanded=False,
        ):
            render_raw_data_table(df)

#endregion ** Energy Data **

#region ** Diagnostics **
# =========================================================
# DIAGNOSTICS
# =========================================================

elif page == "Diagnostics":

    st.title(
        "Diagnostics"
    )

    st.write(
        "Latest Upload Time",
        latest_upload_time,
    )

    st.write(
        "Data Age Minutes",
        round(data_age_minutes, 2),
    )

    st.write(
        "Telemetry Rows",
        len(df),
    )

    st.write(
        "Energy Costs Rows",
        len(settlement_df),
    )

    st.write(
        "Dispatch Rows",
        len(dispatch_history_df),
    )
#endregion ** Diagnostics **