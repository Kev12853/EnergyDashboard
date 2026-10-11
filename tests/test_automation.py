from app.solax.backend.automation import (
    AutomationEngine,
)

from app.solax.backend.automation import (
    ScheduleRepository,
)

from app.solax.backend.storage.db import (
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