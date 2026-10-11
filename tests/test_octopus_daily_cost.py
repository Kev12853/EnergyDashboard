import pandas as pd

from tests.test_octopus_import_costs import (
    get_octopus_consumption,
    get_import_tariff_code,
    apply_tariffs,
)

from tests.test_octopus_export_costs import (
    get_octopus_export,
    get_export_tariff_code,
    apply_export_tariffs,
)


# ============================================================
# DATE TO ANALYSE
# ============================================================

TEST_DATE = "2026-08-11"


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 110)
    print("OCTOPUS DAILY COST ANALYSIS")
    print(
        pd.Timestamp(TEST_DATE).strftime(
            "%d %B %Y"
        )
    )
    print("=" * 110)

    # ========================================================
    # IMPORT
    # ========================================================

    print()
    print("Fetching Octopus import data...")

    import_data = get_octopus_consumption()

    print(
        f"Import periods : {len(import_data)}"
    )

    import_tariff_code = get_import_tariff_code()

    import_result = apply_tariffs(
        import_data,
        import_tariff_code,
    )

    import_kwh = (
        import_result["consumption_kwh"]
        .sum()
    )

    import_energy_cost = (
        import_result["cost_gbp"]
        .sum()
    )

    import_unmatched = (
        import_result["rate_p_per_kwh"]
        .isna()
        .sum()
    )

    import_recorded = (
        import_result["rate_source"]
        == "recorded"
    ).sum()

    import_fallback = (
        import_result["rate_source"]
        == "historical_fallback"
    ).sum()

    # ========================================================
    # EXPORT
    # ========================================================

    print()
    print("Fetching Octopus export data...")

    export_data = get_octopus_export()

    print(
        f"Export periods : {len(export_data)}"
    )

    export_tariff_code = get_export_tariff_code()

    export_result = apply_export_tariffs(
        export_data,
        export_tariff_code,
    )

    export_kwh = (
        export_result["export_kwh"]
        .sum()
    )

    export_payment = (
        export_result["payment_gbp"]
        .sum()
    )

    export_unmatched = (
        export_result["rate_p_per_kwh"]
        .isna()
        .sum()
    )

    export_recorded = (
        export_result["rate_source"]
        == "recorded"
    ).sum()

    export_fallback = (
        export_result["rate_source"]
        == "historical_fallback"
    ).sum()

    # ========================================================
    # STANDING CHARGE
    # ========================================================

    # 49.71p before VAT
    # VAT = 5%
    #
    # 49.71 * 1.05 = 52.1955p
    # £0.521955

    standing_charge = (
        0.4971 * 1.05
    )

    # ========================================================
    # TOTALS
    # ========================================================

    total_import_cost = (
        import_energy_cost
        + standing_charge
    )

    net_daily_cost = (
        total_import_cost
        - export_payment
    )

    # ========================================================
    # IMPORT SUMMARY
    # ========================================================

    print()
    print("=" * 110)
    print("IMPORT")
    print("=" * 110)

    print(
        f"Tariff code       : "
        f"{import_tariff_code}"
    )

    print(
        f"Consumption       : "
        f"{import_kwh:.5f} kWh"
    )

    print(
        f"Energy cost       : "
        f"£{import_energy_cost:.5f}"
    )

    print(
        f"Standing charge   : "
        f"£{standing_charge:.5f}"
    )

    print(
        f"Total import cost : "
        f"£{total_import_cost:.5f}"
    )

    # ========================================================
    # EXPORT SUMMARY
    # ========================================================

    print()
    print("=" * 110)
    print("EXPORT")
    print("=" * 110)

    print(
        f"Tariff code       : "
        f"{export_tariff_code}"
    )

    print(
        f"Export            : "
        f"{export_kwh:.5f} kWh"
    )

    print(
        f"Export payment    : "
        f"£{export_payment:.5f}"
    )

    # ========================================================
    # NET DAILY COST
    # ========================================================

    print()
    print("=" * 110)
    print("NET DAILY COST")
    print("=" * 110)

    print(
        f"Import cost       : "
        f"£{total_import_cost:.5f}"
    )

    print(
        f"Export payment    : "
        f"£{export_payment:.5f}"
    )

    print()
    print(
        f"NET COST          : "
        f"£{net_daily_cost:.5f}"
    )

    # ========================================================
    # TARIFF MATCHING
    # ========================================================

    print()
    print("=" * 110)
    print("TARIFF MATCHING")
    print("=" * 110)

    print(
        f"Import periods          : "
        f"{len(import_result)}"
    )

    print(
        f"Import recorded rates   : "
        f"{import_recorded}"
    )

    print(
        f"Import fallback rates   : "
        f"{import_fallback}"
    )

    print(
        f"Import unmatched        : "
        f"{import_unmatched}"
    )

    print()

    print(
        f"Export periods          : "
        f"{len(export_result)}"
    )

    print(
        f"Export recorded rates   : "
        f"{export_recorded}"
    )

    print(
        f"Export fallback rates   : "
        f"{export_fallback}"
    )

    print(
        f"Export unmatched        : "
        f"{export_unmatched}"
    )

    # ========================================================
    # COVERAGE
    # ========================================================

    print()
    print("=" * 110)
    print("COVERAGE")
    print("=" * 110)

    print(
        f"Import periods : "
        f"{len(import_result)}"
    )

    print(
        f"Export periods : "
        f"{len(export_result)}"
    )

    print(
        f"Expected       : 48"
    )

    print()

    if len(import_result) != 48:
        print(
            "WARNING: Import coverage is incomplete"
        )

    if len(export_result) != 48:
        print(
            "WARNING: Export coverage is incomplete"
        )

    if import_unmatched:
        print(
            f"WARNING: {import_unmatched} "
            f"import periods have no tariff"
        )

    if export_unmatched:
        print(
            f"WARNING: {export_unmatched} "
            f"export periods have no tariff"
        )


if __name__ == "__main__":
    main()