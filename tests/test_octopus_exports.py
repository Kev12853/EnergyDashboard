import requests
import pandas as pd

from app.connections.connection import get_connection

from app.config.octopus_config import (
    BASE_URL,
    EXPORT_MPAN,
    METER_SERIAL,
    OCTOPUS_API_KEY,
)


START_DATE = "2026-08-11"
END_DATE = "2026-08-12"


# ============================================================
# GET OCTOPUS EXPORT CONSUMPTION
# ============================================================

def get_octopus_exports():

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

    print()
    print("HTTP status:", response.status_code)

    response.raise_for_status()

    data = response.json()

    df = pd.DataFrame(
        data.get("results", [])
    )

    if df.empty:
        raise RuntimeError(
            "No Octopus export consumption data returned"
        )

    df["interval_start"] = pd.to_datetime(
        df["interval_start"],
        utc=True,
    )

    df["consumption_kwh"] = pd.to_numeric(
        df["consumption"],
        errors="coerce",
    )

    # Convert to UK local time.

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
                "consumption_kwh",
            ]
        ]
        .sort_values("bucket_start")
        .reset_index(drop=True)
    )


# ============================================================
# GET EXPORT TARIFF
# ============================================================

def get_export_tariff():

    connection = get_connection()

    try:

        df = pd.read_sql_query(
            """
            SELECT
                id,
                tariff_code,
                value_exc_vat,
                value_inc_vat,
                valid_from,
                valid_to

            FROM octopus_tariffs

            WHERE tariff_code LIKE 'E-1R-OUTGOING-%'

            ORDER BY created_at DESC

            LIMIT 1
            """,
            connection,
        )

    finally:

        connection.close()

    if df.empty:
        raise RuntimeError(
            "No export tariff found"
        )

    return df.iloc[0]


# ============================================================
# CALCULATE EXPORT PAYMENT
# ============================================================

def calculate_export_payment(
    consumption,
    tariff,
):

    result = consumption.copy()

    result["rate_p_per_kwh"] = (
        tariff["value_inc_vat"]
    )

    result["payment_gbp"] = (
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
    print("=" * 100)
    print("OCTOPUS EXPORT ANALYSIS")
    print(
        pd.Timestamp(START_DATE).strftime(
            "%d %B %Y"
        )
    )
    print("=" * 100)

    # --------------------------------------------------------
    # Export consumption
    # --------------------------------------------------------

    exports = get_octopus_exports()

    print()
    print("=" * 100)
    print("OCTOPUS EXPORT CONSUMPTION")
    print("=" * 100)

    print(
        exports.to_string(
            index=False,
            float_format=lambda x: f"{x:.5f}",
        )
    )

    # --------------------------------------------------------
    # Export tariff
    # --------------------------------------------------------

    tariff = get_export_tariff()

    print()
    print("=" * 100)
    print("EXPORT TARIFF")
    print("=" * 100)

    print(
        f"Tariff code : {tariff['tariff_code']}"
    )

    print(
        f"Rate        : "
        f"{tariff['value_inc_vat']:.5f} p/kWh"
    )

    # --------------------------------------------------------
    # Calculate payment
    # --------------------------------------------------------

    result = calculate_export_payment(
        exports,
        tariff,
    )

    print()
    print("=" * 100)
    print("30-MINUTE EXPORT PAYMENT")
    print("=" * 100)

    print(
        result[
            [
                "bucket_start",
                "consumption_kwh",
                "rate_p_per_kwh",
                "payment_gbp",
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.5f}",
        )
    )

    # --------------------------------------------------------
    # Daily total
    # --------------------------------------------------------

    total_kwh = (
        result["consumption_kwh"]
        .sum()
    )

    total_payment = (
        result["payment_gbp"]
        .sum()
    )

    print()
    print("=" * 100)
    print("DAILY TOTAL")
    print("=" * 100)

    print(
        f"Export : {total_kwh:.5f} kWh"
    )

    print(
        f"Payment: £{total_payment:.5f}"
    )


if __name__ == "__main__":
    main()