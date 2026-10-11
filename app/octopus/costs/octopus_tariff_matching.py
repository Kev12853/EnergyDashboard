from datetime import datetime, time, timezone

from app.connections.connection import get_connection

FOUR_RATE_BUCKET_TYPES = {
    "CONSUMPTION_CHARGE_ECO7_DAY_A": "DAY",
    "CONSUMPTION_CHARGE_ECO7_NIGHT_A": "NIGHT",
    "CONSUMPTION_CHARGE_EV_DEVICE_PEAK_A": "EV_DEVICE_PEAK",
    "CONSUMPTION_CHARGE_EV_DEVICE_OFF_PEAK_A": "EV_DEVICE_OFF_PEAK",
}


def _time_in_interval(
    target: time,
    start: time,
    end: time | None,
) -> bool:
    """
    Return True when target falls within a tariff time interval.

    Handles intervals that cross midnight, such as:
        22:30 -> 04:30
    """

    if end is None:
        return target >= start

    if start < end:
        return start <= target < end

    # Interval crosses midnight.
    return target >= start or target < end


def get_tariff_for_period(
    tariff_code: str,
    period_start: datetime,
    include_vat: bool = True,
) -> dict | None:
    """
    Find the tariff applicable to a specific period.

    1. Use an actual tariff record if one covers the date/time.
    2. If no historical record covers the date, find the earliest
       tariff record that existed at or before the requested date
       and whose TIME SLOT contains the requested UTC time.

    Returns:
        {
            "tariff_id": int,
            "rate_p_per_kwh": float,
            "rate_source": "recorded" | "historical_fallback",
        }

    Returns None if no tariff exists.
    """

    if period_start.tzinfo is None:
        raise ValueError(
            "period_start must be timezone-aware"
        )

    period_utc = period_start.astimezone(timezone.utc)

    period_iso = (
        period_utc
        .isoformat()
        .replace("+00:00", "Z")
    )

    target_time = period_utc.time().replace(
        tzinfo=None
    )

    conn = get_connection()

    try:

        # ==========================================================
        # 1. Exact historical match
        # ==========================================================

        row = conn.execute(
            """
            SELECT
                id,
                value_inc_vat,
                value_exc_vat
            FROM octopus_tariffs
            WHERE
                tariff_code = ?
                AND valid_from <= ?
                AND (
                    valid_to IS NULL
                    OR valid_to > ?
                )
            ORDER BY valid_from DESC
            LIMIT 1
            """,
            (
                tariff_code,
                period_iso,
                period_iso,
            ),
        ).fetchone()

        if row is not None:

            return {
                "tariff_id": row["id"],
                "rate_p_per_kwh": (
                    row["value_inc_vat"] if include_vat else row["value_exc_vat"]
                ),
                "rate_source": "recorded",
            }

        # ==========================================================
        # 2. Historical fallback
        #
        #    Only consider tariff records that existed at or before
        #    the date being analysed.
        # ==========================================================

        rows = conn.execute(
            """
            SELECT
                id,
                value_inc_vat,
                value_exc_vat,
                valid_from,
                valid_to
            FROM octopus_tariffs
            WHERE
                tariff_code = ?
                AND valid_from <= ?
            ORDER BY
                valid_from DESC
            """,
            (
                tariff_code,
                period_iso,
            ),
        ).fetchall()

        for row in rows:

            valid_from = datetime.fromisoformat(
                row["valid_from"].replace(
                    "Z",
                    "+00:00",
                )
            ).astimezone(timezone.utc)

            if row["valid_to"] is None:

                valid_to = None

            else:

                valid_to = datetime.fromisoformat(
                    row["valid_to"].replace(
                        "Z",
                        "+00:00",
                    )
                ).astimezone(timezone.utc)

            start_time = valid_from.time().replace(
                tzinfo=None
            )

            end_time = (
                valid_to.time().replace(
                    tzinfo=None
                )
                if valid_to is not None
                else None
            )

            if _time_in_interval(
                target_time,
                start_time,
                end_time,
            ):

                return {
                    "tariff_id": row["id"],
                    "rate_p_per_kwh": (
                        row["value_inc_vat"] if include_vat else row["value_exc_vat"]
                    ),
                    "rate_source": "historical_fallback",
                }

        return None

    finally:
        conn.close()

