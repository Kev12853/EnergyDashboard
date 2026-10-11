import requests
import pandas as pd

from app.connections.connection import get_connection

from app.config.octopus_config import (
    BASE_URL,
    IMPORT_MPAN,
    METER_SERIAL,
    OCTOPUS_API_KEY,
)


# ============================================================
# DATE TO ANALYSE
# ============================================================

START_DATE = "2026-08-11"
END_DATE = "2026-08-12"


# ============================================================
# OCTOPUS CONSUMPTION
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

    # Convert Octopus UTC timestamps to UK local time.
    df["bucket_start"] = (
        df["interval_start"]
        .dt.tz_convert("Europe/London")
        .dt.tz_localize(None)
    )

    # Keep exactly the requested local day.

    df = df[
        (df["bucket_start"] >= START_DATE)
        &
        (df["bucket_start"] < END_DATE)
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
# GET CURRENT IMPORT TARIFF
# ============================================================

def get_import_tariffs():

    connection = get_connection()

    try:

        # Find the current import tariff code.

        row = connection.execute(
            """
            SELECT
                tariff_code

            FROM octopus_tariffs

            WHERE tariff_code LIKE 'E-1R-INTELLI-%'

            ORDER BY
                created_at DESC

            LIMIT 1
            """
        ).fetchone()

        if row is None:
            raise RuntimeError(
                "No Intelligent import tariff found"
            )

        tariff_code = row[0]

        print()
        print(
            f"Import tariff: {tariff_code}"
        )

        # Get all stored rows for this tariff.

        df = pd.read_sql_query(
            """
            SELECT
                id,
                tariff_code,
                value_exc_vat,
                value_inc_vat,
                valid_from,
                valid_to,
                payment_method,
                created_at

            FROM octopus_tariffs

            WHERE tariff_code = ?

            ORDER BY valid_from
            """,
            connection,
            params=(tariff_code,),
        )

    finally:

        connection.close()

    if df.empty:
        raise RuntimeError(
            f"No tariff rows found for {tariff_code}"
        )

    df["valid_from"] = pd.to_datetime(
        df["valid_from"],
        utc=True,
    )

    df["valid_to"] = pd.to_datetime(
        df["valid_to"],
        utc=True,
    )

    df["value_inc_vat"] = pd.to_numeric(
        df["value_inc_vat"],
        errors="coerce",
    )

    return df


# ============================================================
# DISPLAY TARIFF SCHEDULE
# ============================================================

def print_tariff_schedule(tariff_df):

    print()
    print("=" * 110)
    print("STORED IMPORT TARIFF SCHEDULE")
    print("=" * 110)

    for _, tariff in tariff_df.iterrows():

        start_utc = tariff["valid_from"]
        end_utc = tariff["valid_to"]

        start_local = (
            start_utc
            .tz_convert("Europe/London")
        )

        if pd.isna(end_utc):

            end_local = None

        else:

            end_local = (
                end_utc
                .tz_convert("Europe/London")
            )

        print()
        print(f"ID          : {tariff['id']}")
        print(f"Rate        : {tariff['value_inc_vat']:.5f} p/kWh")
        print(f"UTC         : {start_utc} -> {end_utc}")
        print(
            f"UK time     : "
            f"{start_local} -> {end_local}"
        )


# ============================================================
# APPLY RECURRING TIME-OF-DAY TARIFF
# ============================================================

def apply_tariffs(
    consumption_df,
    tariff_df,
):

    result = consumption_df.copy()

    result["rate_p_per_kwh"] = pd.NA

    # Consumption bucket expressed in UTC.

    result["period_start_utc"] = (
        result["bucket_start"]
        .dt.tz_localize("Europe/London")
        .dt.tz_convert("UTC")
    )

    period_time = (
        result["period_start_utc"]
        .dt.strftime("%H:%M")
    )

    # --------------------------------------------------------
    # Each tariff row represents a recurring time period.
    # We deliberately ignore its calendar date.
    # --------------------------------------------------------

    for _, tariff in tariff_df.iterrows():

        start_time = (
            tariff["valid_from"]
            .strftime("%H:%M")
        )

        if pd.isna(tariff["valid_to"]):

            # Open-ended tariff.

            mask = (
                period_time >= start_time
            )

        else:

            end_time = (
                tariff["valid_to"]
                .strftime("%H:%M")
            )

            # Normal period, e.g. 04:30 -> 22:30.

            if start_time < end_time:

                mask = (
                    (period_time >= start_time)
                    &
                    (period_time < end_time)
                )

            # Period crossing midnight,
            # e.g. 22:30 -> 04:30.

            else:

                mask = (
                    (period_time >= start_time)
                    |
                    (period_time < end_time)
                )

        result.loc[
            mask,
            "rate_p_per_kwh",
        ] = tariff["value_inc_vat"]

    # Convert rate to numeric.

    result["rate_p_per_kwh"] = pd.to_numeric(
        result["rate_p_per_kwh"],
        errors="coerce",
    )

    # Calculate cost.

    result["cost_gbp"] = (
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
    print("OCTOPUS COST ANALYSIS")
    print(
        pd.Timestamp(START_DATE).strftime("%d %B %Y")
    )
    print("=" * 110)

    # --------------------------------------------------------
    # Get data
    # --------------------------------------------------------

    consumption = get_octopus_consumption()

    tariffs = get_import_tariffs()

    print_tariff_schedule(tariffs)

    # --------------------------------------------------------
    # Apply tariff
    # --------------------------------------------------------

    result = apply_tariffs(
        consumption,
        tariffs,
    )

    # --------------------------------------------------------
    # 30-minute costs
    # --------------------------------------------------------

    print()
    print("=" * 110)
    print("30-MINUTE COST ANALYSIS")
    print("=" * 110)

    print(
        result[
            [
                "bucket_start",
                "consumption_kwh",
                "rate_p_per_kwh",
                "cost_gbp",
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

    if not unmatched.empty:

        print()
        print("UNMATCHED PERIODS")

        print(
            unmatched[
                [
                    "bucket_start",
                    "consumption_kwh",
                ]
            ].to_string(
                index=False
            )
        )

    # --------------------------------------------------------
    # Totals
    # --------------------------------------------------------

    total_kwh = (
        result["consumption_kwh"]
        .sum()
    )

    total_cost = (
        result["cost_gbp"]
        .sum()
    )

    print()
    print("=" * 110)
    print("DAILY TOTAL")
    print("=" * 110)

    print(
        f"Consumption : "
        f"{total_kwh:.5f} kWh"
    )

    print(
        f"Energy cost : "
        f"£{total_cost:.5f}"
    )

    # --------------------------------------------------------
    # Cost by rate
    # --------------------------------------------------------

    print()
    print("=" * 110)
    print("COST BY RATE")
    print("=" * 110)

    by_rate = (
        result
        .groupby("rate_p_per_kwh", dropna=False)
        .agg(
            consumption_kwh=(
                "consumption_kwh",
                "sum",
            ),
            cost_gbp=(
                "cost_gbp",
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