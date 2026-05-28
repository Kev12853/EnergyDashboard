from datetime import datetime
import pandas as pd



def normalize_import_tariffs(
    tariff_df: pd.DataFrame,
    tariff_code: str,
) -> pd.DataFrame:

    if tariff_df.empty:

        return pd.DataFrame()

    result = tariff_df.copy()

    result = result.rename(
        columns={
            "value_inc_vat": (
                "unit_rate_gbp_per_kwh"
            ),
        }
    )

    result["valid_from"] = (
        pd.to_datetime(
            result["valid_from"]
        )
    )

    result["valid_to"] = (
        pd.to_datetime(
            result["valid_to"]
        )
    )

    # Pence -> pounds

    result[
        "unit_rate_gbp_per_kwh"
    ] = (

        result[
            "unit_rate_gbp_per_kwh"
        ]

        / 100

    )

    result[
        "tariff_code"
    ] = tariff_code

    result[
        "created_at"
    ] = (
        datetime.now()
        .isoformat()
    )

    result = result[
        [

            "tariff_code",

            "valid_from",

            "valid_to",

            "unit_rate_gbp_per_kwh",

            "created_at",

        ]
    ]

    # ==========================================
    # TIME OF DAY SLOTS
    # ==========================================

    result[
        "slot_start"
    ] = (
        result[
            "valid_from"
        ]
        .dt.strftime(
            "%H:%M"
        )
    )

    result[
        "slot_end"
    ] = (
        result[
            "valid_to"
        ]
        .dt.strftime(
            "%H:%M"
        )
    )

    # ==========================================
    # FIND CANONICAL SLOTS
    # ==========================================

    slot_counts = (

        result

        .groupby(
            [
                "slot_start",
                "slot_end",
            ]
        )

        .size()

    )

    canonical_slots = (

        slot_counts[
            slot_counts
            ==
            slot_counts.max()
            ]

        .index

    )

    result = (

        result[
            result.apply(

                lambda row:

                (

                    row[
                        "slot_start"
                    ],

                    row[
                        "slot_end"
                    ],

                )

                in canonical_slots,

                axis=1,

            )
        ]

    )

    # ==========================================
    # REMOVE DAILY DUPLICATES
    # ==========================================

    result = (

        result

        .drop_duplicates(

            subset=[

                "tariff_code",

                "slot_start",

                "slot_end",

                "unit_rate_gbp_per_kwh",

            ]

        )

    )

    result = result[
        [
            "tariff_code",
            "slot_start",
            "slot_end",
            "unit_rate_gbp_per_kwh",
            "created_at",
        ]
    ]

    result = result.reset_index(
        drop=True
    )

    return result