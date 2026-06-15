import logging

from app.backend.inverter.controller import InverterController
from app.solax.telemetry.modbus_service import SolaxModbusService

logger = logging.getLogger(__name__)

class InverterPollingService:
    def __init__(
        self,
        host="192.168.1.67",
    ):

        self.modbus_service = SolaxModbusService(
            host=host,
        )
        self.controller = InverterController(self.modbus_service)

    def poll(
        self,
    ):
        logger.info("Inside Get Snapshot")
        logger.info("Getting Work Mode")
        mode = self.controller.get_work_mode()
        logger.info("Got Work Mode")
        logger.info("Getting Poll Once")
        snapshot = self.modbus_service.read_telemetry()
        logger.info("Got Poll Once")
        snapshot.work_mode = mode
        logger.info("Leaving Get Snapshot")

        return snapshot

    def close(
        self,
    ):

        self.modbus_service.close()
