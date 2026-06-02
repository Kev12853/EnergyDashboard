import streamlit as st

from app.dashboard.components.shared.dataframe_formatting import (
    format_dataframe_columns,
)


def render_daily_summary_table(
    summary_df,
):

    st.subheader(
        "Daily Summary"
    )

    if summary_df is None or summary_df.empty:

        st.info(
            "No summary data available."
        )

        return

    display_df = format_dataframe_columns(
        summary_df,
        datetime_format="date_only",
    )


    st.dataframe(
        display_df,
        width="stretch",
    )


def render_raw_data_table(
    df,
):

    st.subheader(
        "Raw Telemetry"
    )

    if df is None or df.empty:

        st.info(
            "No telemetry data available."
        )

        return

    display_df = (
        format_dataframe_columns(df)
    )

    st.dataframe(
        display_df,
        width="content",
        hide_index=True,
    )

def render_daily_energy_summary_table(
        energy_summary_df,
):

    st.subheader(
        "Daily Energy Summary"
    )

    if (
            energy_summary_df is None
            or energy_summary_df.empty
    ):
        st.info(
            "No energy summary available."
        )

        return

    display_df = (
        format_dataframe_columns(
            energy_summary_df,
            datetime_format="date_only",
        )
    )

    st.dataframe(
        display_df,
        width="content",
        hide_index=True,
    )

def render_settlement_table(
        settlement_df,
):

    st.subheader(
        "30 Minute Energy Costs Periods"
    )

    if (
            settlement_df is None
            or settlement_df.empty
    ):
        st.info(
            "No Energy Costs data available."
        )

        return

    display_df = (
        format_dataframe_columns(
            settlement_df
        )
    )

    st.dataframe(
        display_df,
        width="content",
        hide_index=True,
    )