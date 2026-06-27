from app.backend.common.logging_utils import setup_logger

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
            return 0, 0

        if mode == "Feed In Priority":
            return 1, 0

        if mode == "Backup":
            return 2, 0

        if mode == "Manual":
            return 3, 0

        if mode == "Force Charge":
            return 3, 1

        if mode == "Force Discharge":
            return 3, 2

        raise ValueError(...)

    @staticmethod
    def decode_work_mode(
        work_mode,
        manual_mode,
    ):

        if work_mode == 0:
            return "Self Use"

        if work_mode == 1:
            return "Feed In Priority"

        if work_mode == 2:
            return "Backup"

        if work_mode == 3:

            if manual_mode == 0:
                return "Manual"

            if manual_mode == 1:
                return "Force Charge"

            if manual_mode == 2:
                return "Force Discharge"

            return f"Manual ({manual_mode})"

        if work_mode == 4:
            return "Peak Shaving"

        if work_mode == 5:
            return "TOU"

        return f"Unknown ({work_mode})"

    def force_charge(
        self,
    ):
        self.service.write_work_mode(
            3,
            1,
        )

    def force_discharge(
        self,
    ):
        self.service.write_work_mode(
            3,
            2,
        )

    def self_use(
        self,
    ):
        self.service.write_work_mode(
            0,
            0,
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