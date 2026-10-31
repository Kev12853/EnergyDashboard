
"""Standalone SolaX Cloud telemetry poller.

Runs independently of the local Modbus poller.
Cloud readings are monitoring-only and stored separately.
"""

import os
import time

from app.connections.connection import get_connection
from app.enums.service_enums import ServiceName
from app.logging.logger import setup_logger
from app.solax.backend.polling.solax_cloud_service import (
    SolaxCloudTelemetryService,
)
from app.solax.backend.storage.schema import create_solax_tables
from app.solax.backend.storage.solax_repository import TelemetryRepository


POLL_INTERVAL_SECONDS = 300

logger = setup_logger("SolaXCloudPoller")


def update_heartbeat(repository, status, message):
    """Record cloud poller health without interrupting polling."""
    try:
        repository.save_heartbeat(
            ServiceName.SOLAX_CLOUD,
            status=status,
            message=message,
        )
    except Exception:
        logger.exception("Unable to update cloud service heartbeat")


def main():
    """Continuously collect and store SolaX Cloud telemetry."""

    logger.info(
        "SolaX Cloud poller starting, PID=%s",
        os.getpid(),
    )

    connection = get_connection()

    try:
        create_solax_tables(connection)

        repository = TelemetryRepository(connection)
        cloud_service = SolaxCloudTelemetryService()

        while True:
            try:
                snapshot = cloud_service.poll()

                repository.save_snapshot(
                    snapshot,
                    source="cloud",
                )

                update_heartbeat(
                    repository,
                    "Running",
                    "SolaX Cloud telemetry current",
                )

                logger.info(
                    "Cloud telemetry saved: PV=%sW, Battery=%sW, Grid=%sW, SOC=%s%%",
                    snapshot.pv_power_w,
                    snapshot.battery_power_w,
                    snapshot.grid_power_w,
                    snapshot.battery_soc_pct,
                )

            except Exception as exc:
                logger.exception("SolaX Cloud polling failed")

                update_heartbeat(
                    repository,
                    "Warning",
                    f"Cloud polling failed: {exc}",
                )

            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        logger.info("SolaX Cloud poller stopping")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
