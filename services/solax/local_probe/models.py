from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SolaxTelemetrySnapshot:

    timestamp: datetime

    solar_w: int
    inverter_w: int
    battery_w: int
    battery_soc_pct: int
    grid_w: int
    consumption_w: int

    pv1_w: int
    pv2_w: int

    raw_registers: dict[int, int]