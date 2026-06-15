import logging
logger = logging.getLogger(__name__)


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
        pass
        #set workmode to manual
        self.service.write_work_mode(3, 1)
        #


    def force_discharge(
        self,
    ):
        pass
        #set workmode to manual
        self.service.write_work_mode(3, 2)




    def self_use(
        self,
    ):
        pass
        # set work mode to Self Use
        # self.service.write_work_mode(0)
