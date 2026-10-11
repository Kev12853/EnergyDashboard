import requests
import pandas as pd

from app.connections.connection import get_connection

from app.config.octopus_config import (
    BASE_URL,
    IMPORT_MPAN,
    METER_SERIAL,
    OCTOPUS_API_KEY,
)


START_DATE = "2026-08-12"
END_DATE = "2026-08-13"


# ============================================================
# OCTOPUS
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

    df["consumption_kwh"] = pd.to_numeric(
        df["consumption"],
        errors="coerce",
    )

    df["bucket_start"] = (
        df["interval_start"]
        .dt.tz_convert("Europe/London")
        .dt.tz_localize(None)
    )

    return (
        df[
            [
                "bucket_start",
                "consumption_kwh",
            ]
        ]
        .sort_values("bucket_start")
    )


# ============================================================
# TELEMETRY 1 MINUTE
# ============================================================

def get_telemetry():

    connection = get_connection()

    try:

        df = pd.read_sql_query(
            """
            SELECT
                bucket_start,
                avg_grid_w,
                sample_count

            FROM telemetry_1m

            WHERE bucket_start >= ?
              AND bucket_start < ?

            ORDER BY bucket_start
            """,
            connection,
            params=(
                START_DATE,
                END_DATE,
            ),
        )

    finally:

        connection.close()

    if df.empty:
        raise RuntimeError(
            "No telemetry_1m data returned"
        )

    df["bucket_start"] = pd.to_datetime(
        df["bucket_start"]
    )

    df["avg_grid_w"] = pd.to_numeric(
        df["avg_grid_w"],
        errors="coerce",
    )

    # Negative grid power = import.
    #
    # W × 1 minute / 60 / 1000 = kWh

    df["import_kwh"] = (
        df["avg_grid_w"]
        .clip(upper=0)
        .abs()
        / 60
        / 1000
    )

    # Convert 1-minute energy into
    # Octopus 30-minute settlement periods.

    df = df.set_index("bucket_start")

    result = (
        df["import_kwh"]
        .resample("30min")
        .sum()
        .reset_index()
        .rename(
            columns={
                "import_kwh":
                    "telemetry_import_kwh"
            }
        )
    )

    return result


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 100)
    print("OCTOPUS vs 1-MINUTE TELEMETRY")
    print("7 AUGUST 2026")
    print("=" * 100)

    octopus = get_octopus_consumption()

    telemetry = get_telemetry()

    # ========================================================
    # MERGE
    # ========================================================

    comparison = pd.merge(
        octopus,
        telemetry,
        on="bucket_start",
        how="outer",
    )

    comparison = comparison.sort_values(
        "bucket_start"
    )

    comparison["difference_kwh"] = (
        comparison["consumption_kwh"]
        - comparison["telemetry_import_kwh"]
    )

    # ========================================================
    # 30-MINUTE COMPARISON
    # ========================================================

    print()
    print("=" * 100)
    print("30-MINUTE COMPARISON")
    print("=" * 100)

    print(
        comparison[
            [
                "bucket_start",
                "consumption_kwh",
                "telemetry_import_kwh",
                "difference_kwh",
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.5f}",
        )
    )

    # ========================================================
    # COVERAGE
    # ========================================================

    print()
    print("=" * 100)
    print("COVERAGE")
    print("=" * 100)

    print(
        f"Octopus periods : "
        f"{octopus['bucket_start'].nunique()}"
    )

    print(
        f"30-minute periods compared : "
        f"{len(comparison)}"
    )

    print(
        f"Missing Octopus periods : "
        f"{comparison['consumption_kwh'].isna().sum()}"
    )

    print(
        f"Missing telemetry periods : "
        f"{comparison['telemetry_import_kwh'].isna().sum()}"
    )

    # ========================================================
    # TOTALS
    # ========================================================

    octopus_total = (
        comparison["consumption_kwh"]
        .sum()
    )

    telemetry_total = (
        comparison["telemetry_import_kwh"]
        .sum()
    )

    difference = (
        octopus_total
        - telemetry_total
    )

    print()
    print("=" * 100)
    print("DAILY TOTALS")
    print("=" * 100)

    print(
        f"Octopus consumption : "
        f"{octopus_total:.5f} kWh"
    )

    print(
        f"Telemetry import    : "
        f"{telemetry_total:.5f} kWh"
    )

    print(
        f"Difference          : "
        f"{difference:.5f} kWh"
    )

    if octopus_total:

        print(
            f"Difference          : "
            f"{difference / octopus_total * 100:.2f}%"
        )


if __name__ == "__main__":
    main()