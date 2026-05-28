# telemetry/modbus_client.py

from datetime import datetime
from zoneinfo import ZoneInfo

from pymodbus.client import ModbusTcpClient

from services.solax.telemetry.models import (
    PowerFlowSnapshot,
)

from services.solax.telemetry.registers import (
    INVERTER_POWER,
    PV1_POWER,
    PV2_POWER,
    BATTERY_POWER,
    BATTERY_SOC,
    GRID_LSB,
    GRID_MSB,
)


REGISTER_BLOCK_START = 0
REGISTER_BLOCK_SIZE = 80


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

        self.client.connect()

    @staticmethod
    def signed16(value: int) -> int:

        if value > 32767:
            return value - 65536

        return value

    @staticmethod
    def signed32(msb: int, lsb: int) -> int:

        unsigned32 = (
            (msb * 65536)
            + lsb
        )

        if unsigned32 > 2147483647:

            return (
                unsigned32
                - 4294967296
            )

        return unsigned32

    def read_register_block(self) -> dict[int, int]:

        result = (
            self.client.read_input_registers(

                address=REGISTER_BLOCK_START,

                count=REGISTER_BLOCK_SIZE,

                device_id=self.slave_id,

            )
        )

        if result.isError():

            raise RuntimeError(
                f"Modbus read failed: {result}"
            )

        return {

            REGISTER_BLOCK_START + index: value

            for index, value
            in enumerate(result.registers)

        }

    def poll_once(self) -> PowerFlowSnapshot:

        registers = (
            self.read_register_block()
        )

        ac_power_w = self.signed16(
            registers[
                INVERTER_POWER
            ]
        )

        pv1_power_w = registers[
            PV1_POWER
        ]

        pv2_power_w = registers[
            PV2_POWER
        ]

        pv_power_w = (
            pv1_power_w
            + pv2_power_w
        )

        battery_power_w = self.signed16(
            registers[
                BATTERY_POWER
            ]
        )

        battery_soc_pct = registers[
            BATTERY_SOC
        ]

        grid_power_w = self.signed32(

            msb=registers[
                GRID_MSB
            ],

            lsb=registers[
                GRID_LSB
            ],

        )

        consumption_power_w = (
            ac_power_w - grid_power_w
        )

        return PowerFlowSnapshot(

            timestamp=datetime.now(
                ZoneInfo("Europe/London")
            ),

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

            consumption_power_w=(
                consumption_power_w
            ),

            # =============================================
            # INVERTER
            # =============================================

            ac_power_w=ac_power_w,

            # =============================================
            # RAW DEBUG DATA
            # =============================================

            raw_registers=registers,

        )
