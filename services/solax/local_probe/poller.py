import time
import logging

from services.solax.local_probe.client import (
    SolaxModbusClient,
)

from services.solax.local_probe.mapper import (
    map_registers_to_snapshot,
)

from services.solax.local_probe.repository import (
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

last_snapshot = None
last_successful_poll = None


while True:

    try:

        registers = (
            client.read_register_block()
        )

        snapshot = (
            map_registers_to_snapshot(
                registers
            )
        )

        repository.save_snapshot(
            snapshot
        )

        last_snapshot = snapshot

        last_successful_poll = (
            snapshot.timestamp
        )

        logger.info(snapshot)

    except Exception:

        logger.exception(
            "Poll failed"
        )

    time.sleep(2)