import pandas as pd


def calculate_interval_energy(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert instantaneous power telemetry into
    interval energy estimates using real elapsed time.
    """

    if df.empty:
        return pd.DataFrame()

    if "bucket_start" in df.columns:
        result = df.copy()

        result["upload_time"] = pd.to_datetime(result["bucket_start"])

        result["pv_energy_wh"] = result["avg_solar_w"] / 60

        result["house_load_energy_wh"] = result["avg_consumption_w"] / 60

        result["grid_energy_wh"] = result["avg_grid_w"] / 60

        result["battery_energy_wh"] = result["avg_battery_w"] / 60

        return result

    # raw telemetry path below

    result = df.copy()

    result = result.sort_values("timestamp")

    # =====================================================
    # SORT BY TIME
    # =====================================================

    result = result.sort_values("timestamp")

    # =====================================================
    # TIME DELTAS
    # =====================================================

    result["delta_seconds"] = result["upload_time"].diff().dt.total_seconds().fillna(0)
    MAX_INTERVAL_SECONDS = 600
    result["delta_seconds"] = result["delta_seconds"].clip(upper=MAX_INTERVAL_SECONDS)

    result["delta_hours"] = result["delta_seconds"] / 3600

    # =====================================================
    # ENERGY COLUMN MAPPING
    # =====================================================

    energy_column_map = {
        "pv_power_w": "pv_energy_wh",
        "battery_power_w": "battery_energy_wh",
        "grid_power_w": "grid_energy_wh",
        "house_load_w": "house_load_energy_wh",
    }

    # =====================================================
    # VALIDATE REQUIRED COLUMNS
    # =====================================================

    missing_columns = [
        column for column in energy_column_map if column not in result.columns
    ]

    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    # =====================================================
    # ENERGY CALCULATIONS
    # =====================================================

    for power_column, energy_column in energy_column_map.items():
        result[energy_column] = result[power_column] * result["delta_hours"]

    return result


def calculate_daily_energy_summary(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Aggregate interval energy into daily totals.
    """

    if df.empty:
        return pd.DataFrame()

    energy_df = calculate_interval_energy(df)

    # =====================================================
    # GRID IMPORT / EXPORT
    # =====================================================

    energy_df["grid_import_wh"] = energy_df["grid_energy_wh"].clip(upper=0).abs()

    energy_df["grid_export_wh"] = energy_df["grid_energy_wh"].clip(lower=0)

    # =====================================================
    # BATTERY CHARGE / DISCHARGE
    # =====================================================

    energy_df["battery_charge_wh"] = energy_df["battery_energy_wh"].clip(lower=0)

    energy_df["battery_discharge_wh"] = (
        energy_df["battery_energy_wh"].clip(upper=0).abs()
    )

    # =====================================================
    # DAILY AGGREGATION
    # =====================================================

    summary_df = (
        energy_df.groupby(energy_df["upload_time"].dt.date)
        .agg(
            pv_generation_wh=(
                "pv_energy_wh",
                "sum",
            ),
            house_consumption_wh=(
                "house_load_energy_wh",
                "sum",
            ),
            grid_import_wh=(
                "grid_import_wh",
                "sum",
            ),
            grid_export_wh=(
                "grid_export_wh",
                "sum",
            ),
            battery_charge_wh=(
                "battery_charge_wh",
                "sum",
            ),
            battery_discharge_wh=(
                "battery_discharge_wh",
                "sum",
            ),
        )
        .reset_index()
    )
    # =====================================================
    # CONVERT WH -> KWH
    # =====================================================

    wh_columns = [
        "pv_generation_wh",
        "house_consumption_wh",
        "grid_import_wh",
        "grid_export_wh",
        "battery_charge_wh",
        "battery_discharge_wh",
    ]

    for column in wh_columns:
        kwh_column = column.replace(
            "_wh",
            "_kwh",
        )

        summary_df[kwh_column] = summary_df[column] / 1000

    # =====================================================
    # KEEP ONLY KWH COLUMNS
    # =====================================================

    summary_df = summary_df[
        [
            "upload_time",
            "pv_generation_kwh",
            "house_consumption_kwh",
            "grid_import_kwh",
            "grid_export_kwh",
            "battery_charge_kwh",
            "battery_discharge_kwh",
        ]
    ]
    return summary_df
