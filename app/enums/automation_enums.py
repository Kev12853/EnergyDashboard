from enum import StrEnum


class AutomationMode(StrEnum):
    SELF_USE = "SELF_USE"
    FORCE_CHARGE = "FORCE_CHARGE"
    FORCE_DISCHARGE = "FORCE_DISCHARGE"
    PEAK_SHAVING = "PEAK_SHAVING"