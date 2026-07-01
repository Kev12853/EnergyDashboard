from datetime import (
    datetime,
    time,
)

import streamlit as st



from app.backend.automation.models import (
    SchedulePeriod,
)
from app.config.solax_config import (
    SCHEDULER_MODE_SELF_USE,
    SCHEDULER_MODE_MANUAL_CHARGE,
    SCHEDULER_MODE_MANUAL_DISCHARGE,
    SCHEDULER_MODE_PEAK_SHAVING,
    SCHEDULER_MODE_FEED_IN,
)

# from app.dashboard_app import repository

st.markdown(
    """
<style>

.period-card {
    background-color: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 0.75rem;
}

.period-card-selected {
    background-color: rgba(74,125,255,0.15);
    border: 2px solid #4a7dff;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 0.75rem;
}

.period-title {
    font-size: 1.05rem;
    font-weight: 600;
}

.period-meta {
    color: #999;
    font-size: 0.9rem;
}

</style>
""",
    unsafe_allow_html=True,
)


def render(
    repo,
):
    # ==========================================
    # Load periods
    # ==========================================

    if "selected_period_id" not in st.session_state:
        st.session_state.selected_period_id = None

    if "new_period" not in st.session_state:
        st.session_state.new_period = False

    periods = repo.get_periods()

    selected_id = st.session_state.get("selected_period_id")

    selected_period = None

    if selected_id is not None:
        selected_period = repo.get_period(selected_id)

    if st.session_state.get(
        "new_period",
        False,
    ):
        selected_period = SchedulePeriod(
            id=None,
            name="New Period",
            source="MANUAL",
            enabled=True,
            start_time="00:00",
            end_time="01:00",
            mode=SCHEDULER_MODE_SELF_USE,
            priority=10,
            updated_at=datetime.now(),
        )

    elif selected_period is None and periods:
        selected_period = periods[0]

    if selected_period is None:
        st.info("No periods configured.")

        return

    # ========================================
    # Title
    # ======================================
    st.title("Automation")

    list_col, editor_col = st.columns([1, 2])

    with list_col:
        # ==========================================
        # Configured Periods
        # ==========================================

        st.subheader("Configured Periods")

        if st.button(
            "➕ New Period",
            use_container_width=True,
        ):
            st.session_state.selected_period_id = None
            st.session_state.new_period = True
            st.rerun()

        for period in periods:
            selected = st.session_state.get("selected_period_id") == period.id
            with st.container(border=True):
                # if selected:
                #     st.success("✏️ Currently Editing")
                if selected:
                    st.info("✏️ Editing")

                st.markdown(f"### {period.name}")

                st.write(period.mode.replace("_", " ").title())

                st.write(f"Priority: {period.priority}")

                st.write(f"{period.start_time} → {period.end_time}")

            col1, col2 = st.columns(2)

            with col1:
                if st.button(
                    "Edit",
                    key=f"edit_{period.id}",
                    use_container_width=True,
                ):
                    st.session_state.selected_period_id = period.id
                    st.session_state.new_period = False
                    st.rerun()

            with col2:
                if st.button(
                    "Delete",
                    key=f"delete_{period.id}",
                    use_container_width=True,
                ):
                    repo.delete_period(period.id)
                    st.rerun()

            st.markdown(
                "</div>",
                unsafe_allow_html=True,
            )

    # ==================================================
    # Editor
    # ==================================================
    with editor_col:
        st.subheader("Editor")

        with st.container(border=True):
            if st.session_state.get(
                "new_period",
                False,
            ):
                st.subheader("➕ New Period")
            else:
                st.subheader(f"✏️ Editing: {selected_period.name}")

            name = st.text_input(
                "Period Name",
                value=selected_period.name,
            )

            st.divider()

            MODE_OPTIONS = {
                "Self Use": SCHEDULER_MODE_SELF_USE,
                "Force Charging": SCHEDULER_MODE_MANUAL_CHARGE,
                "Force Discharging": SCHEDULER_MODE_MANUAL_DISCHARGE,
                "Peak Shaving": SCHEDULER_MODE_PEAK_SHAVING,
                "Feed In Priority": SCHEDULER_MODE_FEED_IN,
            }

            mode_col, priority_col, gap, enabled_col = st.columns([2, 1, 0.5, 3])

            with mode_col:
                display_mode = st.selectbox(
                    "Mode",
                    options=list(MODE_OPTIONS.keys()),
                    index=list(MODE_OPTIONS.values()).index(selected_period.mode),
                )

                mode = MODE_OPTIONS[display_mode]

            with priority_col:
                priority = st.number_input(
                    "Priority",
                    min_value=1,
                    max_value=100,
                    value=selected_period.priority,
                )

            with enabled_col:
                enabled = st.checkbox(
                    "Enabled",
                    value=selected_period.enabled,
                )

            st.divider()

            start_col, end_col, gap = st.columns([1, 1, 1])

            with start_col:
                start_time = st.time_input(
                    "Start Time",
                    value=datetime.strptime(
                        selected_period.start_time,
                        "%H:%M",
                    ).time(),
                )

            with end_col:
                end_time = st.time_input(
                    "End Time",
                    value=datetime.strptime(
                        selected_period.end_time,
                        "%H:%M",
                    ).time(),
                )

            st.divider()

            # ==================================================
            # Action Buttons
            # ==================================================

            save_col, new_col, spacer_col = st.columns([1, 1.5, 3])

            with save_col:
                save_clicked = st.button(
                    "Save",
                    key="save_period",
                )

    # ==================================================
    # Build Updated Period
    # ==================================================

    updated_period = SchedulePeriod(
        id=selected_period.id,
        name=name,
        source=selected_period.source,
        enabled=enabled,
        start_time=start_time.strftime("%H:%M"),
        end_time=end_time.strftime("%H:%M"),
        mode=mode,
        priority=priority,
        updated_at=datetime.now(),
    )

    # ==================================================
    # Save Existing / New Period
    # ==================================================

    if save_clicked:
        try:
            repo.save_period(updated_period)

            st.session_state.new_period = False

            if updated_period.id is not None:
                st.session_state.selected_period_id = updated_period.id

            st.success(f"Saved '{updated_period.name}'")

            st.rerun()

        except Exception as ex:
            st.error(f"Save failed: {ex}")
