from app.backend.automation.engine import (
    AutomationEngine,
)

from app.backend.automation.automation_repository import (
    ScheduleRepository,
)

from app.backend.storage.db import (
    get_connection,
)

connection = get_connection()

repo = ScheduleRepository(
    connection,
)

engine = AutomationEngine(
    repo,
)

print(
    engine.get_state()
)