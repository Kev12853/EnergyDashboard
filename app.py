import datetime

import altair as alt
import pandas as pd
import streamlit as st

from components.charts import (
    energy_chart,
    financial_chart
)
from components.filters import aggregation_selector

from services.aggregation import aggregate_data
from services.calculations import add_costs
from services.octopus_api import (
    get_consumption,
    get_tariffs,
    get_intelligent_dispatches
)

# -----------------------
# PAGE CONFIG
# -----------------------
st.set_page_config(layout="wide")
st.sidebar.title("⚡ Energy Dashboard")
#st.title("Energy Dashboard")

#------------------------
# STYLING
#------------------------
st.markdown("""
<style>

/* Main page */
.block-container {
    padding-top: 1rem;
    padding-bottom: 1rem;
}

/* Sidebar */
[data-testid="stSidebarContent"] {
    padding-top: 0rem;
}

/* Remove extra sidebar spacing */
section[data-testid="stSidebar"] > div {
    padding-top: 0rem;
}

/* Move sidebar content upward */
section[data-testid="stSidebar"] .block-container {
    padding-top: 0.5rem;
}

/* Dropdowns */
div[data-baseweb="select"] > div {
    cursor: pointer !important;
}

/* Date input */
[data-testid="stDateInput"] {
    cursor: pointer !important;
}

[data-testid="stDateInput"] input {
    cursor: pointer !important;
}

</style>
""", unsafe_allow_html=True)

# -----------------------
# AGGREGATION
# -----------------------
st.sidebar.subheader("Date Filters")

freq = aggregation_selector()

view_labels = {
    None: "Viewing: Half-hourly data",
    "D": "Viewing: Daily totals",
    "W": "Viewing: Weekly totals",
    "M": "Viewing: Monthly totals"
}

st.caption(view_labels.get(freq, ""))


# -----------------------
# DATE HELPERS
# -----------------------
def to_utc_range(start, end):
    start_dt = (
        datetime.datetime.combine(start, datetime.time.min)
        - datetime.timedelta(hours=1)
    )

    end_dt = (
        datetime.datetime.combine(end, datetime.time.max)
        - datetime.timedelta(hours=1)
    )

    return (
        start_dt.isoformat() + "Z",
        end_dt.isoformat() + "Z"
    )

# -----------------------
# DATE SELECTION
# -----------------------
today = datetime.date.today()

if "start_date" not in st.session_state:
    st.session_state.start_date = (
        today - datetime.timedelta(days=30)
    )

if "end_date" not in st.session_state:
    st.session_state.end_date = today

if "applied_range" not in st.session_state:
    st.session_state.applied_range = (
        st.session_state.start_date,
        st.session_state.end_date
    )

st.sidebar.divider()
st.sidebar.subheader("Date Selection")

dates = st.sidebar.date_input(
    "Select period",
    value=(
        st.session_state.start_date,
        st.session_state.end_date
    ),
    key="date_range"
)

# -----------------------
# APPLY DATES
# -----------------------
apply_dates = st.sidebar.button("Get Dates")

if apply_dates:

    if isinstance(dates, tuple) and len(dates) == 2:

        st.session_state.start_date = dates[0]
        st.session_state.end_date = dates[1]

        st.session_state.applied_range = (
            dates[0],
            dates[1]
        )

        st.rerun()

# Always use committed dates
start, end = st.session_state.applied_range

# -----------------------
# RESET DATES
# -----------------------
# if st.sidebar.button("Reset Dates"):
#
#     default_range = (
#         today - datetime.timedelta(days=30),
#         today
#     )
#
#     # Reset applied range
#     st.session_state.applied_range = default_range
#
#     # Remove widget state
#     if "date_range" in st.session_state:
#         del st.session_state["date_range"]
#
#     st.rerun()

# -----------------------
# REFRESH
# -----------------------

st.sidebar.divider()
st.sidebar.subheader("Refresh")

