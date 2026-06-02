import streamlit as st
import pandas as pd


def render(
    latest_upload_time,
    data_age_minutes,
    df: pd.DataFrame,
    settlement_df: pd.DataFrame,
    dispatch_history_df: pd.DataFrame,
):

    st.title(
        "Diagnostics"
    )

    # =====================================================
    # SYSTEM STATUS
    # =====================================================

    st.subheader(
        "System Status"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Latest Telemetry",
            str(latest_upload_time),
        )

    with col2:
        st.metric(
            "Data Age (mins)",
            f"{data_age_minutes:.1f}",
        )

    with col3:

        if data_age_minutes < 5:
            status = "Healthy"
        elif data_age_minutes < 30:
            status = "Warning"
        else:
            status = "Stale"

        st.metric(
            "Telemetry Status",
            status,
        )

    st.divider()

    # =====================================================
    # DATA COUNTS
    # =====================================================

    st.subheader(
        "Data Volumes"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Telemetry Rows",
            len(df),
        )

    with col2:
        st.metric(
            "Settlement Rows",
            len(settlement_df),
        )

    with col3:
        st.metric(
            "Dispatch Rows",
            len(dispatch_history_df),
        )

    st.divider()

    # =====================================================
    # TELEMETRY DATA
    # =====================================================

    with st.expander(
        "Telemetry Data",
        expanded=False,
    ):

        st.write(
            "Columns:"
        )

        st.code(
            "\n".join(df.columns)
        )

        st.dataframe(
            df.tail(50),
            width='stretch',
        )

    # =====================================================
    # SETTLEMENT DATA
    # =====================================================

    with st.expander(
        "Settlement Data",
        expanded=False,
    ):

        st.write(
            "Columns:"
        )

        st.code(
            "\n".join(
                settlement_df.columns
            )
        )

        st.dataframe(
            settlement_df.tail(50),
            width='stretch',
        )

    # =====================================================
    # OCTOPUS DATA
    # =====================================================

    with st.expander(
        "Dispatch History",
        expanded=False,
    ):

        st.dataframe(
            dispatch_history_df.tail(50),
            width='stretch',
        )

    # =====================================================
    # SUMMARY STATISTICS
    # =====================================================

    if not df.empty:

        with st.expander(
            "Telemetry Statistics",
            expanded=False,
        ):

            st.dataframe(
                df.describe(
                    include="all"
                ),
                width='stretch',
            )