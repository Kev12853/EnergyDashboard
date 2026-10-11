from datetime import datetime
from pprint import pprint

from app.solax.backend.storage.db import get_connection
from app.solax.backend.automation.models import SchedulePeriod
from app.solax.backend.automation.scheduler import Scheduler
from app.solax.backend.automation.automation_repository import ScheduleRepository
from app.solax.backend.automation.inverter_state_repository import (
    InverterStateRepository,
)

from app.enums.solax_enums import WorkMode, ManualMode
from app.enums.automation_enums import InverterWorkMode
from app.enums.inverter_state_enums import InverterRequestPhase
from app.solax.telemetry.models import PowerFlowSnapshot


connection = get_connection()

schedule_repo = ScheduleRepository(connection)
inverter_state_repo = InverterStateRepository(connection)


# Clean start
connection.execute("DELETE FROM schedule_periods")
connection.commit()
inverter_state_repo.clear()


# Create a schedule which is initially enabled
schedule = SchedulePeriod(
    id=None,
    name="Test Smart Flex No Schedule",
    source="TEST",
    enabled=True,
    start_time="08:00",
    end_time="10:00",
    mode=InverterWorkMode.MANUAL_CHARGE,
    priority=10,
    updated_at=datetime.now(),
)

schedule_repo.save_period(schedule)


# Smart Flex owns the current request.
# The Scheduler's desired state is stored underneath it.
inverter_state_repo.set(
    requested_work_mode=WorkMode.MANUAL,
    requested_manual_mode=ManualMode.FORCE_CHARGE,
    restore_work_mode_to=WorkMode.PEAK_SHAVING,
    restore_manual_mode_to=ManualMode.IDLE,
    underlying_work_mode=WorkMode.MANUAL,
    underlying_manual_mode=ManualMode.FORCE_CHARGE,
    phase=InverterRequestPhase.OVERRIDE,
    active=True,
    source="smart_flex",
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
scheduler.active_schedule_id = schedule.id


# Disable the schedule completely.
schedule.enabled = False
schedule.updated_at = datetime.now()
schedule_repo.save_period(schedule)


# Evaluate with no enabled schedules.
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


# Smart Flex must remain completely untouched.
assert state["source"] == "smart_flex"
assert state["requested_work_mode"] == WorkMode.MANUAL
assert state["requested_manual_mode"] == ManualMode.FORCE_CHARGE
assert state["phase"] == InverterRequestPhase.OVERRIDE

# Scheduler's underlying request must be cleared.
assert state["underlying_work_mode"] is None
assert state["underlying_manual_mode"] is None


print()
print("=" * 60)
print("PASS")
print("=" * 60)