"""SolaX Cloud API telemetry used only when local Modbus polling fails."""

import os
from datetime import datetime
from zoneinfo import ZoneInfo

import requests
from dotenv import load_dotenv

from app.solax.telemetry.models import PowerFlowSnapshot

load_dotenv()

BASE_URL = os.getenv("SOLAX_BASE_URL")
CLIENT_ID = os.getenv("SOLAX_CLIENT_ID")
CLIENT_SECRET = os.getenv("SOLAX_CLIENT_SECRET")
PLANT_ID = os.getenv("SOLAX_PLANT_ID", "1676898809691574274")
BUSINESS_TYPE = 1  # Residential
MAX_READING_AGE_SECONDS = 360  # Five-minute reporting cadence plus small tolerance


class SolaxCloudTelemetryService:
    """Fetch the latest cloud snapshot without controlling the inverter."""

    def __init__(self):
        # Do not prevent the local Modbus poller from starting if cloud API
        # credentials are absent; validate them only when fallback is needed.
        self._inverter_sn = os.getenv("SOLAX_INVERTER_SN")

    def _get_access_token(self) -> str:
        response = requests.post(
            f"{BASE_URL}/openapi/auth/oauth/token",
            data={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "grant_type": "client_credentials",
            },
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 0:
            raise RuntimeError(f"SolaX token request failed: {data}")
        return data["result"]["access_token"]

    @staticmethod
    def _check_response(response):
        response.raise_for_status()
        data = response.json()
        if data.get("code") != 10000:
            raise RuntimeError(f"SolaX API request failed: {data}")
        return data.get("result")

    def _get_inverter_serial(self, headers) -> str:
        if self._inverter_sn:
            return self._inverter_sn

        response = requests.get(
            f"{BASE_URL}/openapi/v2/device/page_device_info",
            headers=headers,
            params={
                "plantId": PLANT_ID,
                "deviceType": 1,
                "businessType": BUSINESS_TYPE,
                "pageNo": 1,
            },
            timeout=30,
        )
        result = self._check_response(response)
        records = result.get("records", []) if isinstance(result, dict) else []
        if not records:
            raise RuntimeError("SolaX Cloud returned no inverter devices")

        self._inverter_sn = records[0].get("deviceSn")
        if not self._inverter_sn:
            raise RuntimeError("SolaX Cloud did not return an inverter serial number")
        return self._inverter_sn

    def _get_realtime_data(self, headers, inverter_sn, device_type):
        params = {
            "snList": inverter_sn,
            "deviceType": device_type,
            "businessType": BUSINESS_TYPE,
        }
        if device_type == 2:
            params["requestSnType"] = 1

        response = requests.get(
            f"{BASE_URL}/openapi/v2/device/realtime_data",
            headers=headers,
            params=params,
            timeout=30,
        )
        result = self._check_response(response)
        if not result:
            raise RuntimeError(f"No SolaX real-time data returned for device type {device_type}")
        return result[0]

    def poll(self) -> PowerFlowSnapshot:
        """Fetch a cloud telemetry sample and return a snapshot for monitoring; cloud readings are not accepted as local control telemetry."""
        if not all((BASE_URL, CLIENT_ID, CLIENT_SECRET)):
            raise RuntimeError("Missing SolaX API configuration in .env")
        token = self._get_access_token()
        headers = {"Authorization": f"bearer {token}"}
        inverter_sn = self._get_inverter_serial(headers)
        inverter = self._get_realtime_data(headers, inverter_sn, 1)

        local_timestamp = inverter.get("plantLocalTime")
        if local_timestamp:
            timestamp = datetime.strptime(local_timestamp, "%Y-%m-%d %H:%M:%S")
        elif inverter.get("dataTime"):
            timestamp = datetime.fromisoformat(
                inverter["dataTime"].replace("Z", "+00:00")
            ).astimezone(ZoneInfo("Europe/London")).replace(tzinfo=None)
        else:
            raise RuntimeError("SolaX Cloud response has no measurement timestamp")

        now = datetime.now(ZoneInfo("Europe/London")).replace(tzinfo=None)
        age_seconds = (now - timestamp).total_seconds()
        if age_seconds > MAX_READING_AGE_SECONDS:
            raise RuntimeError(
                f"SolaX Cloud reading is stale ({age_seconds / 60:.1f} minutes old)"
            )

        pv_power = inverter.get("MPPTTotalInputPower")
        if pv_power is None:
            mppt_map = inverter.get("mpptMap") or {}
            mppt_powers = [
                value for key, value in mppt_map.items()
                if key.lower().endswith("power") and value is not None
            ]
            pv_power = sum(mppt_powers) if mppt_powers else None

        grid_power = inverter.get("gridPower")
        ac_power = inverter.get("acPower1")

        battery = {}
        try:
            battery = self._get_realtime_data(headers, inverter_sn, 2)
        except Exception:
            # Inverter readings remain useful if the battery endpoint is unavailable.
            battery = {}

        battery_power = battery.get("chargeDischargePower")
        consumption_power = ac_power
        if consumption_power is None and None not in (pv_power, grid_power, battery_power):
            # Approximation only; AC output is preferred because PV input is DC-side.
            consumption_power = pv_power - grid_power - battery_power

        return PowerFlowSnapshot(
            timestamp=timestamp,
            upload_time=local_timestamp,
            pv_power_w=pv_power,
            pv1_power_w=(inverter.get("mpptMap") or {}).get("MPPT1Power"),
            pv2_power_w=(inverter.get("mpptMap") or {}).get("MPPT2Power"),
            battery_soc_pct=battery.get("batterySOC"),
            battery_power_w=battery_power,
            battery_status="Cloud",
            grid_power_w=grid_power,
            consumption_power_w=consumption_power,
            ac_power_w=ac_power,
            inverter_status=str(inverter.get("deviceStatus")) if inverter.get("deviceStatus") is not None else None,
            inverter_serial=inverter_sn,
            work_mode_name="Unavailable (cloud telemetry)",
            work_mode=None,
            manual_mode=None,
            raw_registers=None,
        )
