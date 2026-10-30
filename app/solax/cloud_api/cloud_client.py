"""Call the SolaX cloud API and translate its realtime response into application data. This is a remote monitoring source and is not used as local control telemetry."""

from datetime import datetime

import requests

from app.solax.telemetry.models import PowerFlowSnapshot


class SolaxCloudAPI:
    """Wrap the SolaX cloud HTTP API and translate responses for monitoring/reporting; it is not a local Modbus control channel."""
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

        """Request realtime cloud data and return the decoded API payload; network, response and API errors may propagate."""
        url = f"{self.base_url}/api/v2/dataAccess/realtimeInfo/get"

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
            raise Exception(f"SolaX API error: {data.get('exception')}")

        return data["result"]

    # =====================================================
    # NORMALIZED SNAPSHOT
    # =====================================================

    def get_live_snapshot(self) -> PowerFlowSnapshot:

        """Convert a realtime cloud response into the module’s live snapshot representation."""
        data = self.get_realtime_data()

        #
        # PV Power
        #
        # Sum all available PV strings
        #

        pv_power = sum(
            [
                data.get("powerdc1") or 0,
                data.get("powerdc2") or 0,
                data.get("powerdc3") or 0,
                data.get("powerdc4") or 0,
            ]
        )

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
