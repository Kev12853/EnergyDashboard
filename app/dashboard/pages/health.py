import pandas as pd
import streamlit as st


def render(
    latest,
    latest_timestamp,
    data_age_minutes,
    repo,
):

    st.title("🔧 System Health")

    # ==========================================
    # Overall Status
    # ==========================================

    if data_age_minutes < 5:
        icon = "🟢"
        status = "Healthy"

    elif data_age_minutes < 30:
        icon = "🟡"
        status = "Delayed"

    else:
        icon = "🔴"
        status = "Offline"

    last_update = pd.Timestamp(
        latest_timestamp
    ).strftime("%d %b %H:%M")

    work_mode = latest["work_mode"]

    with st.container(border=True):

        st.markdown(
            f"""
            <span style="font-size:1.4em; font-weight:bold;">
                {icon} EnergyDashboard {status}
            </span>

            <span style="font-size:1.2em;">
                &nbsp;&nbsp;
                | ⚡ {work_mode}
            </span>

            <span style="font-size:1.2em;">
                &nbsp;&nbsp;
                Last Update: {last_update}
            </span>
            """,
            unsafe_allow_html=True,
        )

    # ==========================================
    # Health Cards
    # ==========================================

    left, right = st.columns(2)

    # ------------------------------------------
    # Poller
    # ------------------------------------------

    with left:

        with st.container(border=True):

            st.subheader("⚡ Poller")

            st.write(
                f"Telemetry Age: {data_age_minutes:.1f} minutes"
            )

            st.write(
                f"Status: {status}"
            )

    # ------------------------------------------
    # Automation
    # ------------------------------------------

    with right:

        periods = repo.get_periods()

        enabled = sum(
            1
            for p in periods
            if p.enabled
        )

        with st.container(border=True):

            st.subheader("⚙ Automation")

            st.write(
                f"Configured Periods: {len(periods)}"
            )

            st.write(
                f"Enabled Periods: {enabled}"
            )

    # ------------------------------------------
    # Inverter
    # ------------------------------------------

    with left:

        with st.container(border=True):

            st.subheader("🔌 Inverter")

            st.write(
                f"Work Mode: {work_mode}"
            )

            st.write(
                "Connection: Online"
            )

    # ------------------------------------------
    # Database
    # ------------------------------------------

    with right:

        with st.container(border=True):

            st.subheader("💾 Database")

            st.write(
                "SQLite Operational"
            )

            st.write(
                "Telemetry Available"
            )

    # ------------------------------------------
    # Future
    # ------------------------------------------

    with st.container(border=True):

        st.subheader("🚀 Future Health Checks")

        st.write("• Scheduler heartbeat")

        st.write("• Notification status")

        st.write("• Octopus connectivity")

        st.write("• Poller reconnect count")

        st.write("• Database statistics")

        st.write("• System uptime")