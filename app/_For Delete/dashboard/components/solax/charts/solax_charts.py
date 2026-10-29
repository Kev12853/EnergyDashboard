"""
solax_charts.py

Plotly chart components used by the dashboard.

The incoming dataframe is expected to contain aggregated
telemetry data with timestamps and power values in watts.

Charts convert power to kilowatts and reshape the dataframe
into Plotly's preferred long format before plotting.
"""

import streamlit as st
import plotly.express as px


# Consistent colour palette used throughout the dashboard.
ENERGY_COLORS = {
    "Solar Generation": "#FFC107",
    "House Load": "#64B5F6",
    "Battery": "#66BB6A",
    "Grid": "#EF5350",
}


def apply_trace_styling(fig):
    """
    Apply standard line and tooltip styling.
    """

    fig.update_traces(
        line=dict(width=4),
        hovertemplate="<b>%{fullData.name}</b>: %{y:.1f} kW<extra></extra>",
    )


def apply_chart_layout(fig):

    fig.update_layout(
        hovermode="x unified",
        xaxis=dict(hoverformat="%a %d %b %H:%M"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
        ),
        legend_title_text="",
        height=450,
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=20,
        ),
        hoverlabel=dict(font_size=15),
        xaxis_title=None,
    )


def render_solar_chart(df):
    """
    Render solar generation and house load time series.
    """

    if df.empty:
        st.info("No data available for selected period.")
        return

    st.subheader("Solar and House Load")

    chart_df = df[
        [
            "upload_time",
            "pv_power_w",
            "house_load_w",
        ]
    ].copy()

    chart_df = chart_df.rename(
        columns={
            "pv_power_w": "Solar Generation",
            "house_load_w": "House Load",
        }
    )

    # Convert wide format:
    # upload_time | Solar Generation | House Load
    # into long format:
    # upload_time | Series | Power_W
    # allowing Plotly to create one line per series.

    chart_df = chart_df.melt(
        id_vars="upload_time",
        var_name="Series",
        value_name="Power_W",
    )

    chart_df["Power_kW"] = chart_df["Power_W"] / 1000

    fig = px.line(
        chart_df,
        x="upload_time",
        y="Power_kW",
        color="Series",
        color_discrete_map=ENERGY_COLORS,
    )

    fig.update_traces(
        line=dict(width=4),
        hovertemplate="<b>%{fullData.name}</b>: %{y:.1f} kW<extra></extra>",
    )

    apply_chart_layout(fig)

    st.plotly_chart(
        fig,
        width="stretch",
    )


def render_battery_chart(df):
    """
    Render battery and grid power time series.
    """

    if df.empty:
        st.info("No data available for selected period.")
        return

    st.subheader("Battery and Grid")

    chart_df = df[
        [
            "upload_time",
            "battery_power_w",
            "grid_power_w",
        ]
    ].copy()

    chart_df = chart_df.rename(
        columns={
            "battery_power_w": "Battery",
            "grid_power_w": "Grid",
        }
    )

    # Convert wide format into Plotly-friendly long format.
    chart_df = chart_df.melt(
        id_vars="upload_time",
        var_name="Series",
        value_name="Power_W",
    )

    chart_df["Power_kW"] = chart_df["Power_W"] / 1000

    fig = px.line(
        chart_df,
        x="upload_time",
        y="Power_kW",
        color="Series",
        color_discrete_map=ENERGY_COLORS,
    )

    fig.update_traces(
        line=dict(width=4),
        hovertemplate="<b>%{fullData.name}</b>: %{y:.1f} kW<extra></extra>",
    )

    apply_chart_layout(fig)

    st.plotly_chart(
        fig,
        width="stretch",
    )

    with st.expander("View Data"):
        st.dataframe(
            df.sort_values(
                "timestamp",
                ascending=False,
            ),
            width="stretch",
        )
