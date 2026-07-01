# telemetry/modbus_client.py

import time

from datetime import datetime
from zoneinfo import ZoneInfo

from pymodbus.client import ModbusTcpClient

from app.backend.common.logging_utils import setup_logger

from app.config.solax_config import (
    INVERTER_POWER,
    PV1_POWER,
    PV2_POWER,
    BATTERY_POWER,
    BATTERY_SOC,
    GRID_MSB,
    GRID_LSB,
    REGISTER_BLOCK_START,
    REGISTER_BLOCK_SIZE,
    WORK_MODE_REGISTER,
    MANUAL_MODE_REGISTER,
)

from app.solax.analytics.decoders import parse_schedule
from app.solax.telemetry.models import (
    PowerFlowSnapshot,
)

logger = setup_logger("ModbusClient")

class SolaxModbusClient:
    def __init__(
        self,
        host: str,
        port: int = 502,
        slave_id: int = 1,
    ):

        self.host = host
        self.port = port
        self.slave_id = slave_id

        self.client = ModbusTcpClient(
            host=self.host,
            port=self.port,
        )
        logger.info("Creating persistent Modbus client")

        #if not self.client.connect():
            #raise ConnectionError(f"Unable to connect to {host}")
        logger.info("Persistent Modbus client connected")

    @staticmethod
    def signed16(value: int) -> int:

        if value > 32767:
            return value - 65536

        return value

    @staticmethod
    def signed32(msb: int, lsb: int) -> int:

        unsigned32 = (msb * 65536) + lsb

        if unsigned32 > 2147483647:
            return unsigned32 - 4294967296

        return unsigned32

    def read_register_block(
        self,
    ) -> dict[int, int]:

        max_attempts = 3

        last_exception = None

        for attempt in range(max_attempts):
            client = ModbusTcpClient(
                host=self.host,
                port=self.port,
            )

            try:
                connected = client.connect()

                if not connected:
                    raise RuntimeError(f"Unable to connect to {self.host}")

                result = client.read_input_registers(
                    address=REGISTER_BLOCK_START,
                    count=REGISTER_BLOCK_SIZE,
                    device_id=self.slave_id,
                )

                if result.isError():
                    raise RuntimeError(f"Modbus read failed: {result}")

                return {
                    REGISTER_BLOCK_START + index: value
                    for (
                        index,
                        value,
                    ) in enumerate(result.registers)
                }

            except Exception as exc:
                last_exception = exc

                logger.warning(
                    f"Register block read failed ({attempt + 1}/{max_attempts}): {exc}"
                )

                time.sleep(5.0)

            finally:
                try:
                    client.close()
                except Exception:
                    pass

        raise RuntimeError(
            f"Unable to read Modbus registers after multiple attempts: {last_exception}"
        )

    def read_register_block_from_connection(
        self,
        client,
    ) -> dict[int, int]:

        result = client.read_input_registers(
            address=REGISTER_BLOCK_START,
            count=REGISTER_BLOCK_SIZE,
            device_id=self.slave_id,
        )

        if result.isError():
            raise RuntimeError(f"Modbus read failed: {result}")

        return {
            REGISTER_BLOCK_START + index: value
            for (
                index,
                value,
            ) in enumerate(result.registers)
        }

    def poll_once(self) -> PowerFlowSnapshot:

        registers = self.read_register_block()
        logger.info("B1 register block OK")

        return self.build_snapshot(registers)

    def build_snapshot(
        self,
        registers,
    ) -> PowerFlowSnapshot:

        ac_power_w = self.signed16(registers[INVERTER_POWER])

        pv1_power_w = registers[PV1_POWER]

        pv2_power_w = registers[PV2_POWER]

        pv_power_w = pv1_power_w + pv2_power_w

        battery_power_w = self.signed16(registers[BATTERY_POWER])

        battery_soc_pct = registers[BATTERY_SOC]

        grid_power_w = self.signed32(
            msb=registers[GRID_MSB],
            lsb=registers[GRID_LSB],
        )

        consumption_power_w = ac_power_w - grid_power_w

        return PowerFlowSnapshot(
            timestamp=datetime.now(ZoneInfo("Europe/London")),
            # =============================================
            # SOLAR
            # =============================================
            pv_power_w=pv_power_w,
            pv1_power_w=pv1_power_w,
            pv2_power_w=pv2_power_w,
            # =============================================
            # BATTERY
            # =============================================
            battery_soc_pct=battery_soc_pct,
            battery_power_w=battery_power_w,
            # =============================================
            # GRID
            # =============================================
            grid_power_w=grid_power_w,
            # =============================================
            # CONSUMPTION
            # =============================================
            consumption_power_w=consumption_power_w,
            # =============================================
            # INVERTER
            # =============================================
            ac_power_w=ac_power_w,
            # =============================================
            # RAW DEBUG DATA
            # =============================================
            raw_registers=registers,
        )

    def reconnect(self):

        logger.warning(f"Reconnecting to {self.host}")

        try:
            self.client.close()

        except Exception:
            pass

        self.client = ModbusTcpClient(
            host=self.host,
            port=self.port,
        )

        connected = self.client.connect()

        if not connected:
            logger.error(f"Unable to connect to {self.host}")

            raise ConnectionError(f"Unable to connect to {self.host}")

        logger.info(f"Connected to {self.host}")

    def read_charge_schedule(self):

        result = self.client.read_holding_registers(
            address=0x0097,
            count=9,
            device_id=self.slave_id,
        )

        if result.isError():
            raise RuntimeError(f"Schedule read failed: {result}")

        registers = {
            0x0097 + index: value for index, value in enumerate(result.registers)
        }

        return parse_schedule(registers)

    def read_work_mode_registers(self):
        logger.info("Inside Work_Mode_Read_Registers")

        max_attempts = 3

        last_exception = None

        for attempt in range(max_attempts):
            client = ModbusTcpClient(
                host=self.host,
                port=self.port,
            )

            try:
                connected = client.connect()

                if not connected:
                    raise RuntimeError(f"Unable to connect to {self.host}")

                result = client.read_holding_registers(
                    address=WORK_MODE_REGISTER,
                    count=2,
                    device_id=self.slave_id,
                )

                if result.isError():
                    raise RuntimeError(f"Work mode read failed: {result}")

                return {
                    WORK_MODE_REGISTER: result.registers[0],
                    MANUAL_MODE_REGISTER: result.registers[1],
                }

            except Exception as exc:
                last_exception = exc

                logger.warning(
                    f"Work mode read failed ({attempt + 1}/{max_attempts}): {exc}"
                )

                time.sleep(5.0)

            finally:
                try:
                    client.close()
                except Exception:
                    pass

        raise RuntimeError(
            f"Unable to read work mode after multiple attempts: {last_exception}"
        )

    def read_work_mode_registers_from_connection(
        self,
        client,
    ):
        logger.info("Inside Work_Mode_Read_Registers")

        result = client.read_holding_registers(
            address=WORK_MODE_REGISTER,
            count=2,
            device_id=self.slave_id,
        )

        if result.isError():
            raise RuntimeError(f"Work mode read failed: {result}")

        return {
            WORK_MODE_REGISTER: result.registers[0],
            MANUAL_MODE_REGISTER: result.registers[1],
        }

    def read_polling_registers(
        self,
    ):

        max_attempts = 3

        last_exception = None

        for attempt in range(max_attempts):
            client = ModbusTcpClient(
                host=self.host,
                port=self.port,
            )

            try:
                connected = client.connect()

                if not connected:
                    raise RuntimeError(f"Unable to connect to {self.host}")

                logger.info("A get_work_mode")
                work_mode_registers = self.read_work_mode_registers_from_connection(
                    client,
                )
                logger.info("B poll_once")
                telemetry_registers = self.read_register_block_from_connection(client)
                logger.info("B1 register block OK")

                return (
                    work_mode_registers,
                    telemetry_registers,
                )

            except Exception as exc:
                last_exception = exc

                logger.warning(
                    f"Polling read failed ({attempt + 1}/{max_attempts}): {exc}"
                )

                time.sleep(5.0)

            finally:
                try:
                    client.close()
                except Exception:
                    pass

        raise RuntimeError(
            f"Unable to read polling registers after multiple attempts: {last_exception}"
        )

    def close(self):

        logger.info(f"Closing connection to {self.host}")

        try:
            self.client.close()

        except Exception:
            pass
