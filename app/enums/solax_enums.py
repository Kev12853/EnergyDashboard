from enum import IntEnum


class WorkMode(IntEnum):
    SELF_USE = 0
    FEED_IN = 1
    BACKUP = 2
    MANUAL = 3
    PEAK_SHAVING = 4
    TOU = 5


class ManualMode(IntEnum):
    IDLE = 0
    FORCE_CHARGE = 1
    FORCE_DISCHARGE = 2