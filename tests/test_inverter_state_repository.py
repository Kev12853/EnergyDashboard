from app.enums.inverter_state_enums import InverterRequestPhase
from app.enums.solax_enums import ManualMode, WorkMode
from app.solax.backend.automation.inverter_state_repository import (
    InverterStateRepository,
)


class FakeRepository(InverterStateRepository):
    def __init__(self):
        self.state = {
            "requested_work_mode": WorkMode.MANUAL,
            "requested_manual_mode": ManualMode.FORCE_CHARGE,
            "restore_work_mode_to": WorkMode.SELF_USE,
            "restore_manual_mode_to": 0,
            "underlying_work_mode": WorkMode.MANUAL,
            "underlying_manual_mode": ManualMode.FORCE_CHARGE,
            "active": 1,
            "source": "smart_flex",
            "phase": InverterRequestPhase.OVERRIDE,
        }

    def get(self):
        return self.state

    def set(
        self,
        requested_work_mode,
        requested_manual_mode,
        restore_work_mode_to,
        restore_manual_mode_to,
        underlying_work_mode,
        underlying_manual_mode,
        phase,
        active,
        source,
    ):
        self.state = {
            "requested_work_mode": requested_work_mode,
            "requested_manual_mode": requested_manual_mode,
            "restore_work_mode_to": restore_work_mode_to,
            "restore_manual_mode_to": restore_manual_mode_to,
            "underlying_work_mode": underlying_work_mode,
            "underlying_manual_mode": underlying_manual_mode,
            "active": active,
            "source": source,
            "phase": phase,
        }


repo = FakeRepository()

repo.activate_underlying()

state = repo.get()

print("RESULT:")
print(state)

assert state["requested_work_mode"] == WorkMode.MANUAL
assert state["requested_manual_mode"] == ManualMode.FORCE_CHARGE
assert state["restore_work_mode_to"] == WorkMode.SELF_USE
assert state["restore_manual_mode_to"] == 0
assert state["underlying_work_mode"] is None
assert state["underlying_manual_mode"] is None
assert state["active"] == 1
assert state["source"] == "scheduler"
assert state["phase"] == InverterRequestPhase.OVERRIDE

print("PASS")