from datetime import datetime
import time

import pandas as pd

from app.enums.service_enums import ServiceName

from app.logging.logger import setup_logger

from app.octopus.api.octopus_api import (
    get_intelligent_dispatches,
    get_tariffs,
    get_octopus_agreements,
    get_completed_dispatches,
    get_device_consumption_breakdown,
)

from app.connections.connection import get_connection
from app.octopus.storage.octopus_schema import (
    create_agreements_table,
    create_tariffs_table,
    create_dispatches_table,
    create_accounts_table,
    create_consumption_costs_table,
    create_four_rate_tariffs_table,
)
from app.octopus.storage.repository import OctopusRepository

logger = setup_logger("Octopus Service")


def initialise_database():
    conn = get_connection()

    create_tariffs_table(conn)
    create_four_rate_tariffs_table(conn)
    create_dispatches_table(conn)
    create_accounts_table(conn)
    create_consumption_costs_table(conn)

    conn.commit()
    conn.close()


def update_prices(
    repository: OctopusRepository,
    import_tariff_code: str,
    export_tariff_code: str,
) -> None:

    now = pd.Timestamp.now(tz="UTC")

    period_from = (
        now - pd.Timedelta(hours=24)
    ).isoformat()

    period_to = (
        now + pd.Timedelta(hours=48)
    ).isoformat()

    # -------------------------------------------------
    # Import tariff
    # -------------------------------------------------

    logger.info("Downloading import electricity prices")

    import_prices = get_tariffs(
        import_tariff_code,
        period_from=period_from,
        period_to=period_to,
    )

    import_rows = repository.upsert_tariffs(
        import_prices,
        import_tariff_code,
    )

    logger.info(
        "Synchronised %d import tariff periods",
        import_rows,
    )

    # -------------------------------------------------
    # Export tariff
    # -------------------------------------------------

    logger.info("Downloading export electricity prices")

    export_prices = get_tariffs(
        export_tariff_code,
        period_from=period_from,
        period_to=period_to,
    )

    export_rows = repository.upsert_tariffs(
        export_prices,
        export_tariff_code,
    )

    logger.info(
        "Synchronised %d export tariff periods",
        export_rows,
    )

    # print("IMPORT TARIFF CODE:", import_tariff_code)
    # print("IMPORT PRICE ROWS:", len(import_prices))

    if not import_prices.empty:
        print("FIRST IMPORT PRICE:", import_prices[0])
        print("LAST IMPORT PRICE:", import_prices[-1])


def update_dispatches(repository: OctopusRepository) -> None:

    logger.info("Downloading Intelligent planned dispatches")
    planned = get_intelligent_dispatches()

    logger.info("Downloading Intelligent completed dispatches")
    completed = get_completed_dispatches()

    dispatches = pd.concat(
        [planned, completed],
        ignore_index=True,
    )

    if dispatches.empty:
        logger.info("No dispatches returned")
        return

    repository.upsert_dispatches(dispatches)

    logger.info(
        "Processed %d dispatches",
        len(dispatches),
    )

def update_consumption_costs(
    repository: OctopusRepository,
) -> None:

    logger.info("Downloading Octopus consumption costs")

    # now = pd.Timestamp.now(tz="UTC")
    #
    # period_from = (
    #     now - pd.Timedelta(hours=24)
    # ).isoformat()
    #
    # period_to = now.isoformat()
    #


    period_from = "2026-09-20T00:00:00Z"
    period_to = "2026-09-25T00:00:00Z"

    consumption = get_device_consumption_breakdown(
        period_from,
        period_to,
    )


    if consumption.empty:
        logger.info("No consumption cost data returned")
        return

    rows_changed = repository.upsert_consumption_costs(
        consumption
    )

    logger.info(
        "Synchronised %d consumption cost rows",
        rows_changed,
    )
    
def save_heartbeat() -> None:

    connection = get_connection()

    try:
        now = datetime.now().isoformat()
        connection.execute(
            """
            INSERT INTO service_heartbeat (
                service_name,
                last_seen
            )
            VALUES (?, ?)

            ON CONFLICT(service_name)
            DO UPDATE SET
                last_seen = excluded.last_seen
            """,
            (
                ServiceName.OCTOPUS.value,
                now,
            ),
        )

        connection.commit()

    finally:
        connection.close()


def main() -> None:

    logger.info("Octopus Service starting")
    repository = OctopusRepository()

    initialise_database()

    while True:
        try:
            logger.info("=" * 80)
            logger.info("Running Octopus Service")
            logger.info("Synchronising Octopus agreements")
            agreements = get_octopus_agreements()
            rows_added = repository.upsert_agreements(agreements)
            logger.info(
                "Agreements synchronised, %d new rows",
                rows_added,
            )
            import_tariff_code = repository.get_current_import_tariff()
            logger.info(
                "Current import tariff: %s",
                import_tariff_code,
            )
            export_tariff_code = repository.get_current_export_tariff()
            logger.info(
                "Current export tariff: %s",
                export_tariff_code,
            )
            update_prices(
                repository,
                import_tariff_code,
                export_tariff_code,
            )
            update_dispatches(repository)
            update_consumption_costs(repository)
            save_heartbeat()

        except Exception:
            logger.exception("Unhandled exception in Octopus Service")

        time.sleep(300)


if __name__ == "__main__":
    main()
