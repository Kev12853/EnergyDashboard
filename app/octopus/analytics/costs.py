import pandas as pd


def apply_import_costs(
    settlement_df,
    tariff_df,
):

    if settlement_df.empty:
        return settlement_df

    settlement_df = settlement_df.copy()

    settlement_df["slot_time"] = settlement_df["upload_time"].dt.strftime("%H:%M")

    settlement_df["import_rate_gbp_per_kwh"] = 0.0

    for _, tariff in tariff_df.iterrows():
        start = tariff["slot_start"]

        end = tariff["slot_end"]

        rate = tariff["unit_rate_gbp_per_kwh"]

        if start < end:
            mask = (settlement_df["slot_time"] >= start) & (
                settlement_df["slot_time"] < end
            )

        else:
            mask = (settlement_df["slot_time"] >= start) | (
                settlement_df["slot_time"] < end
            )

        settlement_df.loc[
            mask,
            "import_rate_gbp_per_kwh",
        ] = rate

    settlement_df["import_cost_gbp"] = (
        settlement_df["grid_import_kwh"] * settlement_df["import_rate_gbp_per_kwh"]
    )

    return settlement_df
