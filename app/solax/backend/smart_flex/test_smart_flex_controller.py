from datetime import datetime
from zoneinfo import ZoneInfo
from types import SimpleNamespace

from app.solax.backend.smart_flex.smart_flex_controller import (
    SmartFlexController,
)


TIMEZONE = ZoneInfo("Europe/London")


def make_snapshot(time_string, soc):
    return SimpleNamespace(
        timestamp=datetime.fromisoformat(time_string).replace(
            tzinfo=TIMEZONE
        ),
        battery_soc_pct=soc,
    )


def main():

    print()
    print("=" * 60)
    print("SMART FLEX CONTROLLER SIMULATION")
    print("=" * 60)

    controller = SmartFlexController()

    dispatch = object()

    tests = [
        (
            "14:00",
            70,
            False,
            "NORMAL",
            "New slot, BMW not charging",
        ),
        (
            "14:10",
            70,
            True,
            "FORCE_CHARGE",
            "BMW starts charging during slot",
        ),
        (
            "14:20",
            70,
            False,
            "FORCE_CHARGE",
            "BMW stops charging, but slot continues",
        ),
        (
            "14:30",
            70,
            False,
            "NORMAL",
            "New slot, Force Charge must reset",
        ),
    ]

    for time, soc, charging, expected, description in tests:

        snapshot = make_snapshot(
            f"2026-09-10T{time}:00",
            soc,
        )

        vehicle_status = {
            "connected": charging,
            "charging": charging,
        }

        decision = controller.evaluate(
            snapshot=snapshot,
            dispatch=dispatch,
            vehicle_status=vehicle_status,
        )

        result = "PASS" if decision == expected else "FAIL"

        print()
        print(
            f"{time}  "
            f"SOC={soc}%  "
            f"BMW charging={charging}"
        )
        print(f"Expected: {expected}")
        print(f"Actual:   {decision}")
        print(f"{result}: {description}")

    print()
    print("=" * 60)

    print()
    print("-" * 60)
    print("SOC TARGET TEST")
    print("-" * 60)

    controller.reset()

    soc_tests = [
        (70.0, "FORCE_CHARGE"),
        (79.9, "FORCE_CHARGE"),
        (80.0, "NORMAL"),
        (85.0, "NORMAL"),
    ]

    for soc, expected in soc_tests:

        snapshot = make_snapshot(
            "2026-09-10T15:00:00",
            soc,
        )

        vehicle_status = {
            "connected": True,
            "charging": True,
        }

        decision = controller.evaluate(
            snapshot=snapshot,
            dispatch=dispatch,
            vehicle_status=vehicle_status,
        )

        result = "PASS" if decision == expected else "FAIL"

        print(
            f"SOC={soc:4.1f}%  "
            f"Expected={expected:12s}  "
            f"Actual={decision:12s}  "
            f"{result}"
        )

        controller.reset()


if __name__ == "__main__":
    main()