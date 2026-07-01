from datetime import datetime

from app.backend.common.logging_utils import setup_logger

from app.backend.automation.models import AutomationState

from app.config.solax_config import (
    DRY_RUN,
    SCHEDULER_MODE_MANUAL_CHARGE,
    WORK_MODE_MANUAL,
    MANUAL_MODE_FORCE_CHARGE,
    MANUAL_MODE_FORCE_DISCHARGE,
    SCHEDULER_MODE_SELF_USE,
    WORK_MODE_SELF_USE,
    MANUAL_MODE_IDLE,
    WORK_MODE_PEAK_SHAVING,
    SCHEDULER_MODE_PEAK_SHAVING,
    SCHEDULER_MODE_FEED_IN,
    WORK_MODE_FEED_IN,
    SCHEDULER_MODE_BACKUP,
    WORK_MODE_BACKUP,
    SCHEDULER_MODE_MANUAL_DISCHARGE,
)

logger = setup_logger("Scheduler")


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
            # There are currently no enabled schedules
            logger.info(f"There are no currently enabled schedules")

            pending = self.inverter_state_repo.get()

            if pending is not None:
                #
                # If a restore state exists then the inverter has
                # already entered a temporary override. Replace the
                # outstanding request with a request to restore the
                # previous operating mode.
                #

                restore_pending = pending["restore_work_mode_to"] is not None
                # Is this a temporary override, ie pending["restore_work_mode_to"] is Not None

                if restore_pending:
                    logger.info(f"Restoring prvious operating mode")
                    self.inverter_state_repo.request_restore()

                #
                # Otherwise the outstanding request has never been
                # applied, so simply cancel it.
                else:
                    logger.info(f"Cancelling current override, it was never started")
                    self.inverter_state_repo.clear()

            # Run this code in either  True or False  for Pending is not None

            # Set Flag for next time
            self.is_active = False
            # Exit Scheduler
            return

        # If there are active periods get the first one in the list. This will be the period with the highest priority
        rule = periods[0]

        if rule is None:
            return

        if not rule.enabled:
            return

        #Should this schedule currently be active?
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

            logger.info(f"Entering Window for {rule.name}")

            if not DRY_RUN:
                print(f"DRY RUN: Requesting {rule.mode}")

            if should_run and not self.is_active:
                #
                # Determine the requested operating mode.
                #

                if rule.mode == SCHEDULER_MODE_MANUAL_CHARGE:
                    requested_work_mode = WORK_MODE_MANUAL
                    requested_manual_mode = MANUAL_MODE_FORCE_CHARGE

                elif rule.mode == SCHEDULER_MODE_MANUAL_DISCHARGE:
                    requested_work_mode = WORK_MODE_MANUAL
                    requested_manual_mode = MANUAL_MODE_FORCE_DISCHARGE

                elif rule.mode == SCHEDULER_MODE_SELF_USE:
                    requested_work_mode = WORK_MODE_SELF_USE
                    requested_manual_mode = MANUAL_MODE_IDLE

                elif rule.mode == SCHEDULER_MODE_PEAK_SHAVING:
                    requested_work_mode = WORK_MODE_PEAK_SHAVING
                    requested_manual_mode = MANUAL_MODE_IDLE

                elif rule.mode == SCHEDULER_MODE_FEED_IN:
                    requested_work_mode = WORK_MODE_FEED_IN
                    requested_manual_mode = MANUAL_MODE_IDLE

                elif rule.mode == SCHEDULER_MODE_BACKUP:
                    requested_work_mode = WORK_MODE_BACKUP
                    requested_manual_mode = MANUAL_MODE_IDLE

                else:
                    raise ValueError(f"Unknown schedule mode: {rule.mode}")

                #
                # Remember the current operating mode so it can be
                # restored when the schedule finishes.
                #
                # create inverter_state request
                from app.enums.inverter_state_enums import InverterRequestPhase

                self.inverter_state_repo.set(
                    requested_work_mode=requested_work_mode,
                    requested_manual_mode=requested_manual_mode,
                    restore_work_mode_to=snapshot.work_mode,
                    restore_manual_mode_to=snapshot.manual_mode,
                    phase=InverterRequestPhase.OVERRIDE,
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
