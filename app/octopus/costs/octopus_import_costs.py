from datetime import datetime

import pandas as pd

from app.octopus.costs.octopus_tariff_matching import (
    get_tariff_for_period,
)


def calculate_import_costs(
    consumption: pd.DataFrame,
    tariff_code: str,
) -> pd.DataFrame:
    """
    Calculate the cost of Octopus import consumption.

    Expected input columns:

        bucket_start
        consumption_kwh

    Returns the same periods with:

        rate_p_per_kwh
        cost_gbp
        rate_source
        tariff_id
    """

    if consumption.empty:
        return consumption.copy()

    result = consumption.copy()

    rates = []
    costs = []
    sources = []
    tariff_ids = []

    for _, row in result.iterrows():

        period_start = row["bucket_start"]

        if not isinstance(period_start, datetime):
            period_start = pd.Timestamp(
                period_start
            ).to_pydatetime()

        tariff = get_tariff_for_period(
            tariff_code=tariff_code,
            period_start=period_start,
        )

        if tariff is None:
            rates.append(pd.NA)
            costs.append(pd.NA)
            sources.append("unmatched")
            tariff_ids.append(pd.NA)
            continue

        rate = tariff["rate_p_per_kwh"]
        consumption_kwh = float(
            row["consumption_kwh"]
        )

        rates.append(rate)
        costs.append(
            consumption_kwh * rate / 100
        )
        sources.append(
            tariff["rate_source"]
        )
        tariff_ids.append(
            tariff["tariff_id"]
        )

    result["rate_p_per_kwh"] = rates
    result["cost_gbp"] = costs
    result["rate_source"] = sources
    result["tariff_id"] = tariff_ids

    return result