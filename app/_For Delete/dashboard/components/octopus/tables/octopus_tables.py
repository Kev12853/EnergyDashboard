import streamlit as st

from app.dashboard.components.shared.dataframe_formatting import (
    format_dataframe_columns,
)


def render_tariff_table(
    tariff_df,
):

    st.subheader("Octopus Import Tariffs")

    if tariff_df is None or tariff_df.empty:
        st.info("No tariff data available.")

        return

    display_df = format_dataframe_columns(
        tariff_df,
        datetime_format="compact",
    )

    st.dataframe(
        display_df,
        width="content",
        hide_index=True,
    )


def render_dispatch_history_table(
    dispatch_history_df,
):

    st.subheader("Dispatch History")

    if dispatch_history_df is None or dispatch_history_df.empty:
        st.info("No dispatch history available.")

        return

    display_df = format_dataframe_columns(
        dispatch_history_df,
        datetime_format="compact",
    )

    st.dataframe(
        display_df,
        width="content",
        hide_index=True,
    )
