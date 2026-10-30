from app.config.solax_config import (
    MANUAL_MODE_WRITE_REGISTER,
    WORK_MODE_WRITE_REGISTER,
    DRY_RUN,
)
from app.logging.logger import setup_logger
from app.solax.telemetry.modbus_client import SolaxModbusClient
from pymodbus.client import ModbusTcpClient

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

        if DRY_RUN:
            logger.info(
                f"DRY RUN: would write work_mode={work_mode}, manual_mode={manual_mode}"
            )
            return

        # Use a short lived connection for the write too; the dongle has shown
        # instability with reused connections. Keep the configured mappings.
        client = ModbusTcpClient(host=self._client.host, port=self._client.port)
        if not client.connect():
            raise ConnectionError(f"Unable to connect to {self._client.host} for inverter write")
        try:
            result = client.write_register(address=WORK_MODE_WRITE_REGISTER,
                                           value=int(work_mode),
                                           device_id=self._client.slave_id)
            if result.isError():
                raise RuntimeError(f"Work-mode write rejected: {result}")
            if manual_mode is not None:
                try:
                    result = client.write_register(address=MANUAL_MODE_WRITE_REGISTER,
                                                   value=int(manual_mode),
                                                   device_id=self._client.slave_id)
                    if result.isError():
                        raise RuntimeError(f"Manual-mode write rejected: {result}")
                except Exception as exc:
                    raise RuntimeError(
                        f"Work-mode write acknowledged but manual-mode write failed: {exc}"
                    ) from exc
        finally:
            client.close()

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
