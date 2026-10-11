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
# CONFIG
# ============================================================

START_DATE = "2026-07-19"
END_DATE = "2026-07-20"

TIMEZONE = "Europe/London"


# ============================================================
# OCTOPUS CONSUMPTION
# ============================================================

def get_octopus_consumption():

    url = (
        f"{BASE_URL}/electricity-meter-points/"
        f"{IMPORT_MPAN}/meters/{METER_SERIAL}/consumption/"
    )

    params = {
        "page_size": 25000,
        "period_from": START_DATE,
        "period_to": END_DATE,
    }

    print()
    print("Fetching Octopus consumption...")

    results = []

    while url:

        response = requests.get(
            url,
            params=params,
            auth=(OCTOPUS_API_KEY, ""),
            timeout=30,
        )

        response.raise_for_status()

        data = response.json()

        results.extend(
            data.get("results", [])
        )

        url = data.get("next")

        # The next URL already contains its
        # own parameters.
        params = None

    df = pd.DataFrame(results)

    if df.empty:

        print("No Octopus consumption returned.")

        return pd.DataFrame(
            columns=[
                "bucket_start",
                "octopus_import_kwh",
            ]
        )

    df["bucket_start"] = (
        pd.to_datetime(
            df["interval_start"],
            utc=True,
        )
        .dt.tz_convert(TIMEZONE)
        .dt.tz_localize(None)
    )

    df["octopus_import_kwh"] = pd.to_numeric(
        df["consumption"],
        errors="coerce",
    )

    return (
        df[
            [
                "bucket_start",
                "octopus_import_kwh",
            ]
        ]
        .sort_values("bucket_start")
    )


# ============================================================
# TELEMETRY
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

        print("No telemetry_1m data returned.")

        return pd.DataFrame(
            columns=[
                "bucket_start",
                "telemetry_import_kwh",
            ]
        )

    df["bucket_start"] = pd.to_datetime(
        df["bucket_start"]
    )

    df["avg_grid_w"] = pd.to_numeric(
        df["avg_grid_w"],
        errors="coerce",
    )

    # --------------------------------------------------------
    # Negative grid power = grid import.
    #
    # One minute:
    #
    #       W / 60 = Wh
    #
    #       Wh / 1000 = kWh
    # --------------------------------------------------------

    df["telemetry_import_kwh"] = (
        df["avg_grid_w"]
        .clip(upper=0)
        .abs()
        / 60
        / 1000
    )

    # --------------------------------------------------------
    # Aggregate the one-minute energy into exact
    # 30-minute settlement periods.
    # --------------------------------------------------------

    df = df.set_index("bucket_start")

    result = (
        df["telemetry_import_kwh"]
        .resample("30min")
        .sum()
        .reset_index()
    )

    return result


# ============================================================
# DISPATCHES FROM OUR DATABASE
# ============================================================

def get_dispatches():

    connection = get_connection()

    try:

        df = pd.read_sql_query(
            """
            SELECT
                dispatch_start,
                dispatch_end,
                scheduled_energy_kwh,
                status

            FROM octopus_dispatches

            WHERE status = 'Completed'

              AND dispatch_start < ?
              AND dispatch_end > ?

            ORDER BY dispatch_start
            """,
            connection,
            params=(
                END_DATE,
                START_DATE,
            ),
        )

    finally:

        connection.close()

    if df.empty:

        print("No completed dispatches found.")

        return pd.DataFrame(
            columns=[
                "dispatch_start",
                "dispatch_end",
                "scheduled_energy_kwh",
                "status",
            ]
        )

    df["dispatch_start"] = pd.to_datetime(
        df["dispatch_start"]
    )

    df["dispatch_end"] = pd.to_datetime(
        df["dispatch_end"]
    )

    df["scheduled_energy_kwh"] = pd.to_numeric(
        df["scheduled_energy_kwh"],
        errors="coerce",
    )

    return df.sort_values(
        "dispatch_start"
    )


# ============================================================
# ADD DISPATCH INFORMATION TO EACH 30-MINUTE PERIOD
# ============================================================

def add_dispatch_information(
    comparison,
    dispatches,
):

    comparison = comparison.copy()

    comparison["dispatch_active"] = False

    comparison["scheduled_dispatch_kwh"] = 0.0

    comparison["dispatch_status"] = ""

    for _, dispatch in dispatches.iterrows():

        dispatch_start = dispatch[
            "dispatch_start"
        ]

        dispatch_end = dispatch[
            "dispatch_end"
        ]

        settlement_end = (
            comparison["bucket_start"]
            + pd.Timedelta(minutes=30)
        )

        # A dispatch overlaps a settlement period
        # when the two time ranges overlap.
        mask = (
            (comparison["bucket_start"] < dispatch_end)
            &
            (settlement_end > dispatch_start)
        )

        comparison.loc[
            mask,
            "dispatch_active",
        ] = True

        comparison.loc[
            mask,
            "scheduled_dispatch_kwh",
        ] += dispatch[
            "scheduled_energy_kwh"
        ]

        comparison.loc[
            mask,
            "dispatch_status",
        ] = dispatch[
            "status"
        ]

    return comparison