if st.sidebar.button("Refresh Data"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()

# -----------------------
# UTC RANGE
# -----------------------
period_from, period_to = to_utc_range(start, end)

# -----------------------
# LOAD DATA
# -----------------------
with st.spinner("Loading energy data..."):

    df = get_consumption(
        period_from=period_from,
        period_to=period_to
    )

    if not df.empty:

        # Local filtering
        start_dt = pd.to_datetime(start)
        end_dt = pd.to_datetime(end) + pd.Timedelta(days=1)

        df = df[
            (df["datetime"] >= start_dt) &
            (df["datetime"] < end_dt)
        ]

        df = df.sort_values("datetime")

        # Calculations
        df = add_costs(df)

        # Aggregation
        df = aggregate_data(df, freq)

        # Ensure datetime column exists
        if "datetime" not in df.columns:
            df = df.reset_index()

# -----------------------
# EMPTY STATE
# -----------------------
if df.empty:
    st.info(
        "Waiting for data from Octopus API..."
    )
    st.stop()

# -----------------------
# KPIs
# -----------------------
col1, col2, col3 = st.columns(3)

col1.metric(
    "Consumption (kWh)",
    round(df["consumption_kwh"].sum(), 2)
)

col2.metric(
    "Export (kWh)",
    round(df["export_kwh"].sum(), 2)
)

if "net" in df.columns:
    col3.metric(
        "Net (£)",
        round(df["net"].sum(), 2)
    )

# -----------------------
# DISPATCH TIMELINE
# -----------------------
dispatch_df = get_intelligent_dispatches()

if not dispatch_df.empty:

    with st.expander(
        "🔌 Intelligent Charging Schedule",
        expanded=True
    ):

        timeline = (
            alt.Chart(dispatch_df)
            .mark_bar(cornerRadius=5)
            .encode(
                x=alt.X(
                    "startDt:T",
                    title="Time (London)"
                ),
                x2="endDt:T",
                y=alt.Y(
                    "status:N",
                    title=None
                ),
                color=alt.Color(
                    "status:N",
                    scale=alt.Scale(
                        domain=["Planned", "Completed"],
                        range=["#2ecc71", "#3498db"]
                    )
                ),
                tooltip=[
                    alt.Tooltip(
                        "startDt:T",
                        format="%H:%M",
                        title="Start"
                    ),
                    alt.Tooltip(
                        "endDt:T",
                        format="%H:%M",
                        title="End"
                    ),
                    alt.Tooltip(
                        "deltaKwh:Q",
                        title="Est. kWh"
                    )
                ]
            )
            .properties(height=120)
        )

        now_line = (
            alt.Chart(
                pd.DataFrame({
                    "now": [pd.Timestamp.now()]
                })
            )
            .mark_rule(
                color="red",
                strokeDash=[4, 4]
            )
            .encode(x="now:T")
        )

        st.altair_chart(
            timeline + now_line,
            width="stretch"
        )

# -----------------------
# MAIN CHART
# -----------------------
col1, col2 = st.columns(2)

with col1:
    energy_chart(df, freq)

with col2:
    financial_chart(df, freq)
# -----------------------
# RAW DATA TABLE
# -----------------------
with st.expander("Show Data"):

    display_df = df.copy()

    display_df = display_df.rename(columns={
        "datetime": "Date / Time",
        "consumption_kwh": "Consumption (kWh)",
        "export_kwh": "Export (kWh)",
        "cost": "Cost (£)",
        "revenue": "Revenue (£)",
        "net": "Net (£)"
    })

    numeric_columns = [
        "Consumption (kWh)",
        "Export (kWh)",
        "Cost (£)",
        "Revenue (£)",
        "Net (£)"
    ]

    # Totals row
    totals = {
        col: display_df[col].sum()
        for col in numeric_columns
    }

    totals["Date / Time"] = "TOTAL"

    display_df = pd.concat(
        [display_df, pd.DataFrame([totals])],
        ignore_index=True
    )

    # Format datetime
    display_df["Date / Time"] = (
        display_df["Date / Time"]
        .apply(
            lambda x:
            x.strftime("%d %b %Y %H:%M")
            if isinstance(x, pd.Timestamp)
            else x
        )
    )

    # Format numbers
    display_df["Consumption (kWh)"] = (
        display_df["Consumption (kWh)"]
        .round(3)
    )

    display_df["Export (kWh)"] = (
        display_df["Export (kWh)"]
        .round(3)
    )

    for col in [
        "Cost (£)",
        "Revenue (£)",
        "Net (£)"
    ]:
        display_df[col] = (
            display_df[col]
            .map("£{:.2f}".format)
        )

    st.dataframe(
        display_df[
            ["Date / Time"] + numeric_columns
        ],
        width="stretch"
    )

# -----------------------
# TARIFF TABLE
# -----------------------
with st.expander("Tariffs"):

    tariff_df = get_tariffs(
        period_from=period_from,
        period_to=period_to
    )

    if tariff_df.empty:

        st.warning(
            "No tariff data available."
        )

    else:

        tariff_display = tariff_df.copy()

        tariff_display["Time"] = (
            tariff_display["datetime"]
            .dt.strftime("%d %b %H:%M")
        )

        tariff_display["Unit Rate"] = (
            tariff_display["unit_rate"]
            .map("£{:.3f}".format)
        )

        st.dataframe(
            tariff_display[
                ["Time", "Unit Rate"]
            ],
            width="stretch"
        )

# -----------------------
# DEBUG
# -----------------------
# if st.sidebar.toggle("Debug"):
#
#     st.write(
#         "DEBUG INFO:",
#         df["datetime"].min(),
#         "→",
#         df["datetime"].max()
#     )
#
#     st.write("ROWS:", len(df))