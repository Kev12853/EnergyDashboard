"""
test_scheduler_enter_window.py

Verify that entering a schedule window creates an override request
and remembers the current inverter operating mode.
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
# Create a schedule
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
# Fake inverter snapshot
#

snapshot = PowerFlowSnapshot(
    timestamp=datetime.now(),

    work_mode=WORK_MODE_PEAK_SHAVING,
    manual_mode=MANUAL_MODE_IDLE,
)

#
# Scheduler
#

scheduler = Scheduler(
    schedule_repo,
    inverter_state_repo,
)

#
# Execute
#

scheduler.evaluate(
    snapshot,
    current_time="09:00",
)

#
# Results
#

state = inverter_state_repo.get()

print()
print("=" * 60)
print("EXPECTED")
print("=" * 60)

print(f"requested_work_mode      = {WORK_MODE_MANUAL}")
print(f"requested_manual_mode    = {MANUAL_MODE_FORCE_CHARGE}")
print(f"restore_work_mode_to     = {WORK_MODE_PEAK_SHAVING}")
print(f"restore_manual_mode_to   = {MANUAL_MODE_IDLE}")
print("active                   = 1")

print()
print("=" * 60)
print("ACTUAL")
print("=" * 60)

pprint(state)

#
# Assertions
#

assert state["requested_work_mode"] == WORK_MODE_MANUAL
assert state["requested_manual_mode"] == MANUAL_MODE_FORCE_CHARGE

assert state["restore_work_mode_to"] == WORK_MODE_PEAK_SHAVING
assert state["restore_manual_mode_to"] == MANUAL_MODE_IDLE

assert state["active"] == 1

print()
print("=" * 60)
print("PASS")
print("=" * 60)