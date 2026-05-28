import time

from services.solax.cloud_api import SolaxCloudAPI

#
# Replace these
#

TOKEN_ID = "202307140243593619522312"

WIFI_SN = "SVKQDUUJLK"


api = SolaxCloudAPI(
    token_id=TOKEN_ID,
    wifi_sn=WIFI_SN,
)


while True:

    snapshot = api.get_live_snapshot()

    print("\n" + "=" * 80)

    print(snapshot.timestamp)

    print("=" * 80)

    print(f"PV Power        : {snapshot.pv_power_w} W")

    print(f"Battery SOC     : {snapshot.battery_soc_pct} %")

    print(f"Battery Power   : {snapshot.battery_power_w} W")

    print(f"Grid Power      : {snapshot.grid_power_w} W")

    print(f"Inverter Status : {snapshot.inverter_status}")

    time.sleep(30)