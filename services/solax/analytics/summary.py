# =========================================================
# SUMMARY ANALYTICS
# =========================================================

# =========================================================
# DAILY SUMMARY
# =========================================================

def calculate_daily_summary(df):

    summary_df = (
        df.groupby(
            df["upload_time"].dt.date
        )
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