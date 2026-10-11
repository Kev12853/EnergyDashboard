import requests
import pandas as pd

from app.config.octopus_config import (
    BASE_URL,
    IMPORT_MPAN,
    METER_SERIAL,
    OCTOPUS_API_KEY,
)


def get_last_12_hours():

    url = (
        f"{BASE_URL}/electricity-meter-points/"
        f"{IMPORT_MPAN}/meters/{METER_SERIAL}/consumption/"
    )

    params = {
        "page_size": 100,
        "period_from": "2026-08-25",
        "period_to": "2026-08-28",
    }

    response = requests.get(
        url,
        params=params,
        auth=(OCTOPUS_API_KEY, ""),
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    results = data.get("results", [])

    if not results:
        print("No consumption data returned.")
        return

    df = pd.DataFrame(results)

    df["interval_start"] = pd.to_datetime(
        df["interval_start"],
        utc=True,
    )

    df["interval_end"] = pd.to_datetime(
        df["interval_end"],
        utc=True,
    )

    # Find the latest 24 half-hour periods
    df = (
        df
        .sort_values("interval_start")
        .tail(24)
    )

    print()
    print("=" * 100)
    print("LATEST 12 HOURS OF AVAILABLE OCTOPUS DATA")
    print("=" * 100)

    print(
        df[
            [
                "interval_start",
                "interval_end",
                "consumption",
            ]
        ].to_string(
            index=False,
        )
    )

    print()
    print("=" * 100)
    print("SUMMARY")
    print("=" * 100)

    print(
        f"Oldest period : "
        f"{df['interval_start'].iloc[0]}"
    )

    print(
        f"Newest period : "
        f"{df['interval_start'].iloc[-1]}"
    )

    print(
        f"Total energy  : "
        f"{df['consumption'].sum():.3f} kWh"
    )


if __name__ == "__main__":
    get_last_12_hours()