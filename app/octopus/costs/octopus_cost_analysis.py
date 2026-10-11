import pandas as pd

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from app.config.octopus_config import TIMEZONE
from app.octopus.costs.octopus_tariff_matching import (
    get_tariffs_for_period,
    match_tariff_from_periods,
    get_four_rate_tariffs_for_period,
    FOUR_RATE_BUCKET_TYPES,
    match_four_rate_tariff_from_periods,
)

def calculate_octopus_actual_costs(
    costs: pd.DataFrame,
) -> pd.DataFrame:
    """
    Prepare Octopus actual consumption costs for analysis.

    The source data contains costs in pence.
    This adds equivalent GBP columns without changing
    the original values.
    """

    if costs.empty:
        return costs.copy()

    result = costs.copy()

    result["cost_excl_vat_gbp"] = (
        result["cost_excl_vat_p"] / 100
    )

    result["cost_incl_vat_gbp"] = (
        result["cost_incl_vat_p"] / 100
    )

    return result

def summarise_octopus_actual_costs(
    costs: pd.DataFrame,
) -> dict:
    """
    Summarise Octopus actual consumption costs.

    Costs in the source DataFrame are stored in pence.
    """

    if costs.empty:
        return {
            "consumption_kwh": 0.0,
            "cost_excl_vat_p": 0.0,
            "cost_incl_vat_p": 0.0,
            "cost_excl_vat_gbp": 0.0,
            "cost_incl_vat_gbp": 0.0,
            "average_rate_p_per_kwh": 0.0,
        }

    consumption_kwh = costs["consumption_kwh"].sum()
    cost_excl_vat_p = costs["cost_excl_vat_p"].sum()
    cost_incl_vat_p = costs["cost_incl_vat_p"].sum()

    if consumption_kwh:
        average_rate_p_per_kwh = (
            cost_excl_vat_p / consumption_kwh
        )
    else:
        average_rate_p_per_kwh = 0.0

    return {
        "consumption_kwh": consumption_kwh,
        "cost_excl_vat_p": cost_excl_vat_p,
        "cost_incl_vat_p": cost_incl_vat_p,
        "cost_excl_vat_gbp": cost_excl_vat_p / 100,
        "cost_incl_vat_gbp": cost_incl_vat_p / 100,
        "average_rate_p_per_kwh": average_rate_p_per_kwh,
    }


def calculate_smart_flex_savings(
    costs: pd.DataFrame,
    tariff_code: str,
) -> pd.DataFrame:
    """
    Compare Octopus actual costs with the normal tariff cost.

    The actual cost comes from octopus_consumption_costs.
    Normal tariff periods are loaded once for the complete analysis period
    and individual consumption intervals are then matched in memory.
    """

    if costs.empty:
        return costs.copy()

    result = costs.copy()

    period_starts = result["interval_start"]
    period_ends = result["interval_end"]

    analysis_start = period_starts.min().tz_localize(TIMEZONE).to_pydatetime()
    analysis_end = period_ends.max().tz_localize(TIMEZONE).to_pydatetime()

    four_rate_tariffs = get_four_rate_tariffs_for_period(
        tariff_code=tariff_code,
        period_start=analysis_start,
        period_end=analysis_end,
        include_vat=False,
    )

    tariffs = []

    if not four_rate_tariffs:
        tariffs = get_tariffs_for_period(
            tariff_code=tariff_code,
            period_start=analysis_start,
            period_end=analysis_end,
            include_vat=False,
        )

    normal_rates = []
    normal_costs = []

    for _, row in result.iterrows():
        period_start = row["interval_start"].tz_localize(TIMEZONE).to_pydatetime()

        tou_bucket = row["tou_bucket"]

        if four_rate_tariffs:
            rate_type = FOUR_RATE_BUCKET_TYPES.get(tou_bucket)

            if rate_type is None:
                normal_rates.append(pd.NA)
                normal_costs.append(pd.NA)
                continue

            tariff = match_four_rate_tariff_from_periods(
                tariffs=four_rate_tariffs,
                period_start=period_start,
                rate_type=rate_type,
                include_vat=False,
            )

        else:
            tariff = match_tariff_from_periods(
                tariffs=tariffs,
                period_start=period_start,
                include_vat=False,
            )

        if tariff is None:
            normal_rates.append(pd.NA)
            normal_costs.append(pd.NA)
            continue

        normal_rate = tariff["rate_p_per_kwh"]
        normal_cost = row["consumption_kwh"] * normal_rate / 100

        normal_rates.append(normal_rate)
        normal_costs.append(normal_cost)

    result["normal_rate_p_per_kwh"] = normal_rates
    result["normal_cost_gbp"] = normal_costs
    result["actual_cost_gbp"] = result["cost_excl_vat_gbp"]
    result["smart_flex_saving_gbp"] = (
        result["normal_cost_gbp"] - result["actual_cost_gbp"]
    )

    return result


