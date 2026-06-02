import streamlit as st

from datetime import (
    datetime,
    time,
)

from app.backend.automation.models import (
    AutomationRule,
)

from app.backend.automation.constants import (
    ACTION_FORCE_CHARGE,
    ACTION_FORCE_DISCHARGE,
)


def render(
    rule,
    repo,
):

    st.title(
        "Automation"
    )

    enabled = st.checkbox(
        "Enabled",
        value=rule.enabled,
    )

    name = st.text_input(
        "Rule Name",
        value=rule.name,
    )

    action = st.selectbox(
        "Action",
        [
            ACTION_FORCE_CHARGE,
            ACTION_FORCE_DISCHARGE,
        ],
        index=(
            0
            if rule.action
            == ACTION_FORCE_CHARGE
            else 1
        ),
    )

    start_time = st.time_input(
        "Start Time",
        value=datetime.strptime(
            rule.start_time,
            "%H:%M",
        ).time(),
    )

    end_time = st.time_input(
        "End Time",
        value=datetime.strptime(
            rule.end_time,
            "%H:%M",
        ).time(),
    )

    if st.button(
        "Save Rule"
    ):

        updated_rule = AutomationRule(

            id=rule.id,

            name=name,

            enabled=enabled,

            start_time=(
                start_time.strftime(
                    "%H:%M"
                )
            ),

            end_time=(
                end_time.strftime(
                    "%H:%M"
                )
            ),

            action=action,

            updated_at=datetime.now(),
        )

        repo.save_rule(
            updated_rule
        )

        st.success(
            "Rule saved"
        )