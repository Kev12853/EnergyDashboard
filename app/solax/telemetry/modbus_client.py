# telemetry/modbus_client.py

from datetime import datetime
import time
from zoneinfo import ZoneInfo

from pymodbus.client import ModbusTcpClient
import logging



from app.solax.analytics.decoders import parse_schedule
from app.solax.telemetry.models import (
    PowerFlowSnapshot,
)

from app.solax.telemetry.registers import (
    INVERTER_POWER,
    PV1_POWER,
    PV2_POWER,
    BATTERY_POWER,
    BATTERY_SOC,
    GRID_LSB,
    GRID_MSB,
)

import app.solax.telemetry.registers as registers

REGISTER_BLOCK_START = 0
REGISTER_BLOCK_SIZE = 10

logger = logging.getLogger(__name__)

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

        if not self.client.connect():
            raise ConnectionError(f"Unable to connect to {host}")

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
            try:
                result = self.client.read_input_registers(
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

                time.sleep(1.0)

        raise RuntimeError(
            f"Unable to read Modbus registers after multiple attempts: {last_exception}"
        )

    def poll_once(self) -> PowerFlowSnapshot:

        registers = self.read_register_block()

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
            consumption_power_w=(consumption_power_w),
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

        result = self.client.read_holding_registers(
            address=registers.WORK_MODE_REGISTER,
            count=2,
            device_id=self.slave_id,
        )

        if result.isError():
            raise RuntimeError(f"Work mode read failed: {result}")

        return {
            registers.WORK_MODE_REGISTER: result.registers[0],
            registers.MANUAL_MODE_REGISTER: result.registers[1],
        }