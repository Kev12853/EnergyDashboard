"""
test_scheduler_leave_window.py

Verify that leaving a schedule window requests restoration
of the previous inverter operating mode.
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

from app.solax.telemetry.models import PowerFlowSnapshot

WORK_MODE_SELF_USE = 0
WORK_MODE_FEED_IN = 1
WORK_MODE_BACKUP = 2
WORK_MODE_MANUAL = 3
WORK_MODE_PEAK_SHAVING = 4

MANUAL_MODE_IDLE = 0
MANUAL_MODE_FORCE_CHARGE = 1
MANUAL_MODE_FORCE_DISCHARGE = 2

MODE_MANUAL_CHARGE = "FORCE_CHARGE"

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
    mode=MODE_MANUAL_CHARGE,
    priority=10,
    updated_at=datetime.now(),
)

schedule_repo.save_period(schedule)

#
# Pretend the scheduler has already entered the window.
#

inverter_state_repo.set(
    requested_work_mode=WORK_MODE_MANUAL,
    requested_manual_mode=MANUAL_MODE_FORCE_CHARGE,

    restore_work_mode_to=WORK_MODE_PEAK_SHAVING,
    restore_manual_mode_to=MANUAL_MODE_IDLE,

    active=True,
    source="scheduler",
)

#
# Fake snapshot.
# The inverter has already changed to Force Charge.
#

snapshot = PowerFlowSnapshot(
    timestamp=datetime.now(),

    work_mode=WORK_MODE_MANUAL,
    manual_mode=MANUAL_MODE_FORCE_CHARGE,
)

#
# Scheduler
#

scheduler = Scheduler(
    schedule_repo,
    inverter_state_repo,
)

#
# Pretend we are already inside the schedule window.
#

scheduler.is_active = True

#
# Execute outside the schedule window.
#

scheduler.evaluate(
    snapshot,
    current_time="10:01",
)

#
# Results
#

state = inverter_state_repo.get()

print()
print("=" * 60)
print("EXPECTED")
print("=" * 60)

print(f"requested_work_mode      = {WORK_MODE_PEAK_SHAVING}")
print(f"requested_manual_mode    = {MANUAL_MODE_IDLE}")
print("restore_work_mode_to     = None")
print("restore_manual_mode_to   = None")
print("active                   = 1")

print()
print("=" * 60)
print("ACTUAL")
print("=" * 60)

pprint(state)

#
# Assertions
#

assert state["requested_work_mode"] == WORK_MODE_PEAK_SHAVING
assert state["requested_manual_mode"] == MANUAL_MODE_IDLE

assert state["restore_work_mode_to"] is None
assert state["restore_manual_mode_to"] is None

assert state["active"] == 1

print()
print("=" * 60)
print("PASS")
print("=" * 60)