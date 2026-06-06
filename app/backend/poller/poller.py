import datetime
import time
import logging

from app.backend.automation.repository import AutomationRepository
from app.backend.automation.scheduler import Scheduler
from app.backend.inverter.controller import InverterController
from app.solax.telemetry.modbus_client import (
    SolaxModbusClient,
)

from app.solax.storage.repository import (
    TelemetryRepository,
)

from app.backend.storage.db import (
    get_connection,
)

from app.backend.storage.schema import (
    create_all_tables,
)

logging.basicConfig(
    level=logging.INFO,
    format=("%(asctime)s %(levelname)s %(name)s: %(message)s"),
)

logger = logging.getLogger(__name__)

connection = get_connection()

create_all_tables(connection)
client = SolaxModbusClient(
    host="192.168.1.66",
)

repository = TelemetryRepository(connection)

logger.info("Starting to Poll")

automation_repo = AutomationRepository(connection)

controller = InverterController(client)

scheduler = Scheduler(
    automation_repo,
    controller,
)

while True:
    try:
        snapshot = client.poll_once()

        repository.save_snapshot(snapshot)

        scheduler.evaluate()

    except Exception:
        logger.exception("Poll failed")

        try:
            logger.warning("Attempting reconnect")

            client.reconnect()

            logger.info("Reconnect successful")

        except Exception:
            logger.exception("Reconnect failed")

    time.sleep(5)
