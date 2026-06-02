import streamlit as st

from app.dashboard.components.solax.charts.solax_charts import (
    render_solar_chart,
    render_battery_chart,
)

from app.dashboard.components.solax.kpis.solax_kpis import (
    render_kpi_row,
    render_settlement_kpis,
)


def render(
    latest,
    df,
    settlement_df,
    latest_upload_time,
    data_age_minutes,
):

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


    with st.container(border=True):
        render_kpi_row(latest)

    with st.container(border=True):
        render_solar_chart(df)

    with st.container(border=True):
        render_battery_chart(df)

    with st.container(border=True):
        render_settlement_kpis(
            settlement_df
        )