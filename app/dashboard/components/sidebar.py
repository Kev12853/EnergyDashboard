import streamlit as st

def render_sidebar():

    with st.sidebar:
        st.title("⚡ Energy Dashboard")

        st.divider()

        st.markdown(
            ('<div class="sidebar-heading">Navigation</div>'),
            unsafe_allow_html=True,
        )

        page = st.radio(
            "Navigation Menu",
            [
                "Operations",
                "Overview",
                "Health",
                "Energy Costs",
                "Octopus",
                "Energy Data",
                "Diagnostics",
                "Automation",
            ],
            label_visibility="collapsed",
        )

        st.divider()

        hours = st.selectbox(
            "Time Window",
            options=[1, 6, 12, 24, 48],
            index=3,
            format_func=lambda x: f"{x} Hours",
        )

    return (
        page,
        hours,
    )
