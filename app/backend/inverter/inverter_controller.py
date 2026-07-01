from app.backend.common.logging_utils import setup_logger
from app.enums.solax_enums import WorkMode, ManualMode

logger = setup_logger("Controller")


class InverterController:

    def __init__(
        self,
        service,
    ):
        self.service = service

    def get_work_mode(self):
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

    def force_charge(
        self,
    ):
        self.service.write_work_mode(
            WorkMode.MANUAL,
            ManualMode.FORCE_CHARGE,
        )

    def force_discharge(
        self,
    ):
        self.service.write_work_mode(
            WorkMode.MANUAL,
            ManualMode.FORCE_DISCHARGE,
        )

    def self_use(
        self,
    ):
        self.service.write_work_mode(
            WorkMode.SELF_USE,
            ManualMode.IDLE,
        )

    def write_work_mode(
        self,
        desired_work_mode,
        desired_manual_mode,
    ):
        """
        Write the requested inverter operating mode.

        Parameters
        ----------
        desired_work_mode
            Inverter work mode register value.

        desired_manual_mode
            Manual mode register value. Ignored by the inverter
            unless the work mode is Manual.
        """

        logger.info(
            f"Writing work_mode={desired_work_mode}, "
            f"manual_mode={desired_manual_mode}"
        )

        self.service.write_work_mode(
            desired_work_mode,
            desired_manual_mode,
        )