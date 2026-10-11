from enum import StrEnum


class InverterWorkMode(StrEnum):
    SELF_USE = "SELF_USE"
    MANUAL_CHARGE = "MANUAL_CHARGE"
    MANUAL_DISCHARGE = "MANUAL_DISCHARGE"
    PEAK_SHAVING = "PEAK_SHAVING"
    FEED_IN = "FEED_IN"
    BACKUP = "BACKUP"