import time

from app.backend.common.logging_utils import setup_logger
from app.backend.octopus.repository import OctopusRepository
from app.backend.storage.db import get_connection
from app.enums.service_names import ServiceName
from app.octopus.api.octopus_api import (
    get_tariffs,
    get_intelligent_dispatches
)
from app.solax.storage.solax_repository import TelemetryRepository

logger = setup_logger("Octopus Service")


def update_prices(repository):
    """
    Download the latest electricity prices if they are not
    already stored in the database.
    """

    if repository.prices_are_current():
        logger.info("Electricity prices are already up to date")
        return

    logger.info("Downloading electricity prices")

    tariff_code = repository.get_current_import_tariff()

    prices = get_tariffs(tariff_code)

    rows = repository.upsert_tariffs(prices)

    logger.info("Saved %d tariff periods", rows)


def update_dispatches(repository):

    logger.info("Downloading Intelligent dispatches")

    dispatches = get_intelligent_dispatches()

    if dispatches.empty:
        logger.info("No dispatches returned")
        return

    repository.upsert_dispatches(dispatches)

    logger.info(
        "Processed %d dispatches",
        len(dispatches),
    )

def main():
    """
    Main entry point for the Octopus service.
    """

    logger.info("Octopus Service starting")

    repository = OctopusRepository()

    while True:
        try:
            logger.info("=" * 80)
            logger.info("Running Octopus Service")

            update_prices(repository)
            update_dispatches(repository)
            # ============================================================
            # Save Heartbeat
            # ============================================================
            connection = get_connection()
            telemetry_repository = TelemetryRepository(connection)
            telemetry_repository.save_heartbeat(ServiceName.OCTOPUS)

        except Exception:
            logger.exception("Unhandled exception in Octopus Service")

        time.sleep(10)
        # time.sleep(3600)

if __name__ == "__main__":
    main()