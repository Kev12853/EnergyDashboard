"""Verify that schedule entry is stored beneath an active Smart Flex request without taking ownership of the top-level override."""

from datetime import datetime
from pprint import pprint

from app.connections.connection import get_connection
from app.solax.backend.automation.models import SchedulePeriod
from app.solax.backend.automation.scheduler import Scheduler
from app.solax.backend.automation.automation_repository import ScheduleRepository
from app.solax.backend.automation.inverter_state_repository import (
    InverterStateRepository,
)

from app.enums.solax_enums import WorkMode, ManualMode
from app.enums.automation_enums import InverterWorkMode
from app.enums.inverter_state_enums import InverterRequestPhase
from app.solax.backend.inverter.inverter_reconciler import InverterReconciler
from app.solax.telemetry.models import PowerFlowSnapshot



class FakeInverterService:
    def write_work_mode(self, work_mode, manual_mode):
        print(
            f"INVERTER WRITE: work_mode={work_mode}, "
            f"manual_mode={manual_mode}"
        )

connection = get_connection()

schedule_repo = ScheduleRepository(connection)
inverter_state_repo = InverterStateRepository(connection)


# Clean start
connection.execute("DELETE FROM schedule_periods")
connection.commit()
inverter_state_repo.clear()


# Create a schedule
schedule = SchedulePeriod(
    id=None,
    name="Test Scheduler Entry",
    source="TEST",
    enabled=True,
    start_time="08:00",
    end_time="10:00",
    mode=InverterWorkMode.SELF_USE,
    priority=10,
    updated_at=datetime.now(),
)

schedule_repo.save_period(schedule)


# Scheduler already owns the inverter request.
inverter_state_repo.set(
    requested_work_mode=WorkMode.MANUAL,
    requested_manual_mode=ManualMode.FORCE_CHARGE,
    restore_work_mode_to=WorkMode.PEAK_SHAVING,
    restore_manual_mode_to=ManualMode.IDLE,
    underlying_work_mode=None,
    underlying_manual_mode=None,
    phase=InverterRequestPhase.OVERRIDE,
    active=True,
    source="scheduler",
)


snapshot = PowerFlowSnapshot(
    timestamp=datetime.now(),
    work_mode=WorkMode.PEAK_SHAVING,
    manual_mode=ManualMode.IDLE,
)


scheduler = Scheduler(
    schedule_repo,
    inverter_state_repo,
)


# Scheduler is not yet active, so this is an entry into its window.
scheduler.evaluate(
    snapshot,
    current_time="09:00",
)


state = inverter_state_repo.get()

print()
print("=" * 60)
print("RESULT")
print("=" * 60)
pprint(state)


# Scheduler must remain the current owner/request.
assert state["source"] == "scheduler"
assert state["requested_work_mode"] == WorkMode.SELF_USE
assert state["requested_manual_mode"] is None

# There should be no underlying request.
assert state["underlying_work_mode"] is None
assert state["underlying_manual_mode"] is None

print()
print("=" * 60)
print("PASS")
print("=" * 60)

print()
print("SMART FLEX STARTS:")

from app.solax.backend.automation.smart_flex_orchestrator import (
    SmartFlexOrchestrator,
)

orchestrator = SmartFlexOrchestrator(inverter_state_repo)

orchestrator.start(snapshot)

print("AFTER SMART FLEX START:")
pprint(inverter_state_repo.get())

print()
print("SMART FLEX STOPS:")

orchestrator.stop()

print("AFTER SMART FLEX STOP:")
pprint(inverter_state_repo.get())

print()
print("RECONCILER PROCESSES SCHEDULER REQUEST:")

reconciler = InverterReconciler(
    inverter_state_repo,
    FakeInverterService(),
)

reconciler.process(snapshot)

print("AFTER RECONCILER:")
pprint(inverter_state_repo.get())

print()
print("SECOND RECONCILER POLL:")

snapshot.work_mode = WorkMode.SELF_USE
snapshot.manual_mode = None

reconciler.process(snapshot)

print("AFTER SECOND RECONCILER:")
pprint(inverter_state_repo.get())

print()
print("SCHEDULER LEAVES WINDOW:")

scheduler.evaluate(
    snapshot,
    current_time="11:00",
)

print("AFTER SCHEDULER LEAVE:")
pprint(inverter_state_repo.get())

print()
print("FINAL RECONCILER:")

snapshot.work_mode = WorkMode.PEAK_SHAVING
snapshot.manual_mode = ManualMode.IDLE

reconciler.process(snapshot)

print("AFTER FINAL RECONCILER:")
pprint(inverter_state_repo.get())