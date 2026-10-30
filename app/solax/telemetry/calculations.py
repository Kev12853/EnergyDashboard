"""Enrich telemetry frames with energy-cost calculations using supplied tariff data. This is reporting logic with no Modbus or database side effects."""

def add_costs(df, import_rate=0.30, export_rate=0.15):
    """Add cost fields to supplied telemetry data using the provided tariff inputs; returns transformed data and performs no persistence."""
    df = df.copy()

    df["cost"] = df["consumption_kwh"] * import_rate
    df["revenue"] = df["export_kwh"] * export_rate
    df["net"] = df["cost"] - df["revenue"]

    return df
