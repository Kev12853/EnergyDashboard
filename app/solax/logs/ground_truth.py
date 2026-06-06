# poller/solax/telemetry/ground_truth.py

from datetime import (
    datetime,
)

from pathlib import Path

import csv
import time

from app.solax.cloud_api.cloud_client import (
    SolaxCloudClient,
)

from app.solax.storage.constants import (
    SOLAX_TOKEN_ID,
    SOLAX_SERIAL_NUMBER,
)


# =====================================================
# OUTPUT FILE
# =====================================================

OUTPUT_FILE = Path("poller/solax/telemetry/ground_truth.csv")


# =====================================================
# CSV COLUMN HEADERS
# =====================================================
#
# Use UI-friendly names matching
# SolaX portal terminology.
#
# Solar      = raw PV generation
# Inverter   = usable AC inverter output
# Battery    = signed battery power
# Export     = signed grid flow
# Consumption = calculated house load
#
# Battery:
#
# +ve = charging
# -ve = discharging
#
# Grid:
#
# +ve = export
# -ve = import
#
# =====================================================

FIELDNAMES = [
    "timestamp",
    "solar_w",
    "inverter_w",
    "battery_w",
    "battery_soc_pct",
    "consumption_w",
    "export_w",
    "upload_time",
]


# =====================================================
# CLOUD CLIENT
# =====================================================

client = SolaxCloudClient(
    token_id=SOLAX_TOKEN_ID,
    serial_number=SOLAX_SERIAL_NUMBER,
)


# =====================================================
# CAPTURE ONE GROUND TRUTH SAMPLE
# =====================================================


def capture_ground_truth():

    try:
        snapshot = client.get_snapshot()

        # =============================================
        # HOUSE CONSUMPTION
        # =============================================
        #
        # SolaX chart logic:
        #
        # Consumption =
        #
        # Inverter AC
        # - Grid export
        # - Battery charging
        # + Battery discharge
        #
        # Battery already carries sign:
        #
        # +ve = charging
        # -ve = discharging
        #
        # therefore:
        #
        # Consumption =
        #
        # AC - Grid - Battery
        #
        # Examples:
        #
        # AC=1406
        # Grid=1064
        # Battery=0
        #
        # Consumption=342
        #
        # =============================================

        consumption = (
            snapshot.ac_power_w - snapshot.grid_power_w - snapshot.battery_power_w
        )

        row = {
            # =========================================
            # LOCAL POLL TIME
            # =========================================
            "timestamp": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
            # =========================================
            # SOLAR DC GENERATION
            # =========================================
            "solar_w": snapshot.pv_power_w,
            # =========================================
            # INVERTER AC OUTPUT
            # =========================================
            "inverter_w": snapshot.ac_power_w,
            # =========================================
            # BATTERY POWER
            # =========================================
            "battery_w": snapshot.battery_power_w,
            # =========================================
            # BATTERY SOC
            # =========================================
            "battery_soc_pct": snapshot.battery_soc_pct,
            # =========================================
            # HOUSE CONSUMPTION
            # =========================================
            "consumption_w": round(
                consumption,
                1,
            ),
            # =========================================
            # GRID EXPORT / IMPORT
            # =========================================
            "export_w": snapshot.grid_power_w,
            # =========================================
            # CLOUD UPDATE TIME
            # =========================================
            "upload_time": snapshot.upload_time,
        }

        file_exists = OUTPUT_FILE.exists()

        with open(
            OUTPUT_FILE,
            "a",
            newline="",
        ) as f:
            writer = csv.DictWriter(
                f,
                fieldnames=FIELDNAMES,
            )

            if not file_exists:
                writer.writeheader()

            writer.writerow(row)

        print(row)

    except Exception as e:
        print(f"Ground truth failed: {e}")


# =====================================================
# MAIN LOOP
# =====================================================

if __name__ == "__main__":
    last_upload = None

    while True:
        try:
            snapshot = client.get_snapshot()

            # =========================================
            # ONLY RECORD NEW CLOUD DATA
            # =========================================

            if snapshot.upload_time != last_upload:
                last_upload = snapshot.upload_time

                capture_ground_truth()

            else:
                print(
                    f"[{datetime.now().astimezone().strftime('%Y-%m-%d %H:%M:%S')}] "
                    "No cloud update"
                )

        except Exception as e:
            print(e)

        time.sleep(60)
