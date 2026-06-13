import streamlit as st

from app.dashboard.helpers.operations import (
    get_current_state,
    get_next_action,
    get_operations_status,
    get_system_health,
)


def render(
    latest,
    latest_upload_time,
    data_age_minutes,
):
    st.title("Operations")

    st.markdown(
        """
    <style>
    .mybox {
        border: 2px solid red;
        border-radius: 50px;
        padding: 1rem;
        margin:1.5rem;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    with st.container():
        operations_status = get_operations_status(data_age_minutes)
        st.markdown(
            f"""
            <div class="mybox">
                <span style="font-size:2em;font-weight:bold;">
                    {operations_status["icon"]} {operations_status["text"]}
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
    main_col_left, main_col_right = st.columns(2)

    with main_col_left:
        with st.container(border=True):
            st.subheader("System Health")
            system_health = get_system_health(latest, latest_upload_time, data_age_minutes)

            mainleft_inner_left, mainleft_inner_middle, mainleft_inner_right = st.columns([3, 2, 3])

            with mainleft_inner_left:
                st.write(f"{system_health['poller']['icon']} Poller")
                st.write(f"{system_health['inverter']['icon']} Inverter")

            with mainleft_inner_middle:
                st.write(f"{system_health['scheduler']['icon']} Scheduler")
                st.write(f"{system_health['notifications']['icon']} Notifications")

    with main_col_right:
        with st.container(border=True):
            st.subheader("Current State")
            mainright_inner_left, mainright_inner_right = st.columns(2)

            with mainright_inner_left:
                with st.container():
                    current = get_current_state(latest)
                    st.markdown(f"#### {current['work_mode']}")
                    st.write(f"{current['status_icon']} {current['status_text']}")


            with mainright_inner_right:
                with st.container():
                    next_action = get_next_action(latest, latest_upload_time, data_age_minutes)
                    st.subheader("Next Action")
                    st.markdown(f"##### {next_action['time']}")
                    st.write(next_action["action"])
