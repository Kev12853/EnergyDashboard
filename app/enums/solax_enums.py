"""Raw SolaX work-mode and manual-mode register values.

These integer enums translate between display/automation decisions and the
register values read by the poller or requested through guarded control writes.
They do not perform Modbus communication.
"""

from enum import IntEnum


class WorkMode(IntEnum):
    """Raw integer values for inverter work-mode registers, shared by mode translation, Smart Flex and reconciliation."""
    SELF_USE = 0
    FEED_IN = 1
    BACKUP = 2
    MANUAL = 3
    PEAK_SHAVING = 4
    TOU = 5


class ManualMode(IntEnum):
    """Raw integer values for the manual-mode register, including idle, force-charge and force-discharge commands."""
    IDLE = 0
    FORCE_CHARGE = 1
    FORCE_DISCHARGE = 2