def summarise_smart_flex_savings(
    savings: pd.DataFrame,
) -> dict:
    """
    Summarise Smart Flex savings for a period.

    Costs are stored/calculated in GBP.
    """

    if savings.empty:
        return {
            "consumption_kwh": 0.0,
            "normal_cost_gbp": 0.0,
            "actual_cost_gbp": 0.0,
            "smart_flex_saving_gbp": 0.0,
        }

    return {
        "consumption_kwh": savings["consumption_kwh"].sum(),
        "normal_cost_gbp": savings["normal_cost_gbp"].sum(),
        "actual_cost_gbp": savings["actual_cost_gbp"].sum(),
        "smart_flex_saving_gbp": savings["smart_flex_saving_gbp"].sum(),
    }


def summarise_smart_flex_savings_daily(savings):
    """
    Aggregate Smart Flex interval savings into daily totals.

    The input must contain the interval-level results produced by
    calculate_smart_flex_savings().
    """

    if savings.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "consumption_kwh",
                "normal_cost_gbp",
                "actual_cost_gbp",
                "smart_flex_saving_gbp",
                "average_normal_rate_p_per_kwh",
                "average_actual_rate_p_per_kwh",
            ]
        )

    df = savings.copy()

    # interval_start is already stored as UK local time
    df["date"] = pd.to_datetime(df["interval_start"]).dt.date

    daily = (
        df.groupby("date", as_index=False)
        .agg(
            consumption_kwh=("consumption_kwh", "sum"),
            normal_cost_gbp=("normal_cost_gbp", "sum"),
            actual_cost_gbp=("actual_cost_gbp", "sum"),
            smart_flex_saving_gbp=("smart_flex_saving_gbp", "sum"),
        )
    )

    # Calculate weighted average rates from the daily totals.
    daily["average_normal_rate_p_per_kwh"] = (
        daily["normal_cost_gbp"]
        / daily["consumption_kwh"]
        * 100
    )

    daily["average_actual_rate_p_per_kwh"] = (
        daily["actual_cost_gbp"]
        / daily["consumption_kwh"]
        * 100
    )

    return daily

