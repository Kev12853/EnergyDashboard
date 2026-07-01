import logging
import time

from app.backend.storage.db import (
    get_connection,
)

from app.octopus.storage.schema import (
    create_dispatches_table,
    create_tariffs_table,
)

from app.octopus.storage.repository import (
    upsert_dispatches,
    upsert_tariffs,
)

from app.octopus.api.octopus_api import (
    get_intelligent_dispatches,
    get_tariffs,
)

from app.octopus.analytics.dispatches import (
    normalize_dispatches,
)

from app.octopus.analytics.tariffs import (
    normalize_import_tariffs,
)

# =====================================================
# LOGGING
# =====================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

logger = logging.getLogger(__name__)

# =====================================================
# INITIALISE DATABASE
# =====================================================

connection = get_connection()

create_dispatches_table(connection)

create_tariffs_table(connection)

connection.close()

logger.info("Octopus logger started")

# =====================================================
# HELPERS
# =====================================================


def get_active_tariffs():

    conn = get_connection()

    active_tarrif_rows = conn.execute(
        """
        SELECT DISTINCT

            tariff_code

        FROM

            octopus_agreements

        WHERE

            tariff_code
            IS NOT NULL
        """
    ).fetchall()

    conn.close()

    return [row["tariff_code"] for row in active_tarrif_rows]


# =====================================================
# MAIN LOOP
# =====================================================

last_tariff_refresh = None

while True:
    try:
        # =============================================
        # DISPATCHES
        # =============================================

        raw_dispatch_df = get_intelligent_dispatches()

        dispatch_df = normalize_dispatches(raw_dispatch_df)

        upsert_dispatches(dispatch_df)

        logger.info("Dispatches updated")

        # =============================================
        # TARIFFS
        # =============================================

        current_time = time.time()

        should_refresh_tariffs = (
            last_tariff_refresh is None or (current_time - last_tariff_refresh) >= 86400
        )

        if should_refresh_tariffs:
            tariff_codes = get_active_tariffs()

            total_rows = 0

            for tariff_code in tariff_codes:
                raw_tariff_df = get_tariffs(tariff_code=tariff_code)

                if raw_tariff_df.empty:
                    continue

                tariff_df = normalize_import_tariffs(
                    raw_tariff_df,
                    tariff_code,
                )

                rows = upsert_tariffs(tariff_df)

                total_rows += rows

            last_tariff_refresh = current_time

            logger.info(f"Tariffs updated ({total_rows} rows)")

    except Exception as e:
        logger.exception(f"Logger error: {e}")

    time.sleep(300)
