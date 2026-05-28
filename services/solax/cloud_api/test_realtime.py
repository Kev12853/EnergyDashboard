import time

from services.solax.cloud_api.cloud_client import (
    SolaxCloudClient,
)
from services.solax.constants import (
    SOLAX_TOKEN_ID,
    SOLAX_SERIAL_NUMBER,
)

# =========================================================
# CLIENT
# =========================================================

client = SolaxCloudClient(
    token_id=SOLAX_TOKEN_ID,
    serial_number=SOLAX_SERIAL_NUMBER,
)

# =========================================================
# MAIN LOOP
# =========================================================

print("Starting SolaX Cloud test...")

try:

    while True:

        snapshot = client.get_snapshot()

        print("\n" + "=" * 80)

        print(
            snapshot.timestamp.strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        )

        print("=" * 80)

        #
        # SOLAR
        #

        print(
            f"PV Total Power     : "
            f"{snapshot.pv_power_w} W"
        )

        print(
            f"PV1 Power          : "
            f"{snapshot.pv1_power_w} W"
        )

        print(
            f"PV2 Power          : "
            f"{snapshot.pv2_power_w} W"
        )

        #
        # BATTERY
        #

        print(
            f"Battery SOC        : "
            f"{snapshot.battery_soc_pct} %"
        )

        print(
            f"Battery Power      : "
            f"{snapshot.battery_power_w} W"
        )

        #
        # GRID
        #

        print(
            f"Grid Power         : "
            f"{snapshot.grid_power_w} W"
        )

        #
        # INVERTER
        #

        print(
            f"AC Power           : "
            f"{snapshot.ac_power_w} W"
        )

        print(
            f"Inverter Status    : "
            f"{snapshot.inverter_status}"
        )

        print(
            f"Upload Time        : "
            f"{snapshot.upload_time}"
        )

        time.sleep(30)

except KeyboardInterrupt:

    print("\nStopping...")