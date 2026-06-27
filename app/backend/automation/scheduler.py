from datetime import datetime

from app.backend.automation.constants import MODE_MANUAL_CHARGE, MODE_MANUAL_DISCHARGE
from app.backend.automation.models import AutomationState

WORK_MODE_SELF_USE = 0
WORK_MODE_FEED_IN = 1
WORK_MODE_BACKUP = 2
WORK_MODE_MANUAL = 3
WORK_MODE_PEAK_SHAVING = 4

MANUAL_MODE_IDLE = 0
MANUAL_MODE_FORCE_CHARGE = 1
MANUAL_MODE_FORCE_DISCHARGE = 2

MODE_SELF_USE=0
MODE_FEED_IN = 1
MODE_BACKUP = 2
MODE_MANUAL = 3
MODE_PEAK_SHAVING = "PEAK_SHAVING"

DRY_RUN = True


class Scheduler:
    def __init__(
        self,
        repository,
        inverter_state_repo,
    ):

        self.repository = repository

        self.inverter_state_repo = inverter_state_repo

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
        snapshot,
        current_time=None,
    ):
        """
        Evaluate all enabled schedules and determine the inverter
        state that should currently be active.

        The scheduler does not communicate directly with the inverter.
        Instead it determines the DESIRED inverter state based on the
        configured schedules and writes that state to the inverter_state
        table.

        The inverter_state table represents:

            "What state should the inverter be in right now?"

        It does NOT represent:

            "What state is the inverter actually in right now?"

        The actual inverter state is obtained separately by polling
        the inverter and creating a snapshot.

        The poller later compares:

            Desired State (inverter_state)

        against:

            Actual State (snapshot)

        and decides whether any action is required.

        State transitions handled by the scheduler:

            Outside Window -> Inside Window
                Create inverter request.

            Inside Window -> Outside Window
                Request return to Self Use.

        Notes:

            The scheduler is responsible for deciding what should
            happen. The poller is responsible for ensuring it does
            happen.
        """

        # Get all the Active periods
        periods = [p for p in self.repository.get_periods() if p.enabled]

        #
        # No enabled schedules.
        #

        if not periods:
            #
            # Has a scheduler request already been made?
            #

            #
            # Has the scheduler already created an outstanding
            # inverter request?
            #

            pending = self.inverter_state_repo.get()

            if pending is not None:

                #
                # If a restore state exists then the inverter has
                # already entered a temporary override. Replace the
                # outstanding request with a request to restore the
                # previous operating mode.
                #

                override_started = (
                    pending["restore_work_mode_to"] is not None
                )

                if override_started:

                    print("RESTORING PREVIOUS OPERATING MODE")

                    self.inverter_state_repo.request_restore()

                #
                # Otherwise the outstanding request has never been
                # applied, so simply cancel it.
                #

                else:

                    print("CANCELLING OUTSTANDING REQUEST")

                    self.inverter_state_repo.clear()

            self.is_active = False

            return

        # If there are active periods get the first one in the list. This will be the period with the highest priority
        rule = periods[0]

        if rule is None:
            return

        if not rule.enabled:
            return

        should_run = self.is_in_window(
            rule.start_time,
            rule.end_time,
            current_time,
        )

        #
        # Enter window
        #

        if (
            should_run and not self.is_active
        ):  # schedule is in time window and is an active schedule
            print(f"ENTER WINDOW: {rule.name}")

            if DRY_RUN:
                print(f"DRY RUN: Requesting {rule.mode}")

            if should_run and not self.is_active:
                #
                # Determine the requested operating mode.
                #

                if rule.mode == MODE_MANUAL_CHARGE:
                    requested_work_mode = WORK_MODE_MANUAL
                    requested_manual_mode = MANUAL_MODE_FORCE_CHARGE

                elif rule.mode == MODE_MANUAL_DISCHARGE:
                    requested_work_mode = WORK_MODE_MANUAL
                    requested_manual_mode = MANUAL_MODE_FORCE_DISCHARGE

                elif rule.mode == MODE_SELF_USE:
                    requested_work_mode = WORK_MODE_SELF_USE
                    requested_manual_mode = MANUAL_MODE_IDLE

                elif rule.mode == MODE_PEAK_SHAVING:
                    requested_work_mode = WORK_MODE_PEAK_SHAVING
                    requested_manual_mode = MANUAL_MODE_IDLE

                elif rule.mode == MODE_FEED_IN:
                    requested_work_mode = WORK_MODE_FEED_IN
                    requested_manual_mode = MANUAL_MODE_IDLE

                elif rule.mode == MODE_BACKUP:
                    requested_work_mode = WORK_MODE_BACKUP
                    requested_manual_mode = MANUAL_MODE_IDLE

                else:
                    raise ValueError(f"Unknown schedule mode: {rule.mode}")

                #
                # Remember the current operating mode so it can be
                # restored when the schedule finishes.
                #

                self.inverter_state_repo.set(
                    requested_work_mode=requested_work_mode,
                    requested_manual_mode=requested_manual_mode,
                    restore_work_mode_to=snapshot.work_mode,
                    restore_manual_mode_to=snapshot.manual_mode,
                    active=True,
                    source="scheduler",
                )

                self.is_active = True
                return

        #
        # Leave window
        #

        if not should_run and self.is_active:
            print(f"LEAVE WINDOW: {rule.name}")

            if DRY_RUN:
                print("DRY RUN: Restoring previous operating mode")

            self.inverter_state_repo.request_restore()

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