# ============================================================
# MAIN
# ============================================================

def compare():

    telemetry = get_telemetry()

    octopus = get_octopus_consumption()

    dispatches = get_dispatches()

    # ========================================================
    # TELEMETRY COVERAGE
    # ========================================================

    connection = get_connection()

    try:

        coverage = pd.read_sql_query(
            """
            SELECT
                COUNT(*) AS minute_count,
                MIN(bucket_start) AS first_minute,
                MAX(bucket_start) AS last_minute

            FROM telemetry_1m

            WHERE bucket_start >= ?
              AND bucket_start < ?
            """,
            connection,
            params=(
                START_DATE,
                END_DATE,
            ),
        )

    finally:

        connection.close()

    print()
    print("=" * 110)
    print("TELEMETRY COVERAGE")
    print("=" * 110)

    print(
        f"Minutes recorded : "
        f"{coverage.iloc[0]['minute_count']}"
    )

    print(
        f"First minute     : "
        f"{coverage.iloc[0]['first_minute']}"
    )

    print(
        f"Last minute      : "
        f"{coverage.iloc[0]['last_minute']}"
    )

    # ========================================================
    # DISPATCHES
    # ========================================================

    print()
    print("=" * 110)
    print("COMPLETED DISPATCHES — 19 JULY 2026")
    print("=" * 110)

    if dispatches.empty:

        print("None found.")

    else:

        print(
            dispatches.to_string(
                index=False
            )
        )

    # ========================================================
    # MERGE
    # ========================================================

    comparison = pd.merge(
        telemetry,
        octopus,
        on="bucket_start",
        how="outer",
    )

    comparison = comparison.sort_values(
        "bucket_start"
    )

    # --------------------------------------------------------
    # Octopus minus telemetry
    # --------------------------------------------------------

    comparison["difference_kwh"] = (
        comparison["octopus_import_kwh"]
        - comparison["telemetry_import_kwh"]
    )

    # --------------------------------------------------------
    # Add dispatch information
    # --------------------------------------------------------

    comparison = add_dispatch_information(
        comparison,
        dispatches,
    )

    # ========================================================
    # ALL 30-MINUTE PERIODS
    # ========================================================

    print()
    print("=" * 110)
    print("19 JULY 2026 — 30-MINUTE COMPARISON")
    print("=" * 110)

    print(
        comparison[
            [
                "bucket_start",
                "telemetry_import_kwh",
                "octopus_import_kwh",
                "difference_kwh",
                "dispatch_active",
                "scheduled_dispatch_kwh",
            ]
        ].to_string(
            index=False,
            float_format=lambda x: f"{x:.5f}",
        )
    )

    # ========================================================
    # DISPATCH PERIODS ONLY
    # ========================================================

    dispatch_periods = comparison[
        comparison["dispatch_active"]
    ]

    print()
    print("=" * 110)
    print("19 JULY 2026 — DISPATCH PERIODS ONLY")
    print("=" * 110)

    if dispatch_periods.empty:

        print("No dispatch periods found.")

    else:

        print(
            dispatch_periods[
                [
                    "bucket_start",
                    "telemetry_import_kwh",
                    "octopus_import_kwh",
                    "difference_kwh",
                    "scheduled_dispatch_kwh",
                ]
            ].to_string(
                index=False,
                float_format=lambda x: f"{x:.5f}",
            )
        )

    # ========================================================
    # TOTALS
    # ========================================================

    telemetry_total = (
        comparison[
            "telemetry_import_kwh"
        ].sum()
    )

    octopus_total = (
        comparison[
            "octopus_import_kwh"
        ].sum()
    )

    difference_total = (
        comparison[
            "difference_kwh"
        ].sum()
    )

    dispatch_total = (
        dispatches[
            "scheduled_energy_kwh"
        ].sum()
        if not dispatches.empty
        else 0
    )

    print()
    print("=" * 110)
    print("19 JULY 2026 — TOTALS")
    print("=" * 110)

    print(
        f"Telemetry import       : "
        f"{telemetry_total:.5f} kWh"
    )

    print(
        f"Octopus import         : "
        f"{octopus_total:.5f} kWh"
    )

    print(
        f"Difference             : "
        f"{difference_total:.5f} kWh"
    )

    print(
        f"Scheduled dispatch     : "
        f"{dispatch_total:.5f} kWh"
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":
    compare()