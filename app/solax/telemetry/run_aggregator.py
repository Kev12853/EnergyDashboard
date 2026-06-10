import time

from app.solax.telemetry.aggregate import (
    TelemetryAggregator,
)

from app.backend.common.logging_utils import (
    setup_logger,
)

logger = setup_logger(
    "aggregator",
)
logger.info("Aggregator starting")


def main():

    aggregator = TelemetryAggregator()

    while True:
        try:
            aggregator.rebuild_1m()
            aggregator.rebuild_30m()
            aggregator.cleanup_raw_telemetry()

            logger.info("Aggregation complete")

        except Exception:
            logger.exception("Aggregation failed")

        time.sleep(300)


if __name__ == "__main__":
    main()
