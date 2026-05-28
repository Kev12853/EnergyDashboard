# telemetry/models.py

from dataclasses import dataclass

from datetime import datetime


@dataclass
class PowerFlowSnapshot:

    # =====================================================
    # TIMESTAMP
    # =====================================================

    timestamp: datetime

    upload_time: str | None = None

    # =====================================================
    # SOLAR
    # =====================================================

    pv_power_w: float | None = None

    pv1_power_w: float | None = None

    pv2_power_w: float | None = None

    # =====================================================
    # BATTERY
    # =====================================================

    battery_soc_pct: float | None = None

    # +ve = charging
    # -ve = discharging
    battery_power_w: float | None = None

    battery_status: str | None = None

    # =====================================================
    # GRID
    # =====================================================

    # +ve = export
    # -ve = import
    grid_power_w: float | None = None

    # =====================================================
    # CONSUMPTION
    # =====================================================

    consumption_power_w: float | None = None

    # =====================================================
    # INVERTER
    # =====================================================

    ac_power_w: float | None = None

    inverter_status: str | None = None

    inverter_serial: str | None = None

    # =====================================================
    # RAW DEBUG DATA
    # =====================================================

    raw_registers: dict[int, int] | None = None
