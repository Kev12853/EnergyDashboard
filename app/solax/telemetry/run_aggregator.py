import time

from app.backend.common.logging_utils import (
    setup_logger,
)
from app.solax.backend.storage.telemetry_aggregation import (
    TelemetryAggregator,
)
from app.connections.connection import get_connection
from app.enums.service_enums import ServiceName
from app.solax.storage.solax_repository import TelemetryRepository

logger = setup_logger(
    "EnergyDashboard_Aggregator",
)
logger.info("Aggregator starting")


def main():

    aggregator = TelemetryAggregator()
    connection = get_connection()
    telemetry_repository = TelemetryRepository(connection)

    while True:
        try:
            aggregator.rebuild_1m()
            aggregator.rebuild_30m()
            aggregator.cleanup_raw_telemetry()

            telemetry_repository.save_heartbeat(ServiceName.AGGREGATOR)

            logger.info("Aggregation complete")

        except Exception:
            logger.exception("Aggregation failed")

        time.sleep(300)


if __name__ == "__main__":
    main()
