import pandas as pd


def apply_dispatch_flags(
    settlement_df: pd.DataFrame,
    dispatch_df: pd.DataFrame,
) -> pd.DataFrame:

    if settlement_df.empty:
        return settlement_df

    result = settlement_df.copy()

    result["dispatch_active"] = False

    if dispatch_df.empty:
        return result

    for _, dispatch in dispatch_df.iterrows():

        mask = (
            (
                result["upload_time"]
                >= dispatch["dispatch_start"]
            )
            &
            (
                result["upload_time"]
                < dispatch["dispatch_end"]
            )
        )

        result.loc[
            mask,
            "dispatch_active",
        ] = True

    return result