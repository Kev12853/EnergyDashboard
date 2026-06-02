import pandas as pd

from app.solax.analytics.energy import (
    calculate_interval_energy,
)


def calculate_half_hour_energy(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Aggregate telemetry energy into
    Octopus-compatible 30-minute
    cost periods.
    """

    if df.empty:
        return pd.DataFrame()

    energy_df = calculate_interval_energy(
        df
    )

    # =====================================================
    # TIMESTAMP INDEX
    # =====================================================

    #debug
    # print(
    #     energy_df[
    #         [
    #             "upload_time",
    #             "pv_energy_wh",
    #         ]
    #     ].head(20)
    # )

    # print(
    #     energy_df[
    #         [
    #             "upload_time",
    #             "pv_energy_wh",
    #         ]
    #     ].tail(20)
    # )
    #end debug

    energy_df = energy_df.set_index(
        "upload_time"
    )

    # =====================================================
    # RESAMPLE TO 30 MINUTES
    # =====================================================

    #debug
    # print(
    #     energy_df.index.min()
    # )
    #
    # print(
    #     energy_df.index.max()
    # )
    #end debug

    settlement_df = (
        energy_df.resample(
            "30min"
        )
        .agg(
            {
                "pv_energy_wh": "sum",
                "house_load_energy_wh": "sum",
                "grid_energy_wh": "sum",
                "battery_energy_wh": "sum",
            }
        )
    )

    settlement_df = (
        settlement_df.reset_index()
    )

    settlement_df["slot_time"] = (
        settlement_df["upload_time"]
        .dt.strftime("%H:%M")
    )

    settlement_df["forced_charge_window"] = (
            (
                    settlement_df["slot_time"] >= "23:30"
            )
            |
            (
                    settlement_df["slot_time"] < "05:30"
            )
    )

    # =====================================================
    # SPLIT IMPORT / EXPORT
    # =====================================================

    settlement_df["grid_import_wh"] = (
        settlement_df["grid_energy_wh"]
        .clip(upper=0)
        .abs()
    )

    settlement_df["grid_export_wh"] = (
        settlement_df["grid_energy_wh"]
        .clip(lower=0)
    )

    # =====================================================
    # SPLIT BATTERY FLOWS
    # =====================================================

    settlement_df["battery_charge_wh"] = (
        settlement_df["battery_energy_wh"]
        .clip(lower=0)
    )

    settlement_df["battery_discharge_wh"] = (
        settlement_df["battery_energy_wh"]
        .clip(upper=0)
        .abs()
    )



    # =====================================================
    # CONVERT TO KWH
    # =====================================================

    wh_columns = [
        "pv_energy_wh",
        "house_load_energy_wh",
        "grid_import_wh",
        "grid_export_wh",
        "battery_charge_wh",
        "battery_discharge_wh",
    ]

    for column in wh_columns:

        kwh_column = (
            column.replace(
                "_wh",
                "_kwh",
            )
        )

        settlement_df[kwh_column] = (
            settlement_df[column] / 1000
        )

    # =====================================================
    # GRID -> BATTERY ENERGY
    # =====================================================

    settlement_df["grid_to_battery_kwh"] = 0.0

    mask = settlement_df[
        "forced_charge_window"
    ]

    settlement_df.loc[
        mask,
        "grid_to_battery_kwh",
    ] = settlement_df.loc[
        mask,
        [
            "battery_charge_kwh",
            "grid_import_kwh",
        ],
    ].min(axis=1)

    return settlement_df