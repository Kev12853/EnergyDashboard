"""Translate between human-readable inverter modes and raw work/manual register values, and obtain the current decoded mode through a polling service. It contains no write path."""

from app.enums.solax_enums import WorkMode, ManualMode
from app.logging.logger import setup_logger

logger = setup_logger("Controller")


class InverterController:

    """Decode raw work/manual mode values and present named modes; reads through the injected service but has no write operation."""
    def __init__(
        self,
        service,
    ):
        self.service = service

    def get_work_mode(self):
        """Read work/manual holding registers and return the decoded human-readable mode; propagates communication/read failures."""
        logger.info("Inside Get Work Mode")
        logger.info("Getting Work Mode Registers")

        mode_registers = self.service.read_work_mode()

        logger.info("Got Work Mode Registers")

        work_mode = mode_registers[0x008B]
        manual_mode = mode_registers[0x008C]

        return self.decode_work_mode(
            work_mode,
            manual_mode,
        )

    @staticmethod
    def encode_work_mode(mode):

        """Map a supported display name to its (work_mode, manual_mode) register values; raises ValueError for an unknown name."""
        if mode == "Self Use":
            return WorkMode.SELF_USE, ManualMode.IDLE

        if mode == "Feed In Priority":
            return WorkMode.FEED_IN, ManualMode.IDLE

        if mode == "Backup":
            return WorkMode.BACKUP, ManualMode.IDLE

        if mode == "Manual":
            return WorkMode.MANUAL, ManualMode.IDLE

        if mode == "Force Charge":
            return WorkMode.MANUAL, ManualMode.FORCE_CHARGE

        if mode == "Force Discharge":
            return WorkMode.MANUAL, ManualMode.FORCE_DISCHARGE

        raise ValueError(...)

    @staticmethod
    def decode_work_mode(
        work_mode,
        manual_mode,
    ):

        """Map raw work/manual register values to a display name, retaining unknown values in the returned label."""
        if work_mode == WorkMode.SELF_USE:
            return "Self Use"

        if work_mode == WorkMode.FEED_IN:
            return "Feed In Priority"

        if work_mode == WorkMode.BACKUP:
            return "Backup"

        if work_mode == WorkMode.MANUAL:

            if manual_mode == ManualMode.IDLE:
                return "Manual"

            if manual_mode == ManualMode.FORCE_CHARGE:
                return "Force Charge"

            if manual_mode == ManualMode.FORCE_DISCHARGE:
                return "Force Discharge"

            return f"Manual ({manual_mode})"

        if work_mode == WorkMode.PEAK_SHAVING:
            return "Peak Shaving"

        if work_mode == WorkMode.TOU:
            return "TOU"

        return f"Unknown ({work_mode})"
