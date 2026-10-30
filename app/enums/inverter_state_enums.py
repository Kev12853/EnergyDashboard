"""Lifecycle phases for the durable desired inverter request.

The scheduler and Smart Flex write these phases to SQLite; the reconciler
uses them to decide whether an override or restoration is awaiting telemetry
confirmation. They are not inverter-reported operating modes.
"""

# app/enums/inverter_state_enums.py

from enum import StrEnum


class InverterRequestPhase(StrEnum):
    """Durable request lifecycle states: OVERRIDE applies a temporary request, RESTORE requests its saved restoration target, and IDLE means no active request."""
    OVERRIDE = "OVERRIDE"
    RESTORE = "RESTORE"
    IDLE = "IDLE"