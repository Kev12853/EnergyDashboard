import pandas as pd

def aggregate_data(df, freq):
    """
    freq:
    None = raw half-hourly
    D = Daily
    W = Weekly
    M = Monthly
    """
    if df.empty:
        return df

    if freq is None:
        # Explicitly return sorted raw data
        # Check if datetime is the index, if so, move it back to columns for sorting
        if "datetime" not in df.columns:
            df = df.reset_index()
        return df.sort_values("datetime").reset_index(drop=True)

    df = df.copy()

    # --- FIX STARTS HERE ---
    # Only set_index if 'datetime' is a column.
    # If it's already the index, this skips to avoid the KeyError.
    if "datetime" in df.columns:
        df = df.set_index("datetime")
    # --- FIX ENDS HERE ---

    agg_df = df.resample(freq).agg({
        "consumption_kwh": "sum",
        "export_kwh": "sum",
        "cost": "sum",
        "revenue": "sum",
        "net": "sum"
    })

    return agg_df.reset_index()
