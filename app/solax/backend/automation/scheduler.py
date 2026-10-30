"""Evaluate enabled schedule windows and update the durable desired inverter request. The scheduler manages ownership and restoration, including scheduler requests underneath Smart Flex; actual writes are performed by the control service reconciler."""

from datetime import datetime


from app.solax.backend.automation.models import AutomationState
from app.solax.backend.automation.mapping import map_automation_mode
from app.enums.inverter_state_enums import InverterRequestPhase

from app.config.solax_config import (
    DRY_RUN,
)
from app.logging.logger import setup_logger

logger = setup_logger("Scheduler")


class Scheduler:
    """Evaluate enabled schedule windows and write desired-state transitions through the injected inverter-state repository; never writes Modbus directly."""
    def __init__(
        self,
        repository,
        inverter_state_repo,
    ):
        self.repository = repository
        self.inverter_state_repo = inverter_state_repo
        self.is_active = False
        self.active_schedule_id = None

    def get_active_period(self):

        """Return the highest-priority enabled period if its window is currently active, otherwise None."""
        periods = [p for p in self.repository.get_periods() if p.enabled]

        logger.info(f"is_active = {self.is_active}")

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

        """Return an AutomationState describing whether the selected schedule is currently in its time window."""
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

        The poller_status_card later compares:

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
            happen. The poller_status_card is responsible for ensuring it does
            happen.
        """

        # Get all the Active periods
        periods = [p for p in self.repository.get_periods() if p.enabled]

        #
        # No enabled schedules.
        #

        if not periods:
            logger.info("There are no currently enabled schedules")
            logger.info(f"Scheduler is_active = {self.is_active}")

            pending = self.inverter_state_repo.get()

            logger.info(f"Pending state = {pending}")

            if pending is not None:
                logger.info(
                    f"phase={pending.get('phase', '<missing>')}, "
                    f"requested={pending['requested_work_mode']}, "
                    f"restore={pending['restore_work_mode_to']}, "
                    f"active={pending['active']}"
                )

                if (
                    pending["phase"] == InverterRequestPhase.OVERRIDE
                    and pending["source"] == "scheduler"
                ):
                    logger.info("Requesting restore")
                    self.inverter_state_repo.request_restore()

                elif pending["phase"] == InverterRequestPhase.OVERRIDE:
                    if pending["source"] == "smart_flex":
                        logger.info(
                            "Override belongs to smart_flex - "
                            "clearing scheduler underlying request"
                        )
                        self.inverter_state_repo.clear_underlying()
                    else:
                        logger.info(
                            f"Override belongs to {pending['source']} - "
                            "scheduler will not restore it"
                        )

                elif pending["phase"] == InverterRequestPhase.RESTORE:
                    logger.info("Restore already in progress")

                elif pending["phase"] == InverterRequestPhase.IDLE:
                    logger.info("Nothing to do")

                # restore_pending = pending["restore_work_mode_to"] is not None
                #
                # logger.info(f"restore_pending = {restore_pending}")

                # if restore_pending:
                #     logger.info("Restoring previous operating mode")
                #     self.inverter_state_repo.start_restore()
                # else:
                #     logger.info("Cancelling current override, it was never started")
                #     self.inverter_state_repo.clear()

            self.is_active = False
            return

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

        # Recover in-memory schedule ownership after a control-process restart.
        # The durable inverter_state request already carries the schedule's
        # restore target; re-entering would incorrectly replace it with the
        # inverter's temporary current mode.
        if should_run and not self.is_active:
            pending = self.inverter_state_repo.get()
            if pending is not None and pending.get("source") == "scheduler":
                if pending.get("phase") == InverterRequestPhase.RESTORE:
                    # A restoration already requested before a process restart
                    # must reach telemetry confirmation before a still-active
                    # schedule can be re-entered.
                    return
                requested_mode = map_automation_mode(rule.mode)
                if (pending["requested_work_mode"], pending["requested_manual_mode"]) != requested_mode:
                    self.inverter_state_repo.set(
                        requested_work_mode=requested_mode[0],
                        requested_manual_mode=requested_mode[1],
                        restore_work_mode_to=pending["restore_work_mode_to"],
                        restore_manual_mode_to=pending["restore_manual_mode_to"],
                        underlying_work_mode=pending["underlying_work_mode"],
                        underlying_manual_mode=pending["underlying_manual_mode"],
                        phase=InverterRequestPhase.OVERRIDE,
                        active=True,
                        source="scheduler",
                    )
                self.is_active = True
                self.active_schedule_id = rule.id
                logger.info("Recovered active schedule %s from inverter_state", rule.id)
                return

        #
        # Has the active schedule changed?
        #

        if should_run and self.is_active and self.active_schedule_id != rule.id:
            logger.info(f"Switching schedule {self.active_schedule_id} -> {rule.id}")

            requested_work_mode, requested_manual_mode = map_automation_mode(rule.mode)

            #
            # Update the request, but preserve the original restore values.
            #

            pending = self.inverter_state_repo.get()

            if pending["source"] == "smart_flex":
                self.inverter_state_repo.set_underlying(
                    requested_work_mode,
                    requested_manual_mode,
                )
            else:
                self.inverter_state_repo.set(
                    requested_work_mode=requested_work_mode,
                    requested_manual_mode=requested_manual_mode,
                    restore_work_mode_to=pending["restore_work_mode_to"],
                    restore_manual_mode_to=pending["restore_manual_mode_to"],
                    underlying_work_mode=pending["underlying_work_mode"],
                    underlying_manual_mode=pending["underlying_manual_mode"],
                    phase=InverterRequestPhase.OVERRIDE,
                    active=True,
                    source="scheduler",
                )

            self.active_schedule_id = rule.id

            return
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

                requested_work_mode, requested_manual_mode = map_automation_mode(rule.mode)

                #
                # Remember the current operating mode so it can be
                # restored when the schedule finishes.
                #
                # create inverter_state request

                pending = self.inverter_state_repo.get()

                if pending is not None and pending["source"] == "smart_flex":
                    self.inverter_state_repo.set_underlying(
                        requested_work_mode,
                        requested_manual_mode,
                    )
                else:
                    self.inverter_state_repo.set(
                        requested_work_mode=requested_work_mode,
                        requested_manual_mode=requested_manual_mode,
                        restore_work_mode_to=snapshot.work_mode,
                        restore_manual_mode_to=snapshot.manual_mode,
                        underlying_work_mode=None,
                        underlying_manual_mode=None,
                        phase=InverterRequestPhase.OVERRIDE,
                        active=True,
                        source="scheduler",
                    )

                self.is_active = True
                self.active_schedule_id = rule.id
                return

        #
        # Leave window
        #

        if not should_run and self.is_active:
            print(f"LEAVE WINDOW: {rule.name}")

            if DRY_RUN:
                print("DRY RUN: Restoring previous operating mode")

            pending = self.inverter_state_repo.get()

            if pending is not None and pending["source"] == "smart_flex":
                self.inverter_state_repo.clear_underlying()
            else:
                self.inverter_state_repo.request_restore()

            self.is_active = False
            self.active_schedule_id = None

            return

    def reset(
        self,
    ):
        """Clear only this Scheduler instance’s in-memory active flag; it does not alter the durable inverter request."""
        self.is_active = False

        print("Scheduler reset")

    def is_in_window(
        self,
        start_time: str,
        end_time: str,
        current_time: str | None = None,
    ) -> bool:

        """Test a local HH:MM time against a half-open interval, including a window that wraps past midnight."""
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
