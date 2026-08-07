from app.backend.common.logging_utils import setup_logger
from app.config.solax_config import MANUAL_MODE_WRITE_REGISTER, WORK_MODE_WRITE_REGISTER
from app.solax.telemetry.modbus_client import SolaxModbusClient

logger = setup_logger("ModBus Service")


class SolaxModbusService:
    def __init__(
        self,
        host: str,
        port: int = 502,
        slave_id: int = 1,
    ):

        self._client = SolaxModbusClient(
            host=host,
            port=port,
            slave_id=slave_id,
        )

    def read_work_mode(
        self,
    ):

        return self._client.read_work_mode_registers()

    def read_telemetry(
        self,
    ):

        return self._client.poll_once()

    def read_polling_registers(
        self,
    ):

        return self._client.read_polling_registers()

    def build_snapshot(
        self,
        registers,
    ):

        return self._client.build_snapshot(registers)

    def read_charge_schedule(
        self,
    ):

        return self._client.read_charge_schedule()

    def write_work_mode(
        self,
        work_mode,
        manual_mode=None,
    ):

        logger.info(f"Writing work_mode={work_mode}, manual_mode={manual_mode}")
        # ===========================
        x = 1
        if x == 0:
            logger.info("*** TEST: Simulating failed write ***")
            return
        # ==================================

        self._client.client.write_register(
            address=WORK_MODE_WRITE_REGISTER,
            value=work_mode,
            device_id=self._client.slave_id,
        )

        if manual_mode is None:
            return

        self._client.client.write_register(
            address=MANUAL_MODE_WRITE_REGISTER,
            value=manual_mode,
            device_id=self._client.slave_id,
        )

    def write_charge_schedule(
        self,
        *args,
        **kwargs,
    ):

        raise NotImplementedError("Charge schedule writing is not implemented")

    def close(
        self,
    ):

        self._client.close()
