def add_costs(df, import_rate=0.30, export_rate=0.15):
    df = df.copy()

    df["cost"] = df["consumption_kwh"] * import_rate
    df["revenue"] = df["export_kwh"] * export_rate
    df["net"] = df["cost"] - df["revenue"]

    return df