from datetime import datetime

from app.backend.automation.constants import (
    MODE_MANUAL_DISCHARGE,
    MODE_MANUAL_CHARGE,
    SELF_USE,
)
from app.backend.automation.models import AutomationState

DRY_RUN = True


class Scheduler:
    def __init__(
        self,
        repository,
        service,
    ):

        self.repository = repository

        self.service = service

        self.is_active = False

    def get_active_period(self):

        periods = [p for p in self.repository.get_periods() if p.enabled]

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

        periods = [p for p in self.repository.get_periods() if p.enabled]

        if not periods:
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

        rule = periods[0]

        if not self.is_in_window(
            rule.start_time,
            rule.end_time,
        ):
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
            mode=rule.mode,
            start_time=rule.start_time,
            end_time=rule.end_time,
            status="Waiting",
            message="Manual implementation available.",
        )

    def evaluate(
        self,
    ):

        periods = [p for p in self.repository.get_periods() if p.enabled]

        if not periods:
            return

        rule = periods[0]

        if rule is None:
            return

        if not rule.enabled:
            return

        should_run = self.is_in_window(
            rule.start_time,
            rule.end_time,
        )

        #
        # Enter window
        #

        if should_run and not self.is_active:
            print(f"ENTER WINDOW: {rule.name}")

            if DRY_RUN:
                print(f"DRY RUN: Would execute {rule.mode}")

            else:
                if rule.mode == MODE_MANUAL_DISCHARGE:
                    self.service.write_work_mode(3, 2)

                elif rule.mode == MODE_MANUAL_CHARGE:
                    self.service.write_work_mode(3, 1)

            self.is_active = True

            return

        #
        # Leave window
        #

        if not should_run and self.is_active:
            print(f"LEAVE WINDOW: {rule.name}")

            if DRY_RUN:
                print("DRY RUN: Would return to Self Use")

            else:
                pass

            self.is_active = False

            return

    def reset(
        self,
    ):
        self.is_active = False

        print("Scheduler reset")

    def is_in_window(
        self,
        start_time: str,
        end_time: str,
        current_time: str | None = None,
    ) -> bool:

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
