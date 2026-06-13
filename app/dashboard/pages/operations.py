import streamlit as st

def get_current_state(latest):
    return {
        "work_mode": latest["work_mode"],
        "status_icon": "🟢",
        "status_text": "Following Schedule",
    }

def get_operations_status(
    data_age_minutes,
):
    return {
        "icon": "🟢",
        "text": "Operating Normally",
    }

def get_system_health():

    return {
        "poller": {
            "icon": "🟢",
            "text": "Healthy",
        },

        "inverter": {
            "icon": "🟢",
            "text": "Connected",
        },

        "scheduler": {
            "icon": "🟢",
            "text": "Running",
        },

        "notifications": {
            "icon": "🟢",
            "text": "Active",
        },
    }



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

            mainleft_inner_left, mainleft_inner_middle, mainleft_inner_right = st.columns([3, 2, 3])

            with mainleft_inner_left:
                st.write("🟢 Poller")
                st.write("🟢 Inverter")

            with mainleft_inner_middle:
                st.write("🟢 Scheduler")
                st.write("🟢 Notifications")

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
                    st.subheader("Next Action")
                    st.markdown("##### 23:30")
                    st.write("Force Charge")
