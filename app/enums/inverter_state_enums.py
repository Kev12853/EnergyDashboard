# app/enums/inverter_state_enums.py

from enum import StrEnum


class InverterRequestPhase(StrEnum):
    OVERRIDE = "OVERRIDE"
    RESTORE = "RESTORE"