import time
import logging

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


client = SolaxModbusClient(
    host="192.168.1.66",
)

repository = TelemetryRepository()


while True:

    try:

        snapshot = client.poll_once()

        repository.save_snapshot(
            snapshot
        )

        # logger.info(snapshot)

    except Exception:

        logger.exception(
            "Poll failed"
        )

    time.sleep(2)