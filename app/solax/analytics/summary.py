"""Build daily SolaX telemetry summaries for reporting from caller-provided readings; this module does not communicate with the inverter."""

# =========================================================
# SUMMARY ANALYTICS
# =========================================================

# =========================================================
# DAILY SUMMARY
# =========================================================


def calculate_daily_summary(df):

    """Summarise the supplied SolaX readings for one day and return the daily report values."""
    summary_df = (
        df.groupby(df["upload_time"].dt.date)
        .agg(
            avg_house_load_w=(
                "house_load_w",
                "mean",
            ),
            peak_house_load_w=(
                "house_load_w",
                "max",
            ),
            avg_pv_power_w=(
                "pv_power_w",
                "mean",
            ),
            peak_pv_power_w=(
                "pv_power_w",
                "max",
            ),
        )
        .reset_index()
    )

    return summary_df
