from datetime import datetime
import sqlite3

from app.backend.automation.models import (
    AutomationRule,
)

from app.backend.automation.repository import (
    AutomationRepository,
)

connection = sqlite3.connect(
    "data/telemetry.db"
)

from app.solax.storage.repository import (
    TelemetryRepository,
)

TelemetryRepository()

print("Done")

connection.row_factory = sqlite3.Row

repo = AutomationRepository(
    connection
)

rule = AutomationRule(
    id=None,
    name="Evening Export",
    enabled=True,
    start_time="16:00",
    end_time="19:00",
    action="FORCE_DISCHARGE",
    updated_at=datetime.now(),
)

repo.save_rule(rule)

loaded = repo.get_rule()

print(loaded)