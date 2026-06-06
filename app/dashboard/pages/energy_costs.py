import streamlit as st

from app.dashboard.components.solax.kpis.solax_kpis import (
    render_settlement_kpis,
)

from app.dashboard.components.solax.tables.solax_tables import (
    render_settlement_table,
)


def render(
    settlement_df,
):

    st.title("Energy Costs")

    with st.container(border=True):
        render_settlement_kpis(settlement_df)

    with st.container(border=True):
        render_settlement_table(settlement_df)

    total_import_cost = settlement_df["import_cost_gbp"].sum()

    st.metric(
        "Import Cost",
        f"£{total_import_cost:.2f}",
    )
