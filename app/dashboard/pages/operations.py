import streamlit as st

from app.backend.services.system_health_service import (
    get_system_health as build_system_health,
    HealthStatus,
)
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
    system_health=None,
):
    health = system_health or build_system_health(
        last_snapshot_time=latest_upload_time,
        last_successful_poll=latest_upload_time,
    )

    st.title("Operations")

# region CSS Styles
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
# endregion


# region Operation Status
    with st.container():
        operations_status = get_operations_status(health)
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
    # endregion

    # set up 2 columns for stats cards
    main_col_left, main_col_right = st.columns(2)


# region System Health
    with main_col_left:
        # System Health
        with st.container(border=True):
            st.subheader("System Health")
            system_health = get_system_health(health)

            # set up 3 columns for health cards
            mainleft_inner_left, mainleft_inner_middle, mainleft_inner_right = st.columns([4, 4, 1])

            #
            with mainleft_inner_left:
                st.markdown("#### Status")
                st.markdown("##### Healthy")

                st.markdown("##### Age")
                st.markdown("###### 11 s")
            #
            import pandas as pd

            with mainleft_inner_middle:
                if system_health["last_successful_poll"]:
                    last_poll = pd.Timestamp(system_health["last_successful_poll"])
                    now = pd.Timestamp.now(tz=last_poll.tz)

                    if last_poll.date() == now.date():
                        last_poll_text = last_poll.strftime("Today %H:%M")
                    else:
                        last_poll_text = last_poll.strftime("%d %b %H:%M")

                    st.markdown("### Last update")
                    st.markdown(f"##### {last_poll_text}")

# endregion

# region Current Status

    with main_col_right:
        # System State
        with st.container(border=True):

            mainright_inner_left, mainright_inner_middle, mainright_inner_right = st.columns([3, 3, 2])

            with mainright_inner_left:
                #
                with st.container():
                    st.subheader("Current State")

                    if health.overall_status == HealthStatus.OPERATIONAL:
                        current = get_current_state(
                            latest,
                            health,
                        )

                    else:
                        current = {
                            "work_mode": "Last known state",
                            "status_icon": "⚫",
                            "status_text": (f"Latest data {health.data_age_text} old"),
                        }

                    st.markdown(f"##### {current['work_mode']}")

                    st.write(
                        current["status_icon"],
                        current["status_text"],
                    )


            with mainright_inner_middle:
                #
                with st.container():
                    st.subheader("Next Action")
                    next_action = get_next_action(latest, latest_upload_time, data_age_minutes)
                    st.markdown(f"##### {next_action['action']}")
                    st.write(next_action['time'])
    # endregion
