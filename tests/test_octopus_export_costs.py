import requests
import pandas as pd

from app.octopus.costs.octopus_tariff_matching import get_tariff_for_period

from app.connections.connection import get_connection

from app.config.octopus_config import (
    BASE_URL,
    EXPORT_MPAN,
    METER_SERIAL,
    OCTOPUS_API_KEY,
)


# ============================================================
# DATE TO ANALYSE
# ============================================================

START_DATE = "2026-08-11"
END_DATE = "2026-08-12"


# ============================================================
# OCTOPUS EXPORT CONSUMPTION
# ============================================================

def get_octopus_export():

    url = (
        f"{BASE_URL}/electricity-meter-points/"
        f"{EXPORT_MPAN}/meters/{METER_SERIAL}/consumption/"
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

    if not response.ok:
        print()
        print("OCTOPUS ERROR RESPONSE:")
        print(response.text)

    response.raise_for_status()

    data = response.json()

    df = pd.DataFrame(
        data.get("results", [])
    )

    if df.empty:
        raise RuntimeError(
            "No Octopus export data returned"
        )

    df["interval_start"] = pd.to_datetime(
        df["interval_start"],
        utc=True,
    )

    df["interval_end"] = pd.to_datetime(
        df["interval_end"],
        utc=True,
    )

    df["export_kwh"] = pd.to_numeric(
        df["consumption"],
        errors="coerce",
    )

    # Keep the Octopus timestamp timezone-aware.
    # The tariff matcher will convert it to UTC.

    df["bucket_start"] = (
        df["interval_start"]
        .dt.tz_convert("Europe/London")
    )

    # Keep exactly the requested UK local day.

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
                "export_kwh",
            ]
        ]
        .sort_values("bucket_start")
        .reset_index(drop=True)
    )


# ============================================================
# GET EXPORT TARIFF CODE
# ============================================================

def get_export_tariff_code():

    connection = None

    try:

        connection = get_connection()

        # Find the most recently stored export tariff.

        row = connection.execute(
            """
            SELECT
                tariff_code

            FROM octopus_tariffs

            WHERE tariff_code LIKE 'E-1R-OUTGOING-%'

            ORDER BY created_at DESC

            LIMIT 1
            """
        ).fetchone()

    finally:

        if connection is not None:
            connection.close()

    if row is None:
        raise RuntimeError(
            "No export tariff found"
        )

    return row[0]


# ============================================================
# APPLY EXPORT TARIFF
# ============================================================

def apply_export_tariffs(
    export_df,
    tariff_code,
):

    result = export_df.copy()

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

    # pence/kWh -> pounds

    result["payment_gbp"] = (
        result["export_kwh"]
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
    print("OCTOPUS EXPORT COST TEST")
    print(
        pd.Timestamp(START_DATE).strftime(
            "%d %B %Y"
        )
    )
    print("=" * 110)

    # --------------------------------------------------------
    # Get export data
    # --------------------------------------------------------

    print()
    print("Fetching Octopus export data...")

    export = get_octopus_export()

    print(
        f"Octopus periods : {len(export)}"
    )

    if not export.empty:

        print(
            f"First period    : "
            f"{export['bucket_start'].iloc[0]}"
        )

        print(
            f"Last period     : "
            f"{export['bucket_start'].iloc[-1]}"
        )

    # --------------------------------------------------------
    # Get tariff code
    # --------------------------------------------------------

    tariff_code = get_export_tariff_code()

    print()
    print(
        f"TARIFF_CODE: '{tariff_code}'"
    )

    # --------------------------------------------------------
    # Apply tariff matching
    # --------------------------------------------------------

    result = apply_export_tariffs(
        export,
        tariff_code,
    )

    # --------------------------------------------------------
    # 30-minute payment
    # --------------------------------------------------------

    print()
    print("=" * 110)
    print("30-MINUTE EXPORT PAYMENT")
    print("=" * 110)

    print(
        result[
            [
                "bucket_start",
                "export_kwh",
                "rate_p_per_kwh",
                "payment_gbp",
                "rate_source",
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.5f}",
        )
    )

    # --------------------------------------------------------
    # Matching statistics
    # --------------------------------------------------------

    unmatched = result[
        result["rate_p_per_kwh"].isna()
    ]

    recorded = result[
        result["rate_source"] == "recorded"
    ]

    fallback = result[
        result["rate_source"]
        == "historical_fallback"
    ]

    print()
    print("=" * 110)
    print("TARIFF MATCHING")
    print("=" * 110)

    print(
        f"Periods          : {len(result)}"
    )

    print(
        f"Matched          : "
        f"{len(result) - len(unmatched)}"
    )

    print(
        f"Unmatched        : "
        f"{len(unmatched)}"
    )

    print(
        f"Recorded rates   : "
        f"{len(recorded)}"
    )

    print(
        f"Fallback rates   : "
        f"{len(fallback)}"
    )

    if not unmatched.empty:

        print()
        print("UNMATCHED PERIODS")

        print(
            unmatched[
                [
                    "bucket_start",
                    "export_kwh",
                ]
            ].to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # Daily total
    # --------------------------------------------------------

    total_kwh = (
        result["export_kwh"]
        .sum()
    )

    total_payment = (
        result["payment_gbp"]
        .sum()
    )

    print()
    print("=" * 110)
    print("DAILY TOTAL")
    print("=" * 110)

    print(
        f"Export   : "
        f"{total_kwh:.5f} kWh"
    )

    print(
        f"Payment  : "
        f"£{total_payment:.5f}"
    )

    # --------------------------------------------------------
    # Payment by rate
    # --------------------------------------------------------

    print()
    print("=" * 110)
    print("PAYMENT BY RATE")
    print("=" * 110)

    by_rate = (
        result
        .groupby(
            "rate_p_per_kwh",
            dropna=False,
        )
        .agg(
            export_kwh=(
                "export_kwh",
                "sum",
            ),
            payment_gbp=(
                "payment_gbp",
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

    # --------------------------------------------------------
    # Coverage
    # --------------------------------------------------------

    print()
    print("=" * 110)
    print("COVERAGE")
    print("=" * 110)

    print(
        f"Export periods : {len(result)}"
    )

    print(
        f"Expected       : 48"
    )


if __name__ == "__main__":
    main()