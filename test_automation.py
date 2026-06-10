from app.backend.automation.engine import (
    AutomationEngine,
)

from app.backend.automation.repository import (
    AutomationRepository,
)

from app.backend.storage.db import (
    get_connection,
)

connection = get_connection()

repo = AutomationRepository(
    connection,
)

engine = AutomationEngine(
    repo,
)

print(
    engine.get_state()
)