"""Verify that a saved underlying schedule request can be promoted after Smart Flex ownership ends."""

from app.enums.solax_enums import WorkMode, ManualMode
from app.enums.inverter_state_enums import InverterRequestPhase
from app.solax.backend.automation.inverter_state_repository import InverterStateRepository


class FakeConnection:
    pass


class FakeStorage:
    def __init__(self):
        self.state = {
            "requested_work_mode": WorkMode.MANUAL,
            "requested_manual_mode": ManualMode.FORCE_CHARGE,
            "restore_work_mode_to": WorkMode.SELF_USE,
            "restore_manual_mode_to": None,
            "underlying_work_mode": WorkMode.MANUAL,
            "underlying_manual_mode": ManualMode.FORCE_DISCHARGE,
            "active": 1,
            "source": "smart_flex",
            "phase": InverterRequestPhase.OVERRIDE,
        }


# We will replace the repository's storage calls with fakes below.