def summarise_smart_flex_savings_range(daily):
    """
    Summarise daily Smart Flex results across the selected date range.
    """

    if daily.empty:
        return {
            "consumption_kwh": 0.0,
            "normal_cost_gbp": 0.0,
            "actual_cost_gbp": 0.0,
            "smart_flex_saving_gbp": 0.0,
            "average_normal_rate_p_per_kwh": 0.0,
            "average_actual_rate_p_per_kwh": 0.0,
            "saving_percentage": 0.0,
            "average_daily_saving_gbp": 0.0,
            "days": 0,
        }

    consumption_kwh = daily["consumption_kwh"].sum()
    normal_cost_gbp = daily["normal_cost_gbp"].sum()
    actual_cost_gbp = daily["actual_cost_gbp"].sum()
    smart_flex_saving_gbp = daily["smart_flex_saving_gbp"].sum()

    average_normal_rate_p_per_kwh = (
        normal_cost_gbp / consumption_kwh * 100
        if consumption_kwh
        else 0.0
    )

    average_actual_rate_p_per_kwh = (
        actual_cost_gbp / consumption_kwh * 100
        if consumption_kwh
        else 0.0
    )

    saving_percentage = (
        smart_flex_saving_gbp / normal_cost_gbp * 100
        if normal_cost_gbp
        else 0.0
    )

    average_daily_saving_gbp = (
        smart_flex_saving_gbp / len(daily)
        if len(daily)
        else 0.0
    )

    return {
        "consumption_kwh": consumption_kwh,
        "normal_cost_gbp": normal_cost_gbp,
        "actual_cost_gbp": actual_cost_gbp,
        "smart_flex_saving_gbp": smart_flex_saving_gbp,
        "average_normal_rate_p_per_kwh": average_normal_rate_p_per_kwh,
        "average_actual_rate_p_per_kwh": average_actual_rate_p_per_kwh,
        "saving_percentage": saving_percentage,
        "average_daily_saving_gbp": average_daily_saving_gbp,
        "days": len(daily),
    }

def get_daily_smart_flex_summary(
    repository,
    tariff_code: str,
    summary_date: date | None = None,
) -> dict:
    """
    Return the Smart Flex cost summary for one local calendar day.

    Costs are compared excluding VAT, consistent with the existing
    Smart Flex analysis.
    """

    tz = ZoneInfo(TIMEZONE)

    if summary_date is None:
        summary_date = datetime.now(tz).date()

    day_start = datetime.combine(
        summary_date,
        datetime.min.time(),
        tzinfo=tz,
    )

    day_end = day_start + timedelta(days=1)

    # Database timestamps are stored as local, timezone-naive values.
    costs = repository.get_octopus_consumption_costs(
        period_from=day_start.replace(tzinfo=None).isoformat(),
        period_to=day_end.replace(tzinfo=None).isoformat(),
    )

    if costs.empty:
        return {
            "date": summary_date,
            "consumption_kwh": 0.0,
            "actual_cost_gbp": 0.0,
            "normal_cost_gbp": 0.0,
            "smart_flex_saving_gbp": 0.0,
            "saving_percentage": 0.0,
        }

    # Add actual GBP costs.
    actual_costs = calculate_octopus_actual_costs(costs)

    # Load all tariff periods needed for this day once.
    tariffs = get_tariffs_for_period(
        tariff_code=tariff_code,
        period_start=day_start,
        period_end=day_end,
        include_vat=False,
    )

    result = actual_costs.copy()

    normal_costs = []

    for _, row in result.iterrows():

        period_start = row["interval_start"].replace(
            tzinfo=tz
        )

        tariff = match_tariff_from_periods(
            tariffs,
            period_start,
            include_vat=False,
        )

        if tariff is None:
            normal_costs.append(pd.NA)
            continue

        normal_costs.append(
            row["consumption_kwh"]
            * tariff["rate_p_per_kwh"]
            / 100
        )

    result["normal_cost_gbp"] = normal_costs

    result["actual_cost_gbp"] = result["cost_excl_vat_gbp"]

    result["smart_flex_saving_gbp"] = (
        result["normal_cost_gbp"]
        - result["actual_cost_gbp"]
    )

    consumption_kwh = result["consumption_kwh"].sum()
    actual_cost_gbp = result["actual_cost_gbp"].sum()
    normal_cost_gbp = result["normal_cost_gbp"].sum()
    saving_gbp = result["smart_flex_saving_gbp"].sum()

    saving_percentage = (
        saving_gbp / normal_cost_gbp * 100
        if normal_cost_gbp
        else 0.0
    )

    return {
        "date": summary_date,
        "consumption_kwh": consumption_kwh,
        "actual_cost_gbp": actual_cost_gbp,
        "normal_cost_gbp": normal_cost_gbp,
        "smart_flex_saving_gbp": saving_gbp,
        "saving_percentage": saving_percentage,
    }

