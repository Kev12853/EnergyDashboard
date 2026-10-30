"""Expose the Modbus read interface and the guarded inverter write interface. Polling methods read telemetry; write_work_mode is the only method here that can write work/manual registers and returns without a Modbus write while DRY_RUN is true."""

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
    """Provide the Modbus boundary used by polling and control, separating register reads from guarded mode writes."""
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

        """Return raw work/manual mode holding registers from the client."""
        return self._client.read_work_mode_registers()

    def read_telemetry(
        self,
    ):

        """Read a telemetry snapshot from the configured input registers."""
        return self._client.poll_once()

    def read_polling_registers(
        self,
    ):

        """Read work/manual mode plus telemetry mappings for one poll cycle."""
        return self._client.read_polling_registers()

    def build_snapshot(
        self,
        registers,
    ):

        """Convert a telemetry-register mapping into a PowerFlowSnapshot."""
        return self._client.build_snapshot(registers)

    def read_charge_schedule(
        self,
    ):

        """Read and decode the inverter charge schedule through the Modbus client."""
        return self._client.read_charge_schedule()

    def write_work_mode(
        self,
        work_mode,
        manual_mode=None,
    ):
        """Request work/manual register writes using configured write addresses; while DRY_RUN is true it only logs, otherwise it opens a short-lived connection and raises on connection or Modbus write failure."""
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

        """Always raise NotImplementedError because charge-schedule writes are not implemented."""
        raise NotImplementedError("Charge schedule writing is not implemented")

    def close(
        self,
    ):

        """Close the wrapped Modbus client and release its connection resources."""
        self._client.close()
