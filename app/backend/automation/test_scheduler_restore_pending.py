"""
test_scheduler_restore_pending.py

Verify that once a restore has been requested, subsequent scheduler
evaluations do NOT cancel the request before the reconciler has
completed it.
"""

from datetime import datetime
from pprint import pprint

from app.backend.storage.db import get_connection

from app.backend.automation.models import SchedulePeriod
from app.backend.automation.scheduler import Scheduler
from app.backend.automation.automation_repository import ScheduleRepository

from app.backend.automation.inverter_state_repository import (
    InverterStateRepository,
)

from app.enums.solax_enums import WorkMode, ManualMode
from app.enums.automation_enums import AutomationMode
from app.enums.inverter_state_enums import InverterRequestPhase

from app.solax.telemetry.models import PowerFlowSnapshot

#
# Database
#

connection = get_connection()

schedule_repo = ScheduleRepository(connection)
inverter_state_repo = InverterStateRepository(connection)

#
# Clean start
#

connection.execute("DELETE FROM schedule_periods")
connection.commit()

inverter_state_repo.clear()

#
# Create schedule
#

schedule = SchedulePeriod(
    id=None,
    name="Test Force Charge",
    source="TEST",
    enabled=True,
    start_time="08:00",
    end_time="10:00",
    mode=AutomationMode.MANUAL_CHARGE,
    priority=10,
    updated_at=datetime.now(),
)

schedule_repo.save_period(schedule)

#
# Pretend scheduler has already entered the window.
#

inverter_state_repo.set(
    requested_work_mode=WorkMode.MANUAL,
    requested_manual_mode=ManualMode.FORCE_CHARGE,
    restore_work_mode_to=WorkMode.PEAK_SHAVING,
    restore_manual_mode_to=ManualMode.IDLE,
    phase=InverterRequestPhase.OVERRIDE,
    active=True,
    source="scheduler",
)

snapshot = PowerFlowSnapshot(
    timestamp=datetime.now(),
    work_mode=WorkMode.MANUAL,
    manual_mode=ManualMode.FORCE_CHARGE,
)

scheduler = Scheduler(
    schedule_repo,
    inverter_state_repo,
)

scheduler.is_active = True

#
# Disable the schedule.
#

schedule.enabled = False
schedule.updated_at = datetime.now()
schedule_repo.save_period(schedule)

#
# FIRST evaluation
# This should create the restore request.
#

print("\nFIRST EVALUATION")
scheduler.evaluate(
    snapshot,
    current_time="09:00",
)

state = inverter_state_repo.get()

print("\nAfter first evaluation")
pprint(state)

assert state["requested_work_mode"] == WorkMode.PEAK_SHAVING
assert state["requested_manual_mode"] == ManualMode.IDLE
assert state["restore_work_mode_to"] is None
assert state["phase"] == InverterRequestPhase.RESTORE

#
# SECOND evaluation
# Simulate the next poll BEFORE the reconciler has completed.
#

print("\nSECOND EVALUATION")

scheduler.evaluate(
    snapshot,
    current_time="09:01",
)

state = inverter_state_repo.get()

print("\nAfter second evaluation")
pprint(state)

#
# The scheduler should NOT have cancelled the request.
#

assert state is not None

assert state["requested_work_mode"] == WorkMode.PEAK_SHAVING
assert state["requested_manual_mode"] == ManualMode.IDLE

assert state["phase"] == InverterRequestPhase.RESTORE
assert state["active"] == 1

print()
print("=" * 60)
print("PASS")
print("=" * 60)