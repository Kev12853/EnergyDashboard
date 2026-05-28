import csv
import time

from services.solax.client import SolaxModbusClient
from services.solax.constants import (
    INVERTER_IP,
    POLL_INTERVAL,
    RUNTIME_BLOCK_START,
    RUNTIME_BLOCK_COUNT,
    CSV_PATH,
)
from services.solax.telemetry import SolaxTelemetryService

# =========================================================
# CONFIG
# =========================================================

# =========================================================
# ANSI COLORS
# =========================================================

RESET = "\033[0m"

GREEN = "\033[92m"

# =========================================================
# CLIENT
# =========================================================

client = SolaxModbusClient(
    host=INVERTER_IP,
)

service = SolaxTelemetryService(client)

# =========================================================
# CSV SETUP
# =========================================================

if not CSV_PATH.exists():

    with open(CSV_PATH, "w", newline="") as f:

        writer = csv.writer(f)

        header = ["timestamp"]

        for register in range(
            RUNTIME_BLOCK_START,
            RUNTIME_BLOCK_START + RUNTIME_BLOCK_COUNT,
        ):

            header.append(f"reg_{register}")

        writer.writerow(header)

# =========================================================
# MAIN LOOP
# =========================================================

previous_values = {}

print("Starting SolaX debug watch...")

try:

    while True:

        snapshot = service.get_live_snapshot()

        # =================================================
        # CSV LOGGING
        # =================================================

        if snapshot.raw_runtime_block:

            with open(CSV_PATH, "a", newline="") as f:

                writer = csv.writer(f)

                row = [
                    snapshot.timestamp.isoformat()
                ]

                row.extend(snapshot.raw_runtime_block)

                writer.writerow(row)

        # =================================================
        # CONSOLE OUTPUT
        # =================================================

        print("\n" + "=" * 80)

        print(
            snapshot.timestamp.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        print("=" * 80)

        print(
            f"\nBlock "
            f"{RUNTIME_BLOCK_START} - "
            f"{RUNTIME_BLOCK_START + RUNTIME_BLOCK_COUNT - 1}"
        )

        # =================================================
        # REGISTER CHANGE DETECTION
        # =================================================

        if snapshot.raw_runtime_block:

            for i, value in enumerate(
                snapshot.raw_runtime_block
            ):

                register = (
                    RUNTIME_BLOCK_START + i
                )

                changed = False

                if register in previous_values:

                    if (
                        previous_values[register]
                        != value
                    ):

                        changed = True

                previous_values[register] = value

                line = (
                    f"Register "
                    f"{register:03d}: {value}"
                )

                if changed:

                    print(
                        f"{GREEN}{line}{RESET}"
                    )

        time.sleep(POLL_INTERVAL)

except KeyboardInterrupt:

    print("\nStopping...")

finally:

    client.close()

    print("Connection closed")