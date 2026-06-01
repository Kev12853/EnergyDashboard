import time
import logging
import sqlite3
from pathlib import Path
from app.backend.automation.repository import AutomationRepository
from app.backend.automation.scheduler import Scheduler
from app.backend.inverter.controller import InverterController
from services.solax.telemetry.modbus_client import (
    SolaxModbusClient,
)

from services.solax.storage.repository import (
    TelemetryRepository,
)


logging.basicConfig(
    level=logging.INFO,
)

logger = logging.getLogger(__name__)

DB_PATH = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "telemetry.db"
)

connection = sqlite3.connect(
    DB_PATH,
    check_same_thread=False,
)

connection.row_factory = sqlite3.Row
client = SolaxModbusClient(
    host="192.168.1.66",
)

repository = TelemetryRepository()

result = client.client.read_holding_registers(
    address=139,
    count=2,
    device_id=client.slave_id,
)

logger.info(
    "Starting to Poll"
)

schedule = client.read_charge_schedule()

logger.info(schedule)
repo = AutomationRepository(
    connection
)

controller = InverterController(
    client
)

scheduler = Scheduler(
    repo,
    controller,
)
while True:

    try:

        snapshot = client.poll_once()

        repository.save_snapshot(
            snapshot
        )

        #scheduler.evaluate()

        # logger.info(
        #     "Poll OK"
        # )

    except Exception:

        logger.exception(
            "Poll failed"
        )

    time.sleep(5)