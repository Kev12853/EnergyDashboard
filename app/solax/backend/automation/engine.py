"""Legacy scheduling facade that evaluates automation periods using ScheduleRepository and inverter state. It expresses desired state and does not write to the inverter."""

from app.solax.backend.automation.models import (
    AutomationState,
)


class AutomationEngine:
    """Legacy read-only schedule evaluator backed by a repository; it reports periods and window state without changing durable inverter requests."""
    def __init__(
        self,
        repository,
    ):

        self.repository = repository

    def get_active_period(self):

        """Return the first enabled period if its time window contains the current local time, otherwise None."""
        periods = [
            p
            for p in self.repository.get_periods()
            if p.enabled
        ]

        if not periods:
            return None

        rule = periods[0]

        if not self.is_in_window(
            rule.start_time,
            rule.end_time,
        ):
            return None

        return rule

    def get_state(self) -> AutomationState:

        """Build an AutomationState for the currently active period, or an idle state when no period is active."""
        rule = self.get_active_period()

        if rule is None:
            return AutomationState(
                active=False,
                actioned=False,
                period_name=None,
                mode=None,
                start_time=None,
                end_time=None,
                status="Idle",
                message="No active automation periods.",
            )

        return AutomationState(
            active=True,
            actioned=False,
            period_name=rule.name,
            mode=str(rule.mode),
            start_time=rule.start_time,
            end_time=rule.end_time,
            status="Waiting",
            message="Manual implementation available.",
        )

    def is_in_window(
        self,
        start_time: str,
        end_time: str,
        current_time: str | None = None,
    ) -> bool:

        """Check whether a local HH:MM time falls in a half-open schedule interval; supports intervals that cross midnight."""
        from datetime import datetime

        if current_time:
            now = datetime.strptime(
                current_time,
                "%H:%M",
            ).time()

        else:
            now = datetime.now().time()

        start = datetime.strptime(
            start_time,
            "%H:%M",
        ).time()

        end = datetime.strptime(
            end_time,
            "%H:%M",
        ).time()

        if start <= end:
            return start <= now < end

        return now >= start or now < end