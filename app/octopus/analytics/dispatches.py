import pandas as pd


def normalize_dispatches(
    dispatch_df: pd.DataFrame,
) -> pd.DataFrame:

    if dispatch_df.empty:
        return pd.DataFrame()

    result = dispatch_df.copy()

    result = result.rename(
        columns={
            "startDt":
                "dispatch_start",

            "endDt":
                "dispatch_end",

            "deltaKwh":
                "scheduled_energy_kwh",
        }
    )

    result["dispatch_start"] = (
        pd.to_datetime(
            result["dispatch_start"]
        )
    )

    result["dispatch_end"] = (
        pd.to_datetime(
            result["dispatch_end"]
        )
    )

    result = result[
        [
            "dispatch_start",
            "dispatch_end",
            "scheduled_energy_kwh",
            "status",
        ]
    ]

    result = result.sort_values(
        "dispatch_start"
    )

    result = result.reset_index(
        drop=True
    )

    return result