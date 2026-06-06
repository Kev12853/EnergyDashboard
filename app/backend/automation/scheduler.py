from datetime import datetime

from app.backend.automation.constants import (
    MODE_MANUAL_DISCHARGE,
    MODE_MANUAL_CHARGE,
    SELF_USE,
)

DRY_RUN = True


class Scheduler:
    def __init__(
        self,
        repository,
        controller,
    ):

        self.repository = repository

        self.controller = controller

        self.is_active = False

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
                print(f"DRY RUN: Would execute {rule.action}")

            else:
                if rule.action == MODE_MANUAL_DISCHARGE:
                    self.controller.force_discharge()

                elif rule.action == MODE_MANUAL_CHARGE:
                    self.controller.force_charge()

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
                self.controller.self_use()

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
