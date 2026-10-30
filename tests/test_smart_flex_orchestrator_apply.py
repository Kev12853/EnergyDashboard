"""Unit tests for SmartFlexOrchestrator request creation and ownership preservation."""

from app.solax.backend.storage.db import get_connection
from app.solax.backend.storage.schema import create_solax_tables
from app.solax.backend.automation.inverter_state_repository import (
    InverterStateRepository,
)
from app.solax.backend.automation.smart_flex_orchestrator import (
    SmartFlexOrchestrator,
)
from app.solax.storage.inverter_state import (
    clear_inverter_state,
    set_inverter_state,
)
from app.enums.inverter_state_enums import InverterRequestPhase


connection = get_connection()
create_solax_tables(connection)

clear_inverter_state(connection)

# Smart Flex is active with a Scheduler request underneath.
set_inverter_state(
    connection,
    requested_work_mode=3,
    requested_manual_mode=1,
    restore_work_mode_to=0,
    restore_manual_mode_to=0,
    underlying_work_mode=1,
    underlying_manual_mode=0,
    active=True,
    source="smart_flex",
    phase=InverterRequestPhase.OVERRIDE,
)

repository = InverterStateRepository(connection)
orchestrator = SmartFlexOrchestrator(repository)

print("BEFORE")
print(repository.get())

orchestrator.apply_decision("NORMAL", None)

print()
print("AFTER NORMAL")
print(repository.get())

state = repository.get()

assert state["requested_work_mode"] == 1
assert state["requested_manual_mode"] == 0
assert state["underlying_work_mode"] is None
assert state["underlying_manual_mode"] is None
assert state["restore_work_mode_to"] == 0
assert state["restore_manual_mode_to"] == 0
assert state["source"] == "scheduler"
assert state["phase"] == InverterRequestPhase.OVERRIDE

print("PASS")

clear_inverter_state(connection)