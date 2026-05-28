"""
SolaX Modbus register definitions.

IMPORTANT
---------
These mappings are intentionally marked as provisional until we fully
validate them against YOUR inverter firmware and live telemetry.

Do NOT scatter raw register numbers throughout the project.

All register addresses, scaling rules, and signed conversions should
be centralized here.

X1-Hybrid-G4
WiFi 3.0 dongle
Modbus TCP
"""

from dataclasses import dataclass
from typing import Optional


# =========================================================
# REGISTER DEFINITION MODEL
# =========================================================

@dataclass(frozen=True)
class RegisterDefinition:
    name: str
    address: int
    scale: float = 1.0
    signed: bool = False
    unit: Optional[str] = None
    notes: str = ""


# =========================================================
# HELPER
# =========================================================

def signed_16bit(value: int) -> int:
    """
    Convert unsigned 16-bit integer to signed integer.

    Example:
        60536 -> -5000
    """

    if value > 32767:
        return value - 65536

    return value


# =========================================================
# PROVISIONAL REGISTER MAP
# =========================================================
#
# These are based on:
#
# - your live scans
# - known SolaX conventions
# - Home Assistant community mappings
#
# They MUST be validated against real telemetry.
#
# =========================================================


PV_POWER = RegisterDefinition(
    name="pv_power",
    address=25,
    scale=1.0,
    signed=False,
    unit="W",
    notes="Possible total PV generation power"
)

BATTERY_SOC = RegisterDefinition(
    name="battery_soc",
    address=37,
    scale=1.0,
    signed=False,
    unit="%",
    notes="Possible battery state of charge"
)

GRID_VOLTAGE = RegisterDefinition(
    name="grid_voltage",
    address=48,
    scale=0.1,
    signed=False,
    unit="V",
    notes="Likely grid voltage"
)

OUTPUT_VOLTAGE = RegisterDefinition(
    name="output_voltage",
    address=49,
    scale=0.1,
    signed=False,
    unit="V",
    notes="Likely inverter output voltage"
)

SIGNED_POWER_FLOW = RegisterDefinition(
    name="signed_power_flow",
    address=65,
    scale=1.0,
    signed=True,
    unit="W",
    notes="Possible grid or battery signed power flow"
)

INVERTER_TEMPERATURE = RegisterDefinition(
    name="inverter_temperature",
    address=29,
    scale=1.0,
    signed=False,
    unit="°C",
    notes="Possible inverter temperature"
)


# =========================================================
# CENTRAL REGISTRY
# =========================================================

REGISTERS = {
    "pv_power": PV_POWER,
    "battery_soc": BATTERY_SOC,
    "grid_voltage": GRID_VOLTAGE,
    "output_voltage": OUTPUT_VOLTAGE,
    "signed_power_flow": SIGNED_POWER_FLOW,
    "inverter_temperature": INVERTER_TEMPERATURE,
}


# =========================================================
# DECODING
# =========================================================

def decode_register(
    definition: RegisterDefinition,
    raw_value: int,
):
    """
    Decode a raw Modbus register value using the definition.
    """

    value = raw_value

    if definition.signed:
        value = signed_16bit(value)

    value = value * definition.scale

    return value