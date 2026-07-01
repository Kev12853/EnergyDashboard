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

from app.enums.solax_enums import WorkMode, ManualMode
from app.config.solax_config import SCHEDULER_MODE_MANUAL_CHARGE

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
# Create a schedule
#

schedule = SchedulePeriod(
    id=None,
    name="Test Force Charge",
    source="TEST",
    enabled=True,
    start_time="08:00",
    end_time="10:00",
    mode=SCHEDULER_MODE_MANUAL_CHARGE,
    priority=10,
    updated_at=datetime.now(),
)

schedule_repo.save_period(schedule)

#
# Fake inverter snapshot
#

snapshot = PowerFlowSnapshot(
    timestamp=datetime.now(),

    work_mode=WorkMode.PEAK_SHAVING,
    manual_mode=ManualMode.IDLE,
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

print(f"requested_work_mode      = {WorkMode.MANUAL}")
print(f"requested_manual_mode    = {ManualMode.FORCE_CHARGE}")
print(f"restore_work_mode_to     = {WorkMode.PEAK_SHAVING}")
print(f"restore_manual_mode_to   = {ManualMode.IDLE}")
print("active                   = 1")

print()
print("=" * 60)
print("ACTUAL")
print("=" * 60)

pprint(state)

#
# Assertions
#

assert state["requested_work_mode"] == WorkMode.MANUAL
assert state["requested_manual_mode"] == ManualMode.FORCE_CHARGE

assert state["restore_work_mode_to"] == WorkMode.PEAK_SHAVING
assert state["restore_manual_mode_to"] == ManualMode.IDLE

assert state["active"] == 1

print()
print("=" * 60)
print("PASS")
print("=" * 60)