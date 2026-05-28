from datetime import datetime
from zoneinfo import ZoneInfo

from .decoder import (
    signed16,
    signed32,
)

from .models import (
    SolaxTelemetrySnapshot,
)

from .registers import (
    BATTERY_POWER,
    BATTERY_SOC,
    GRID_LSB,
    GRID_MSB,
    INVERTER_POWER,
    PV1_POWER,
    PV2_POWER,
)


def map_registers_to_snapshot(

    registers: dict[int, int]

) -> SolaxTelemetrySnapshot:

    inverter_w = signed16(
        registers[INVERTER_POWER]
    )

    pv1_w = registers[PV1_POWER]
    pv2_w = registers[PV2_POWER]

    solar_w = pv1_w + pv2_w

    battery_w = signed16(
        registers[BATTERY_POWER]
    )

    battery_soc_pct = registers[BATTERY_SOC]

    grid_w = signed32(

        msb=registers[GRID_MSB],
        lsb=registers[GRID_LSB],

    )

    consumption_w = (
        inverter_w - grid_w
    )

    return SolaxTelemetrySnapshot(

        timestamp=datetime.now(
            ZoneInfo("Europe/London")
        ),

        solar_w=solar_w,
        inverter_w=inverter_w,

        battery_w=battery_w,
        battery_soc_pct=battery_soc_pct,

        grid_w=grid_w,
        consumption_w=consumption_w,

        pv1_w=pv1_w,
        pv2_w=pv2_w,

        raw_registers=registers,

    )