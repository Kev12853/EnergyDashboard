import logging
import time

from app.solax.telemetry.aggregate import (
    TelemetryAggregator,
)


logging.basicConfig(
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


aggregator = TelemetryAggregator()


while True:
    try:
        # logger.info(
        #     "Rebuilding 1m aggregates..."
        # )

        aggregator.rebuild_1m()

        # logger.info(
        #     "Rebuilding 30m aggregates..."
        # )

        aggregator.rebuild_30m()

        # logger.info(
        #     "Cleaning raw telemetry..."
        # )
        #
        aggregator.cleanup_raw_telemetry()
        #
        # logger.info(
        #     "Aggregation complete"
        # )

    except Exception:
        logger.exception("Aggregation failed")

    time.sleep(300)
