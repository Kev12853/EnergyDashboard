import requests

from app.config.octopus_config import (
    GRAPHQL_URL,
    ACCOUNT_ID,
)

from app.octopus.api.octopus_api import get_graphql_token


SMARTFLEX_VEHICLE_ID = (
    "00000000-0002-4000-8020-000000100c8e"
)


QUERY = """
query GetDispatches($deviceId: String!) {

    flexPlannedDispatches(deviceId: $deviceId) {

        start
        end
        energyAddedKwh
        type
    }
}
"""


def main():

    token = get_graphql_token()

    response = requests.post(
        GRAPHQL_URL,
        json={
            "query": QUERY,
            "variables": {
                "deviceId": SMARTFLEX_VEHICLE_ID,
            },
        },
        headers={
            "Authorization": token,
            "Content-Type": "application/json",
        },
        timeout=30,
    )

    print("HTTP status:", response.status_code)
    print()

    data = response.json()

    if "errors" in data:

        print("=" * 100)
        print("GRAPHQL ERRORS")
        print("=" * 100)

        for error in data["errors"]:
            print(error)

        return

    dispatches = (
        data
        .get("data", {})
        .get("flexPlannedDispatches", [])
    )

    print("=" * 100)
    print(f"DISPATCHES RETURNED: {len(dispatches)}")
    print("=" * 100)

    for dispatch in dispatches:

        print()
        print(f"Start:           {dispatch.get('start')}")
        print(f"End:             {dispatch.get('end')}")
        print(f"Energy added:    {dispatch.get('energyAddedKwh')}")
        print(f"Type:             {dispatch.get('type')}")


if __name__ == "__main__":
    main()