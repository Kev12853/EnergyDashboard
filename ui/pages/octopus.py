import streamlit as st

from components.octopus.charts.octopus_dispatch_charts import (
    render_dispatch_timeline,
)

from components.octopus.tables.octopus_tables import (
    render_dispatch_history_table,
    render_tariff_table,
)


def render(
    dispatch_history_df,
    tariff_df,
):

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