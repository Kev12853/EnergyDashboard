"""Exercise the legacy SolaX automation facade against the configured SQLite database. This script has database side effects at import time and is not an isolated pytest test."""

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