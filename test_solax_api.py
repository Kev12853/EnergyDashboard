"""Manual SolaX cloud API authentication and telemetry probe. It loads local environment configuration and makes network requests when executed; credential values are intentionally not documented."""

import os

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = os.getenv("SOLAX_BASE_URL")
CLIENT_ID = os.getenv("SOLAX_CLIENT_ID")
CLIENT_SECRET = os.getenv("SOLAX_CLIENT_SECRET")

PLANT_ID = "1676898809691574274"
BUSINESS_TYPE = 1  # Residential


def get_access_token():
    url = f"{BASE_URL}/openapi/auth/oauth/token"

    response = requests.post(
        url,
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
        raise RuntimeError(f"Token request failed: {data}")

    return data["result"]["access_token"]


def api_get(url, headers, params):
    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    if data.get("code") != 10000:
        raise RuntimeError(f"API request failed: {data}")

    return data.get("result")


def print_reading(label, value, unit=""):
    if value is None:
        print(f"{label}: unavailable")
    else:
        print(f"{label}: {value}{unit}")


def main():
    if not all([BASE_URL, CLIENT_ID, CLIENT_SECRET]):
        raise RuntimeError(
            "Missing SolaX API configuration in .env"
        )

    print("Requesting SolaX access token...")
    token = get_access_token()
    print("Access token obtained successfully.")

    headers = {
        "Authorization": f"bearer {token}",
    }

    # Get plant information
    print("\nRequesting plant information...")

    result = api_get(
        f"{BASE_URL}/openapi/v2/plant/page_plant_info",
        headers,
        {
            "businessType": BUSINESS_TYPE,
            "pageNo": 1,
        },
    )

    plants = result.get("records", [])

    plant = next(
        (
            p for p in plants
            if str(p.get("plantId")) == PLANT_ID
        ),
        None,
    )

    if not plant:
        raise RuntimeError(f"Plant {PLANT_ID} not found.")

    print(f"Plant: {plant.get('plantName')}")
    print(f"Plant ID: {plant.get('plantId')}")

    # Get inverter serial number
    print("\nRequesting inverter device list...")

    result = api_get(
        f"{BASE_URL}/openapi/v2/device/page_device_info",
        headers,
        {
            "plantId": PLANT_ID,
            "deviceType": 1,
            "businessType": BUSINESS_TYPE,
            "pageNo": 1,
        },
    )

    inverters = result.get("records", [])

    if not inverters:
        raise RuntimeError("No inverter found.")

    inverter = inverters[0]
    inverter_sn = inverter.get("deviceSn")

    if not inverter_sn:
        raise RuntimeError("Inverter serial number not found.")

    print(f"Inverter serial: {inverter_sn}")
    print(f"Inverter online status: {inverter.get('onlineStatus')}")

    # Get inverter real-time data
    print("\nRequesting inverter real-time data...")

    result = api_get(
        f"{BASE_URL}/openapi/v2/device/realtime_data",
        headers,
        {
            "snList": inverter_sn,
            "deviceType": 1,
            "businessType": BUSINESS_TYPE,
        },
    )

    if not result:
        raise RuntimeError("No inverter readings returned.")

    inverter_data = result[0]

    print("\n--- INVERTER ---")
    print_reading("Timestamp", inverter_data.get("plantLocalTime"))
    print_reading(
        "PV input power",
        inverter_data.get("MPPTTotalInputPower"),
        " W",
    )
    print_reading(
        "AC output power (phase 1)",
        inverter_data.get("acPower1"),
        " W",
    )
    print_reading(
        "Grid power",
        inverter_data.get("gridPower"),
        " W",
    )
    print_reading(
        "Daily imported energy",
        inverter_data.get("todayImportEnergy"),
        " kWh",
    )
    print_reading(
        "Daily exported energy",
        inverter_data.get("todayExportEnergy"),
        " kWh",
    )

    # Get battery real-time data using the inverter serial
    print("\nRequesting battery real-time data...")

    result = api_get(
        f"{BASE_URL}/openapi/v2/device/realtime_data",
        headers,
        {
            "snList": inverter_sn,
            "deviceType": 2,
            "requestSnType": 1,
            "businessType": BUSINESS_TYPE,
        },
    )

    if not result:
        print("No battery readings returned.")
        return

    battery_data = result[0]

    print("\n--- BATTERY ---")
    print_reading("Timestamp", battery_data.get("plantLocalTime"))
    print_reading(
        "State of charge",
        battery_data.get("batterySOC"),
        "%",
    )
    print_reading(
        "Battery power",
        battery_data.get("chargeDischargePower"),
        " W",
    )
    print_reading(
        "Remaining energy",
        battery_data.get("batteryRemainings"),
        " kWh",
    )
    print_reading(
        "Battery temperature",
        battery_data.get("batteryTemperature"),
        " C",
    )

    print("\nTest completed successfully.")


if __name__ == "__main__":
    main()