from app.enums.solax_enums import WorkMode
from app.logging.logger import setup_logger
import time

logger = setup_logger("Inverter Reconciler")


class InverterReconciler:
    """
    Compare the requested inverter state with the actual
    inverter state and determine whether an inverter
    update is required.

    Requested State
        inverter_state table

    Actual State
        PowerFlowSnapshot

    The reconciler is responsible for:

        - Comparing requested and actual state
        - Determining whether action is required
        - Updating the inverter
        - Verifying the change
        - Clearing completed requests

    It does not:

        - Poll the inverter
        - Evaluate schedules
        - Save snapshots
    """

    def __init__(
        self,
        inverter_state_repo,
        inverter_service,
    ):
        self.inverter_state_repo = inverter_state_repo
        self.inverter_service = inverter_service
        self._last_attempt = {}
        self._retry_after_seconds = 60

    def process(
        self,
        snapshot,
    ):
        """
        Reconcile the requested inverter state with the
        actual inverter state.

        If the inverter does not match the requested state,
        request the controller to update it.

        Once the requested state has been achieved, determine
        whether the override has completed and clear the
        request if appropriate.
        """

        requested_state = self.inverter_state_repo.get()

        if not requested_state:
            logger.info("No requested inverter state")
            return

        requested_work_mode = requested_state["requested_work_mode"]
        requested_manual_mode = requested_state["requested_manual_mode"]

        actual_work_mode = snapshot.work_mode
        actual_manual_mode = snapshot.manual_mode

        logger.info(
            f"Requested state : "
            f"work_mode={requested_work_mode}, "
            f"manual_mode={requested_manual_mode}"
        )

        logger.info(
            f"Actual state    : "
            f"work_mode={actual_work_mode}, "
            f"manual_mode={actual_manual_mode}"
        )

        #
        # Determine whether the inverter requires updating.
        #

        if requested_work_mode == WorkMode.MANUAL:
            #
            # Manual work mode.
            #
            action_required = (
                requested_work_mode != actual_work_mode
                or requested_manual_mode != actual_manual_mode
            )

        else:
            #
            # Manual mode ignored.
            #
            action_required = (
                requested_work_mode != actual_work_mode
            )

        logger.info(
            f"Action required: {'YES' if action_required else 'NO'}"
        )

        #
        # Update the inverter if required.
        #

        if action_required:

            request_key = (
                requested_work_mode,
                requested_manual_mode,
                requested_state.get("source"),
                requested_state.get("phase"),
                requested_state.get("updated_at"),
            )
            now = time.monotonic()
            if now - self._last_attempt.get(request_key, float("-inf")) < self._retry_after_seconds:
                logger.warning("Control write retry suppressed by 60 second backoff")
                return

            logger.info("Updating inverter")
            # A scheduler/Smart Flex update may have arrived after the first
            # read. Never issue a command for a superseded request.
            current_state = self.inverter_state_repo.get()
            if current_state is None or any(
                current_state.get(key) != requested_state.get(key)
                for key in (
                    "requested_work_mode", "requested_manual_mode", "source", "phase",
                    "active", "restore_work_mode_to", "restore_manual_mode_to",
                    "underlying_work_mode", "underlying_manual_mode", "updated_at",
                )
            ):
                logger.info("Request changed during reconciliation; deferring to next fresh poll")
                return
            self._last_attempt[request_key] = now
            try:
                self.inverter_service.write_work_mode(
                    requested_work_mode,
                    requested_manual_mode,
                )
            except Exception:
                logger.exception("Inverter command failed; request retained for controlled retry")
                raise
            
            return

        #
        # Requested state has been achieved.
        #

        logger.info("Requested inverter state achieved")

        #
        # If there is no restore state remaining then the
        # override lifecycle has completed.
        #

        if (
            requested_state["restore_work_mode_to"] is None
        ):
            logger.info("Override complete - clearing inverter state")
            clear_if_current = getattr(self.inverter_state_repo, "clear_if_current", None)
            if clear_if_current:
                clear_if_current(requested_state)
            else:
                self.inverter_state_repo.clear()

        else:

            logger.info(
                "Override active - awaiting restore request"
            )
