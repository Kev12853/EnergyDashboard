"""Named automation work modes accepted by the SolaX scheduler.

These values describe schedule intent and are mapped to raw SolaX work/manual
register pairs by the automation mapping layer.
"""

from enum import StrEnum


class InverterWorkMode(StrEnum):
    """Named schedule modes that map to raw work/manual register pairs."""
    SELF_USE = "SELF_USE"
    MANUAL_CHARGE = "MANUAL_CHARGE"
    MANUAL_DISCHARGE = "MANUAL_DISCHARGE"
    PEAK_SHAVING = "PEAK_SHAVING"
    FEED_IN = "FEED_IN"
    BACKUP = "BACKUP"