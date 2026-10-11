from datetime import datetime

from app.octopus.costs.octopus_tariff_matching import get_tariff_for_period


TARIFF = "E-1R-INTELLI-FIX-12M-26-04-18-A"


def test(period: str) -> None:

    dt = datetime.fromisoformat(
        period.replace("Z", "+00:00")
    )

    result = get_tariff_for_period(
        TARIFF,
        dt,
    )

    print()
    print("=" * 70)
    print(f"PERIOD: {period}")
    print("=" * 70)

    if result is None:
        print("NO TARIFF FOUND")
        return

    print(f"Tariff ID   : {result['tariff_id']}")
    print(f"Rate        : {result['rate_p_per_kwh']:.5f} p/kWh")
    print(f"Source      : {result['rate_source']}")


def main() -> None:

    # ==========================================================
    # Test tariff row 3790
    #
    # valid_from = 2026-08-11T22:30:00Z
    # valid_to   = 2026-08-12T04:30:00Z
    # rate       = 10.5 p/kWh
    # ==========================================================

    # One minute before the tariff starts.
    # Should NOT use tariff 3790.
    test("2026-08-11T22:29:00Z")

    # Exactly when tariff 3790 starts.
    # SHOULD use tariff 3790.
    test("2026-08-11T22:30:00Z")

    # Inside tariff 3790.
    # SHOULD use tariff 3790.
    test("2026-08-12T00:00:00Z")

    # One minute before tariff 3790 ends.
    # SHOULD use tariff 3790.
    test("2026-08-12T04:29:00Z")

    # Exactly when tariff 3790 ends.
    # Should NOT use tariff 3790 because valid_to is exclusive.
    test("2026-08-12T04:30:00Z")


if __name__ == "__main__":
    main()
