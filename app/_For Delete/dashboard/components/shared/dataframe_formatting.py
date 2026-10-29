import pandas as pd


ACRONYM_MAP = {
    "pv": "PV",
    "soc": "SOC",
    "wh": "Wh",
    "kwh": "kWh",
    "kw": "kW",
    "w": "W",
    "ac": "AC",
    "dc": "DC",
    "api": "API",
    "id": "ID",
    "pct": "%",
}

COLUMN_LABEL_OVERRIDES = {
    "import_rate_gbp_per_kwh": "Rate (£/kWh)",
}


def ordinal(
    n: int,
) -> str:

    if 11 <= (n % 100) <= 13:
        suffix = "th"

    else:
        suffix = {
            1: "st",
            2: "nd",
            3: "rd",
        }.get(
            n % 10,
            "th",
        )

    return f"{n}{suffix}"


def humanize_column_name(
    column: str,
) -> str:
    """
    Convert machine-friendly dataframe columns
    into human-readable UI labels.
    """
    if column in COLUMN_LABEL_OVERRIDES:
        return COLUMN_LABEL_OVERRIDES[column]
    parts = column.split("_")

    formatted_parts = []

    for part in parts:
        lowercase_part = part.lower()

        if lowercase_part in ACRONYM_MAP:
            formatted_parts.append(ACRONYM_MAP[lowercase_part])

        else:
            formatted_parts.append(part.capitalize())

    label = " ".join(formatted_parts)

    label = label.replace(" Kwh", " (kWh)")

    label = label.replace(" Wh", " (Wh)")

    label = label.replace(" W", " (W)")

    label = label.replace(" %", " (%)")

    return label


def format_dataframe_columns(
    df: pd.DataFrame,
    *,
    datetime_format="full",
) -> pd.DataFrame:
    """
    Return a copy of dataframe with
    human-friendly column names
    and formatted datetime columns.
    """

    if df is None:
        return None

    result = df.copy()

    # =====================================================
    # HUMANIZE COLUMN NAMES
    # =====================================================

    result.columns = [humanize_column_name(column) for column in result.columns]

    # =====================================================
    # FORMAT DATETIME COLUMNS
    # =====================================================

    SKIP_DATETIME_FORMATTING = {
        "Slot Time",
    }

    datetime_columns = [
        column
        for column in result.columns
        if (
            ("Time" in column or "Date" in column)
            and column not in SKIP_DATETIME_FORMATTING
        )
    ]

    for column in datetime_columns:
        try:
            if pd.api.types.is_datetime64_any_dtype(result[column]):
                dt_series = result[column]
            else:
                dt_series = pd.to_datetime(
                    result[column],
                    errors="coerce",
                )

            if datetime_format == "date_only":
                result[column] = dt_series.apply(
                    lambda dt: (
                        f"{dt.strftime('%a')} {ordinal(dt.day)} {dt.strftime('%b %Y')}"
                    )
                )

            else:
                result[column] = dt_series.apply(
                    lambda dt: (
                        f"{dt.strftime('%a')} "
                        f"{ordinal(dt.day)} "
                        f"{dt.strftime('%b %Y %H:%M')}"
                    )
                )

        except Exception:
            pass

    # =====================================================
    # ROUND NUMERIC COLUMNS
    # =====================================================

    numeric_columns = result.select_dtypes(include="number").columns

    for column in numeric_columns:
        result[column] = result[column].map(lambda x: f"{x:.2f}")

    return result
