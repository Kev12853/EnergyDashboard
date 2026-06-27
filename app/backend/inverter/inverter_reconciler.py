from app.backend.common.logging_utils import setup_logger
from app.backend.inverter.inverter_controller import InverterController

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

        if requested_work_mode == 3:
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

            logger.info("Updating inverter")

            self.inverter_service.write_work_mode(
                requested_work_mode,
                requested_manual_mode,
            )
            
            return

        #
        # Requested state has been achieved.
        #

        logger.info("Requested inverter state achieved")

        #
        # If there is no restore state remaining then the
        # override lifecycle has completed.
        #

        if requested_state["restore_work_mode_to"] is None:

            logger.info(
                "Override complete - clearing inverter state"
            )

            self.inverter_state_repo.clear()

        else:

            logger.info(
                "Override active - awaiting restore request"
            )