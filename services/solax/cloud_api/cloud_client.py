from datetime import datetime

import requests

from services.solax.models import PowerFlowSnapshot


class SolaxCloudAPI:

    def __init__(
        self,
        token_id: str,
        wifi_sn: str,
        base_url: str = "https://global.solaxcloud.com",
    ):

        self.token_id = token_id

        self.wifi_sn = wifi_sn

        self.base_url = base_url.rstrip("/")

    # =====================================================
    # REALTIME DATA
    # =====================================================

    def get_realtime_data(self):

        url = (
            f"{self.base_url}"
            "/api/v2/dataAccess/realtimeInfo/get"
        )

        headers = {
            "tokenId": self.token_id,
            "Content-Type": "application/json",
        }

        payload = {
            "wifiSn": self.wifi_sn,
        }

        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

        if not data.get("success"):

            raise Exception(
                f"SolaX API error: "
                f"{data.get('exception')}"
            )

        return data["result"]

    # =====================================================
    # NORMALIZED SNAPSHOT
    # =====================================================

    def get_live_snapshot(self) -> PowerFlowSnapshot:

        data = self.get_realtime_data()

        #
        # PV Power
        #
        # Sum all available PV strings
        #

        pv_power = sum([
            data.get("powerdc1") or 0,
            data.get("powerdc2") or 0,
            data.get("powerdc3") or 0,
            data.get("powerdc4") or 0,
        ])

        snapshot = PowerFlowSnapshot(

            timestamp=datetime.now(),

            #
            # SOLAR
            #

            pv_power_w=pv_power,

            #
            # BATTERY
            #

            battery_soc_pct=data.get("soc"),

            battery_power_w=data.get("batPower"),

            #
            # GRID
            #

            grid_power_w=data.get("feedinpower"),

            #
            # INVERTER
            #

            inverter_status=data.get("inverterStatus"),

        )

        return snapshot