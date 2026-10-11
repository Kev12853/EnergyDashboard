from app.enums.inverter_state_enums import InverterRequestPhase
from app.enums.solax_enums import WorkMode, ManualMode
from app.logging.logger import setup_logger


logger = setup_logger("Smart Flex Orchestrator")


class SmartFlexOrchestrator:
    def __init__(self, inverter_state_repo):
        self.inverter_state_repo = inverter_state_repo

    def is_active(self):
        state = self.inverter_state_repo.get()

        if state is None:
            return False

        return state["source"] == "smart_flex" and state["phase"] == "OVERRIDE"

    def start(self, snapshot):
        state = self.inverter_state_repo.get()

        if state is None:
            logger.info(
                "Smart Flex: no existing inverter state - creating Smart Flex override"
            )

            self.inverter_state_repo.set(
                requested_work_mode=WorkMode.MANUAL,
                requested_manual_mode=ManualMode.FORCE_CHARGE,
                restore_work_mode_to=snapshot.work_mode,
                restore_manual_mode_to=snapshot.manual_mode,
                underlying_work_mode=None,
                underlying_manual_mode=None,
                phase=InverterRequestPhase.OVERRIDE,
                active=True,
                source="smart_flex",
            )

            logger.info("Smart Flex: Force Charge override activated")
            return

        self.inverter_state_repo.set(
            requested_work_mode=WorkMode.MANUAL,
            requested_manual_mode=ManualMode.FORCE_CHARGE,
            restore_work_mode_to=state["restore_work_mode_to"],
            restore_manual_mode_to=state["restore_manual_mode_to"],
            underlying_work_mode=state["requested_work_mode"],
            underlying_manual_mode=state["requested_manual_mode"],
            phase=InverterRequestPhase.OVERRIDE,
            active=True,
            source="smart_flex",
        )

        logger.info("Smart Flex: Force Charge override activated")
        
    def stop(self):
        state = self.inverter_state_repo.get()

        if state is None:
            logger.info("Smart Flex: no active state to stop")
            return

        if state["source"] != "smart_flex":
            logger.info(
                f"Smart Flex: current owner is {state['source']}, "
                "nothing to stop"
            )
            return

        if state["underlying_work_mode"] is not None:
            logger.info(
                "Smart Flex: stopping - activating underlying scheduler request"
            )
            self.inverter_state_repo.activate_underlying()
            return

        logger.info("Smart Flex: stopping - requesting restore")
        self.inverter_state_repo.request_restore()

    def apply_decision(self, decision, snapshot):
        if decision == "FORCE_CHARGE":
            if not self.is_active():
                logger.info("Smart Flex: decision is FORCE_CHARGE - starting")
                self.start(snapshot)
            else:
                logger.info("Smart Flex: Force Charge already active")

        elif decision == "NORMAL":
            if self.is_active():
                logger.info("Smart Flex: decision is NORMAL - stopping")
                self.stop()
            else:
                logger.info("Smart Flex: already inactive")
    