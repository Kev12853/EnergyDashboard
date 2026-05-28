# =========================================================
# SOLAX KPI COMPONENTS
# =========================================================

import streamlit as st


# =========================================================
# KPI ROW
# =========================================================

def render_kpi_row(latest):

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric(
        "PV",
        f"{latest['pv_power_w']:.0f} W",
    )

    col2.metric(
        "Battery",
        f"{latest['battery_power_w']:.0f} W",
    )

    col3.metric(
        "SOC",
        f"{latest['battery_soc_pct']:.0f} %",
    )

    col4.metric(
        "Grid",
        f"{latest['grid_power_w']:.0f} W",
    )

    col5.metric(
        "House",
        f"{latest['house_load_w']:.0f} W",
    )


def render_settlement_kpis(
        settlement_df,
):
    st.subheader(
        "Energy Summary"
    )

    if (
            settlement_df is None
            or settlement_df.empty
    ):
        st.info(
            "No Energy Costs data available."
        )

        return

    total_import = (
        settlement_df["grid_import_kwh"]
        .sum()
    )

    total_export = (
        settlement_df["grid_export_kwh"]
        .sum()
    )

    total_pv = (
        settlement_df["pv_energy_kwh"]
        .sum()
    )

    total_house = (
        settlement_df[
            "house_load_energy_kwh"
        ].sum()
    )

    col1, col2, col3, col4 = (
        st.columns(4)
    )

    col1.metric(
        "Import kWh",
        f"{total_import:.2f}",
    )

    col2.metric(
        "Export kWh",
        f"{total_export:.2f}",
    )

    col3.metric(
        "PV kWh",
        f"{total_pv:.2f}",
    )

    col4.metric(
        "House kWh",
        f"{total_house:.2f}",
    )