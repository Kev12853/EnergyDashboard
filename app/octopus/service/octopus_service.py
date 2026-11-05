from datetime import datetime, time, timedelta, timezone
import time as sleep_time

import pandas as pd

from app.enums.service_enums import ServiceName

from app.logging.logger import setup_logger

from app.octopus.api.octopus_api import (
    get_intelligent_dispatches,
    get_tariffs,
    get_octopus_agreements,
    get_completed_dispatches,
    get_device_consumption_breakdown,
    get_smartflex_vehicle_status,
)

from app.connections.connection import get_connection
from app.octopus.storage.octopus_schema import (
    create_agreements_table,
    create_tariffs_table,
    create_dispatches_table,
    create_accounts_table,
    create_consumption_costs_table,
    create_four_rate_tariffs_table,
    create_smartflex_vehicle_status_table,
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
    create_smartflex_vehicle_status_table(conn)

    conn.commit()
    conn.close()


def update_prices(
    repository: OctopusRepository,
    import_tariff_code: str,
    export_tariff_code: str,
) -> None:

    now = pd.Timestamp.now(tz="UTC")

    period_from = (now - pd.Timedelta(hours=24)).isoformat()

    period_to = (now + pd.Timedelta(hours=48)).isoformat()

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


def update_dispatches(repository: OctopusRepository) -> None:

    logger.info("Downloading Intelligent planned dispatches")
    planned = get_intelligent_dispatches()

    logger.info("Downloading Intelligent completed dispatches")
    completed = get_completed_dispatches()

    dispatches = pd.concat(
        [planned, completed],
        ignore_index=True,
    )

    if not dispatches.empty:
        repository.upsert_dispatches(dispatches)
    else:
        logger.info("No dispatches returned; successful empty result will be recorded")

    # A current successful empty query is different from a query failure.
    connection = get_connection()
    try:
        connection.execute(
            """INSERT INTO octopus_data_status (data_name, updated_at)
               VALUES ('dispatches', ?)
               ON CONFLICT(data_name) DO UPDATE SET updated_at=excluded.updated_at""",
            (datetime.now().astimezone().isoformat(),),
        )
        connection.commit()
    finally:
        connection.close()

    logger.info("Processed %d dispatches", len(dispatches))


def update_consumption_costs(
    repository: OctopusRepository,
) -> None:

    logger.info("Downloading Octopus consumption costs")

    period_to = datetime.now(timezone.utc)
    period_from = period_to - timedelta(hours=48)

    period_from = period_from.isoformat().replace("+00:00", "Z")
    period_to = period_to.isoformat().replace("+00:00", "Z")

    consumption = get_device_consumption_breakdown(
        period_from,
        period_to,
    )

    print("CONSUMPTION PERIOD:", period_from, "to", period_to)
    print("ROWS RETURNED:", len(consumption))

    if not consumption.empty:
        print(
            "FIRST READING:",
            consumption["interval_start"].min(),
            "| LAST READING:",
            consumption["interval_start"].max(),
        )

    if consumption.empty:
        logger.info("No consumption readings returned")
        return

    tariff_code = repository.get_current_import_tariff()

    tariffs = repository.get_four_rate_tariffs_for_period(
        tariff_code,
        datetime.fromisoformat(period_from),
        datetime.fromisoformat(period_to),
    )

    tariffs = [tariff for tariff in tariffs if tariff["rate_type"] in ("DAY", "NIGHT")]

    if not tariffs:
        logger.warning("No applicable import tariff periods found")
        return

    tariff_rates = {tariff["rate_type"]: tariff for tariff in tariffs}

    for index, row in consumption.iterrows():
        local_start = pd.Timestamp(row["interval_start"])

        if local_start.tzinfo is None:
            local_start = local_start.tz_localize("Europe/London")
        else:
            local_start = local_start.tz_convert("Europe/London")

        current_time = local_start.time()

        if current_time >= time(23, 30) or current_time < time(5, 30):
            rate_type = "NIGHT"
        else:
            rate_type = "DAY"

        tariff = tariff_rates.get(rate_type)

        if tariff is None:
            logger.warning("Missing %s tariff rate", rate_type)
            continue

        consumption_kwh = row["consumption_kwh"]

        consumption.loc[index, "tou_bucket"] = rate_type

        consumption.loc[index, "rate_p_per_kwh"] = tariff["rate_inc_vat_p_per_kwh"]

        consumption.loc[index, "cost_excl_vat_p"] = (
            consumption_kwh * tariff["rate_exc_vat_p_per_kwh"]
        )

        consumption.loc[index, "cost_incl_vat_p"] = (
            consumption_kwh * tariff["rate_inc_vat_p_per_kwh"]
        )

    consumption = consumption.dropna(subset=["rate_p_per_kwh"])

    rows_changed = repository.upsert_consumption_costs(consumption)

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


def update_vehicle_status() -> None:
    """Persist vehicle inputs so SolaX control never calls Octopus directly."""
    status = get_smartflex_vehicle_status()
    if (
        not isinstance(status, dict)
        or "connected" not in status
        or "charging" not in status
    ):
        return
    connection = get_connection()
    try:
        connection.execute(
            """INSERT INTO octopus_vehicle_status (id, connected, charging, observed_at)
               VALUES (1, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET connected=excluded.connected,
                   charging=excluded.charging, observed_at=excluded.observed_at""",
            (
                int(bool(status["connected"])),
                int(bool(status["charging"])),
                datetime.now().astimezone().isoformat(),
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
            import_tariff_code = "E-1R-INTELLI-FIX-12M-26-04-18-A"

            logger.info(
                "Selected household import tariff: %s",
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
            try:
                update_vehicle_status()
            except Exception:
                logger.exception("Unable to refresh Smart Flex vehicle status")
            update_consumption_costs(repository)
            save_heartbeat()

        except Exception:
            logger.exception("Unhandled exception in Octopus Service")

        sleep_time.sleep(300)


if __name__ == "__main__":
    main()
