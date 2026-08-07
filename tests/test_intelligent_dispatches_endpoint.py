import json
import time
import requests

from app.octopus.api.octopus_api import (
    GRAPHQL_URL,
    get_graphql_token,
)

POLL_INTERVAL = 1800  # seconds (30 minutes)

SMARTFLEX_DEVICE_ID = "00000000-000a-4000-8020-0f02012aa714"
SMARTFLEX_VEHICLE_ID = "00000000-0002-4000-8020-000000100c8e"


def get_dispatches(device_id):

    query = f"""
    query {{
      flexPlannedDispatches(deviceId: "{device_id}") {{
        start
        end
        energyAddedKwh
        type
      }}
    }}
    """

    headers = {
        "Authorization": get_graphql_token(),
        "Content-Type": "application/json",
    }

    response = requests.post(
        GRAPHQL_URL,
        json={"query": query},
        headers=headers,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if "errors" in data:
        raise RuntimeError(json.dumps(data["errors"], indent=4))

    return data["data"]["flexPlannedDispatches"]


def print_dispatches(name, dispatches):

    print(f"\n{name}")
    print("-" * 80)

    if not dispatches:
        print("No planned dispatches.")
    else:
        print(json.dumps(dispatches, indent=4))


def main():

    previous = {
        "SmartFlexDevice": None,
        "SmartFlexVehicle": None,
    }

    print("Monitoring Intelligent Octopus planned dispatches...")
    print("Only changes will be displayed.")
    print("Press Ctrl+C to stop.")

    while True:

        try:

            current = {
                "SmartFlexDevice": get_dispatches(SMARTFLEX_DEVICE_ID),
                "SmartFlexVehicle": get_dispatches(SMARTFLEX_VEHICLE_ID),
            }

            changed = False

            for name in current:

                if current[name] != previous[name]:

                    if not changed:
                        print("\n" + "=" * 80)
                        print(time.strftime("%Y-%m-%d %H:%M:%S"))
                        changed = True

                    print_dispatches(name, current[name])

                    previous[name] = current[name]

            if changed:
                print("\nWaiting for next change...")

        except KeyboardInterrupt:
            print("\nStopped.")
            break

        except Exception as ex:
            print(f"\n{time.strftime('%Y-%m-%d %H:%M:%S')}  ERROR")
            print(ex)

        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()