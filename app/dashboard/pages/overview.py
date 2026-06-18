import pandas as pd
import streamlit as st

from app.backend.services.system_health_service import (
    HealthStatus,
    get_system_health,
)
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
    system_health=None,
):

    st.title("Energy Dashboard")

    health = system_health or get_system_health(
        last_snapshot_time=latest_upload_time,
        last_successful_poll=latest_upload_time,
    )

    if health.overall_status == HealthStatus.OPERATIONAL:
        icon = "🟢"
        status = "Healthy"

    elif health.overall_status == HealthStatus.DEGRADED:
        icon = "🟡"
        status = "Delayed"

    else:
        icon = "🔴"
        status = "Offline"

    last_update = pd.Timestamp(latest_upload_time).strftime("%d %b %H:%M")
    work_mode = latest["work_mode"]
      
    with st.container(border=True):
        st.markdown(
            f"""
            <span style="font-size:1.4em; font-weight:bold;">
                {icon} Telemetry {status}
            </span>
            
            <span style="font-size:1.2em;">
                &nbsp;&nbsp;
                 | ⚡ {work_mode}
            </span>
            
            <span style="font-size:1.2em;">
                &nbsp;&nbsp;
                Last Update: {last_update}
         
            </span>
            

""",
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        render_kpi_row(latest)

    with st.container(border=True):
        render_solar_chart(df)

    with st.container(border=True):
        render_battery_chart(df)

    with st.container(border=True):
        render_settlement_kpis(settlement_df)