def get_smart_flex_summary(
    repository,
    tariff_code: str,
    start_date: date,
    end_date: date,
) -> dict:
    """
    Return Smart Flex cost analysis for an inclusive range of local
    calendar dates.

    Returns:
        {
            "start_date": date,
            "end_date": date,
            "daily": DataFrame,
            "total": dict,
        }

    Costs are calculated excluding VAT, consistent with the existing
    Smart Flex analysis.
    """

    tz = ZoneInfo(TIMEZONE)

    day_start = datetime.combine(
        start_date,
        datetime.min.time(),
        tzinfo=tz,
    )

    # end_date is inclusive, so the database/API range ends at
    # midnight on the following day.
    day_end = datetime.combine(
        end_date + timedelta(days=1),
        datetime.min.time(),
        tzinfo=tz,
    )

    # Database timestamps are local and timezone-naive.
    costs = repository.get_octopus_consumption_costs(
        period_from=day_start.replace(tzinfo=None).isoformat(),
        period_to=day_end.replace(tzinfo=None).isoformat(),
    )

    if costs.empty:
        return {
            "start_date": start_date,
            "end_date": end_date,
            "daily": pd.DataFrame(
                columns=[
                    "date",
                    "consumption_kwh",
                    "normal_cost_gbp",
                    "actual_cost_gbp",
                    "smart_flex_saving_gbp",
                ]
            ),
            "total": {
                "consumption_kwh": 0.0,
                "normal_cost_gbp": 0.0,
                "actual_cost_gbp": 0.0,
                "smart_flex_saving_gbp": 0.0,
                "saving_percentage": 0.0,
            },
        }

    actual_costs = calculate_octopus_actual_costs(costs)

    # Load the entire tariff range once.
    tariffs = get_tariffs_for_period(
        tariff_code=tariff_code,
        period_start=day_start,
        period_end=day_end,
        include_vat=False,
    )

    result = actual_costs.copy()

    normal_costs = []

    for _, row in result.iterrows():
        period_start = row["interval_start"].replace(tzinfo=tz)

        tariff = match_tariff_from_periods(
            tariffs,
            period_start,
            include_vat=False,
        )

        if tariff is None:
            normal_costs.append(float("nan"))
            continue

        normal_costs.append(
            row["consumption_kwh"]
            * tariff["rate_p_per_kwh"]
            / 100
        )

    result["normal_cost_gbp"] = normal_costs
    result["actual_cost_gbp"] = result["cost_excl_vat_gbp"]

    result["smart_flex_saving_gbp"] = (
        result["normal_cost_gbp"]
        - result["actual_cost_gbp"]
    )

    # Use the local calendar date for daily grouping.
    result["date"] = result["interval_start"].dt.date

    daily = (
        result.groupby("date", as_index=False)
        .agg(
            consumption_kwh=("consumption_kwh", "sum"),
            normal_cost_gbp=("normal_cost_gbp", "sum"),
            actual_cost_gbp=("actual_cost_gbp", "sum"),
            smart_flex_saving_gbp=("smart_flex_saving_gbp", "sum"),
        )
    )

    # Overall totals.
    consumption_kwh = daily["consumption_kwh"].sum()
    normal_cost_gbp = daily["normal_cost_gbp"].sum()
    actual_cost_gbp = daily["actual_cost_gbp"].sum()
    saving_gbp = daily["smart_flex_saving_gbp"].sum()

    saving_percentage = (
        saving_gbp / normal_cost_gbp * 100
        if normal_cost_gbp
        else 0.0
    )

    total = {
        "consumption_kwh": consumption_kwh,
        "normal_cost_gbp": normal_cost_gbp,
        "actual_cost_gbp": actual_cost_gbp,
        "smart_flex_saving_gbp": saving_gbp,
        "saving_percentage": saving_percentage,
    }

    return {
        "start_date": start_date,
        "end_date": end_date,
        "daily": daily,
        "total": total,
    }

