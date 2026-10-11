import requests
import pandas as pd

from app.octopus.costs.octopus_tariff_matching import get_tariff_for_period

from app.config.octopus_config import (
    BASE_URL,
    IMPORT_MPAN,
    METER_SERIAL,
    OCTOPUS_API_KEY,
)


# ============================================================
# DATE TO ANALYSE
# ============================================================

START_DATE = "2026-08-06"
END_DATE = "2026-08-07"


# ============================================================
# GET OCTOPUS CONSUMPTION
# ============================================================

def get_octopus_consumption():

    url = (
        f"{BASE_URL}/electricity-meter-points/"
        f"{IMPORT_MPAN}/meters/{METER_SERIAL}/consumption/"
    )

    params = {
        "page_size": 100,
        "period_from": START_DATE,
        "period_to": END_DATE,
    }

    response = requests.get(
        url,
        params=params,
        auth=(OCTOPUS_API_KEY, ""),
        timeout=30,
    )

    print(f"HTTP status: {response.status_code}")

    response.raise_for_status()

    data = response.json()

    df = pd.DataFrame(
        data.get("results", [])
    )

    if df.empty:
        raise RuntimeError(
            "No Octopus consumption data returned"
        )

    df["interval_start"] = pd.to_datetime(
        df["interval_start"],
        utc=True,
    )

    df["interval_end"] = pd.to_datetime(
        df["interval_end"],
        utc=True,
    )

    df["consumption_kwh"] = pd.to_numeric(
        df["consumption"],
        errors="coerce",
    )

    df["bucket_start"] = (
        df["interval_start"]
        .dt.tz_convert("Europe/London")
    )

    start = pd.Timestamp(
        START_DATE,
        tz="Europe/London",
    )

    end = pd.Timestamp(
        END_DATE,
        tz="Europe/London",
    )

    df = df[
        (df["bucket_start"] >= start)
        &
        (df["bucket_start"] < end)
    ]

    return (
        df[
            [
                "bucket_start",
                "interval_start",
                "interval_end",
                "consumption_kwh",
            ]
        ]
        .sort_values("bucket_start")
        .reset_index(drop=True)
    )


# ============================================================
# GET IMPORT TARIFF CODE
# ============================================================

def get_import_tariff_code():

    connection = None

    try:

        from app.connections.connection import get_connection

        connection = get_connection()

        row = connection.execute(
            """
            SELECT
                tariff_code

            FROM octopus_tariffs

            WHERE tariff_code LIKE 'E-1R-INTELLI-%'

            ORDER BY created_at DESC

            LIMIT 1
            """
        ).fetchone()

    finally:

        if connection is not None:
            connection.close()

    if row is None:
        raise RuntimeError(
            "No Intelligent import tariff found"
        )

    return row[0]


# ============================================================
# APPLY TARIFF
# ============================================================

def apply_tariff(
    consumption_df,
    tariff_code,
):

    result = consumption_df.copy()

    rates = []
    sources = []
    tariff_ids = []

    for _, row in result.iterrows():

        tariff = get_tariff_for_period(
            tariff_code=tariff_code,
            period_start=row["bucket_start"],
        )

        if tariff is None:

            rates.append(pd.NA)
            sources.append("unmatched")
            tariff_ids.append(pd.NA)

        else:

            rates.append(
                tariff["rate_p_per_kwh"]
            )

            sources.append(
                tariff["rate_source"]
            )

            tariff_ids.append(
                tariff["tariff_id"]
            )

    result["tariff_id"] = tariff_ids

    result["rate_p_per_kwh"] = pd.to_numeric(
        rates,
        errors="coerce",
    )

    result["rate_source"] = sources

    # --------------------------------------------------------
    # Energy cost only
    #
    # kWh × p/kWh ÷ 100 = £
    # --------------------------------------------------------

    result["energy_cost_gbp"] = (
        result["consumption_kwh"]
        * result["rate_p_per_kwh"]
        / 100
    )

    return result


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 110)
    print("OCTOPUS IMPORT ENERGY COST TEST")
    print(
        pd.Timestamp(START_DATE).strftime(
            "%d %B %Y"
        )
    )
    print("=" * 110)

    # --------------------------------------------------------
    # Fetch consumption
    # --------------------------------------------------------

    print()
    print("Fetching Octopus import data...")

    consumption = get_octopus_consumption()

    print(
        f"Import periods : {len(consumption)}"
    )

    # --------------------------------------------------------
    # Get tariff
    # --------------------------------------------------------

    tariff_code = get_import_tariff_code()

    print()
    print(
        f"TARIFF_CODE: '{tariff_code}'"
    )

    # --------------------------------------------------------
    # Apply tariff
    # --------------------------------------------------------

    result = apply_tariff(
        consumption,
        tariff_code,
    )

    # --------------------------------------------------------
    # 30-minute calculation
    # --------------------------------------------------------

    print()
    print("=" * 110)
    print("30-MINUTE IMPORT ENERGY COST")
    print("=" * 110)

    print(
        result[
            [
                "bucket_start",
                "consumption_kwh",
                "rate_p_per_kwh",
                "energy_cost_gbp",
                "rate_source",
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.5f}",
        )
    )

    # --------------------------------------------------------
    # Matching
    # --------------------------------------------------------

    unmatched = result[
        result["rate_p_per_kwh"].isna()
    ]

    print()
    print("=" * 110)
    print("TARIFF MATCHING")
    print("=" * 110)

    print(
        f"Periods       : {len(result)}"
    )

    print(
        f"Matched       : "
        f"{len(result) - len(unmatched)}"
    )

    print(
        f"Unmatched     : "
        f"{len(unmatched)}"
    )

    # --------------------------------------------------------
    # Daily energy total
    # --------------------------------------------------------

    total_kwh = (
        result["consumption_kwh"]
        .sum()
    )

    total_energy_cost = (
        result["energy_cost_gbp"]
        .sum()
    )

    print()
    print("=" * 110)
    print("DAILY ENERGY TOTAL")
    print("=" * 110)

    print(
        f"Consumption : "
        f"{total_kwh:.5f} kWh"
    )

    print(
        f"Energy cost : "
        f"£{total_energy_cost:.5f}"
    )

    # --------------------------------------------------------
    # Cost by rate
    # --------------------------------------------------------

    print()
    print("=" * 110)
    print("ENERGY COST BY RATE")
    print("=" * 110)

    by_rate = (
        result
        .groupby(
            "rate_p_per_kwh",
            dropna=False,
        )
        .agg(
            consumption_kwh=(
                "consumption_kwh",
                "sum",
            ),
            energy_cost_gbp=(
                "energy_cost_gbp",
                "sum",
            ),
            periods=(
                "bucket_start",
                "count",
            ),
        )
        .reset_index()
    )

    print(
        by_rate.to_string(
            index=False,
            float_format=lambda x: f"{x:.5f}",
        )
    )


if __name__ == "__main__":
    main()