def get_tariffs_for_period(
    tariff_code: str,
    period_start: datetime,
    period_end: datetime,
    include_vat: bool = True,
) -> list[dict]:
    """Load tariff periods relevant to an analysis period in one DB query."""
    if period_start.tzinfo is None or period_end.tzinfo is None:
        raise ValueError("period_start and period_end must be timezone-aware")
    if period_end <= period_start:
        raise ValueError("period_end must be after period_start")

    start_iso = period_start.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    end_iso = period_end.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT id, value_inc_vat, value_exc_vat, valid_from, valid_to
            FROM octopus_tariffs
            WHERE tariff_code = ?
              AND valid_from < ?
              AND (valid_to IS NULL OR valid_to > ?)
            ORDER BY valid_from DESC
            """,
            (tariff_code, end_iso, start_iso),
        ).fetchall()
    finally:
        conn.close()

    return [
        {
            "tariff_id": row["id"],
            "rate_p_per_kwh": row["value_inc_vat"] if include_vat else row["value_exc_vat"],
            "valid_from": row["valid_from"],
            "valid_to": row["valid_to"],
        }
        for row in rows
    ]


def match_tariff_from_periods(
    tariffs: list[dict],
    period_start: datetime,
    include_vat: bool = True,
) -> dict | None:
    """Match a period against tariff records already loaded in memory."""
    if period_start.tzinfo is None:
        raise ValueError("period_start must be timezone-aware")

    period_utc = period_start.astimezone(timezone.utc)
    period_iso = period_utc.isoformat().replace("+00:00", "Z")
    target_time = period_utc.time().replace(tzinfo=None)

    for tariff in tariffs:
        valid_from = datetime.fromisoformat(
            tariff["valid_from"].replace("Z", "+00:00")
        ).astimezone(timezone.utc)
        if valid_from.isoformat().replace("+00:00", "Z") > period_iso:
            continue

        if tariff["valid_to"] is not None:
            valid_to = datetime.fromisoformat(
                tariff["valid_to"].replace("Z", "+00:00")
            ).astimezone(timezone.utc)
            if valid_to.isoformat().replace("+00:00", "Z") <= period_iso:
                continue

        result = tariff.copy()
        result["rate_source"] = "recorded"
        return result

    for tariff in tariffs:
        valid_from = datetime.fromisoformat(
            tariff["valid_from"].replace("Z", "+00:00")
        ).astimezone(timezone.utc)
        if valid_from.isoformat().replace("+00:00", "Z") > period_iso:
            continue

        valid_to = None if tariff["valid_to"] is None else datetime.fromisoformat(
            tariff["valid_to"].replace("Z", "+00:00")
        ).astimezone(timezone.utc)

        start_time = valid_from.time().replace(tzinfo=None)
        end_time = None if valid_to is None else valid_to.time().replace(tzinfo=None)

        if _time_in_interval(target_time, start_time, end_time):
            result = tariff.copy()
            result["rate_source"] = "historical_fallback"
            return result

    return None


def get_four_rate_tariffs_for_period(
    tariff_code: str,
    period_start: datetime,
    period_end: datetime,
    include_vat: bool = True,
) -> list[dict]:
    """Load four-rate tariff periods relevant to an analysis period."""

    if period_start.tzinfo is None or period_end.tzinfo is None:
        raise ValueError("period_start and period_end must be timezone-aware")

    if period_end <= period_start:
        raise ValueError("period_end must be after period_start")

    start_iso = (
        period_start
        .astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )

    end_iso = (
        period_end
        .astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )

    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT
                id,
                rate_type,
                value_inc_vat,
                value_exc_vat,
                valid_from,
                valid_to
            FROM octopus_four_rate_tariffs
            WHERE tariff_code = ?
              AND valid_from < ?
              AND (valid_to IS NULL OR valid_to > ?)
            ORDER BY valid_from DESC
            """,
            (
                tariff_code,
                end_iso,
                start_iso,
            ),
        ).fetchall()

    finally:
        conn.close()

    return [
        {
            "tariff_id": row["id"],
            "rate_type": row["rate_type"],
            "rate_p_per_kwh": (
                row["value_inc_vat"]
                if include_vat
                else row["value_exc_vat"]
            ),
            "valid_from": row["valid_from"],
            "valid_to": row["valid_to"],
        }
        for row in rows
    ]


def match_four_rate_tariff_from_periods(
    tariffs: list[dict],
    period_start: datetime,
    rate_type: str,
    include_vat: bool = True,
) -> dict | None:
    """Match a four-rate tariff against a period and rate type."""

    if period_start.tzinfo is None:
        raise ValueError("period_start must be timezone-aware")

    period_utc = period_start.astimezone(timezone.utc)
    period_iso = period_utc.isoformat().replace("+00:00", "Z")

    for tariff in tariffs:

        if tariff["rate_type"] != rate_type:
            continue

        valid_from = datetime.fromisoformat(
            tariff["valid_from"].replace("Z", "+00:00")
        ).astimezone(timezone.utc)

        if valid_from.isoformat().replace("+00:00", "Z") > period_iso:
            continue

        if tariff["valid_to"] is not None:
            valid_to = datetime.fromisoformat(
                tariff["valid_to"].replace("Z", "+00:00")
            ).astimezone(timezone.utc)

            if valid_to.isoformat().replace("+00:00", "Z") <= period_iso:
                continue

        result = tariff.copy()
        result["rate_source"] = "recorded"

        return result

    return None

# import pandas as pd
#
# from app.octopus.storage.repository import OctopusRepository
# from app.octopus.costs.octopus_cost_analysis import (
#     calculate_smart_flex_savings,
# )
#
# repository = OctopusRepository()
#
# costs = repository.get_octopus_consumption_costs(
#     period_from="2026-09-10T00:00:00",
#     period_to="2026-09-15T00:00:00",
# )
#
# costs["cost_excl_vat_gbp"] = costs["cost_excl_vat_p"] / 100
#
#
#
# tariff_code = "E-1R-IOG-SMB-FIX-12M-26-04-18-A"
#
# result = calculate_smart_flex_savings(
#     costs=costs,
#     tariff_code=tariff_code,
# )
#
# print(
#     result[
#         [
#             "interval_start",
#             "consumption_kwh",
#             "tou_bucket",
#             "normal_rate_p_per_kwh",
#             "normal_cost_gbp",
#             "actual_cost_gbp",
#             "smart_flex_saving_gbp",
#         ]
#     ].to_string(index=False)
# )
#
# print("\nTOTALS")
#
# print("Consumption:", result["consumption_kwh"].sum())
# print("Normal cost:", result["normal_cost_gbp"].sum())
# print("Actual cost:", result["actual_cost_gbp"].sum())
# print("Saving:", result["smart_flex_saving_gbp"].sum())