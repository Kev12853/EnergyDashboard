import pandas as pd


def apply_import_costs(
    settlement_df,
    tariff_df,
):

    if settlement_df.empty:
        return settlement_df

    settlement_df = settlement_df.copy()

    settlement_df["import_rate_gbp_per_kwh"] = 0.0

    tariff_df = tariff_df.copy()

    tariff_df["valid_from"] = pd.to_datetime(
        tariff_df["valid_from"],
        utc=True,
    )

    tariff_df["valid_to"] = pd.to_datetime(
        tariff_df["valid_to"],
        utc=True,
    )

    settlement_df["upload_time"] = pd.to_datetime(
        settlement_df["upload_time"],
        utc=True,
    )

    for _, tariff in tariff_df.iterrows():

        start = tariff["valid_from"]

        end = tariff["valid_to"]

        rate = tariff["value_inc_vat"] / 100

        mask = (
            (settlement_df["upload_time"] >= start)
            & (settlement_df["upload_time"] < end)
        )

        settlement_df.loc[
            mask,
            "import_rate_gbp_per_kwh",
        ] = rate

    settlement_df["import_cost_gbp"] = (
        settlement_df["grid_import_kwh"]
        * settlement_df["import_rate_gbp_per_kwh"]
    )

    return settlement_df
