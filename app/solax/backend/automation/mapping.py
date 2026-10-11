from app.enums.automation_enums import InverterWorkMode
from app.enums.solax_enums import WorkMode, ManualMode

_MODE_MAPPING = {
    InverterWorkMode.SELF_USE: (WorkMode.SELF_USE, None),
    InverterWorkMode.MANUAL_CHARGE: (WorkMode.MANUAL, ManualMode.FORCE_CHARGE),
    InverterWorkMode.MANUAL_DISCHARGE: (WorkMode.MANUAL, ManualMode.FORCE_DISCHARGE),
    InverterWorkMode.PEAK_SHAVING: (WorkMode.PEAK_SHAVING, None),
    InverterWorkMode.FEED_IN: (WorkMode.FEED_IN, None),
    InverterWorkMode.BACKUP: (WorkMode.BACKUP, None),
}

def map_automation_mode(mode: InverterWorkMode) -> tuple[WorkMode, ManualMode | None]:
    """
    Map an InverterWorkMode to the corresponding (WorkMode, ManualMode) pair.

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
