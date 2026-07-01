from app.enums.automation_enums import AutomationMode
from app.enums.solax_enums import WorkMode, ManualMode

_MODE_MAPPING = {
    AutomationMode.SELF_USE: (WorkMode.SELF_USE, None),
    AutomationMode.MANUAL_CHARGE: (WorkMode.MANUAL, ManualMode.FORCE_CHARGE),
    AutomationMode.MANUAL_DISCHARGE: (WorkMode.MANUAL, ManualMode.FORCE_DISCHARGE),
    AutomationMode.PEAK_SHAVING: (WorkMode.PEAK_SHAVING, None),
    AutomationMode.FEED_IN: (WorkMode.FEED_IN, None),
    AutomationMode.BACKUP: (WorkMode.BACKUP, None),
}

def map_automation_mode(mode: AutomationMode) -> tuple[WorkMode, ManualMode | None]:
    """
    Map an AutomationMode to the corresponding (WorkMode, ManualMode) pair.

    Args:
        mode: The automation mode to map.

    Returns:
        A tuple of (WorkMode, ManualMode | None).

    Raises:
        ValueError: If the mode has no mapping.
    """
    if mode not in _MODE_MAPPING:
        raise ValueError(f"No inverter mode mapping defined for: {mode}")

    return _MODE_MAPPING[mode]
