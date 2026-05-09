import streamlit as st
import datetime


import streamlit as st
import datetime


def date_input_range():
    today = datetime.date.today()

    # Initialise session state once
    if "start_date" not in st.session_state:
        st.session_state.start_date = today - datetime.timedelta(days=30)

    if "end_date" not in st.session_state:
        st.session_state.end_date = today

    dates = st.sidebar.date_input(
        "Select period",
        [st.session_state.start_date, st.session_state.end_date],
        key="date_range"
    )

    # Update session state when user changes input
    if isinstance(dates, list) and len(dates) == 2:
        st.session_state.start_date = dates[0]
        st.session_state.end_date = dates[1]

    return st.session_state.start_date, st.session_state.end_date


def aggregation_selector():
    # Set default only on first run
    if "aggregation_selector" not in st.session_state:
        st.session_state.aggregation_selector = "Daily"

    label = st.sidebar.selectbox(
        "View By",
        ["Half-Hourly", "Daily", "Weekly", "Monthly"],
        key="aggregation_selector"
    )

    if label == "Half-Hourly":
        return None

    return {
        "Daily": "D",
        "Weekly": "W",
        "Monthly": "ME"
    }[label]