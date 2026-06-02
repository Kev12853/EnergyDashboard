from app.solax.telemetry import (
    SolaxModbusClient,
)

from app.backend.inverter.controller import (
    InverterController,
)

from app.backend.automation.repository import (
    AutomationRepository,
)

from app.backend.automation.scheduler import (
    Scheduler,
)

import sqlite3


connection = sqlite3.connect(
    "data/telemetry.db"
)

connection.row_factory = sqlite3.Row

repo = AutomationRepository(
    connection
)

client = SolaxModbusClient(
    host="192.168.1.66",
)

controller = InverterController(
    client
)

scheduler = Scheduler(
    repo,
    controller,
)

print(
    scheduler.is_in_window(
        "13:00",
        "15:00",
        "14:07",
    )
)

print(
    scheduler.is_in_window(
        "15:00",
        "16:00",
        "14:07",
    )
)

print(
    scheduler.is_in_window(
        "23:30",
        "05:30",
        "14:07",
    )
)

print(
    scheduler.is_in_window(
        "23:30",
        "05:30",
        "02:00",
    )
)