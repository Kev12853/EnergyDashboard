"""Exercise reconciliation of Smart Flex override and restoration requests against supplied telemetry."""

from pprint import pprint

from app.solax.backend.inverter.inverter_reconciler import InverterReconciler
from app.enums.inverter_state_enums import InverterRequestPhase
from app.enums.solax_enums import WorkMode, ManualMode


class FakeRepository:
    def __init__(self):
        self.state = {
            "requested_work_mode": WorkMode.MANUAL,
            "requested_manual_mode": ManualMode.FORCE_CHARGE,
            "restore_work_mode_to": None,
            "restore_manual_mode_to": None,
            "underlying_work_mode": WorkMode.MANUAL,
            "underlying_manual_mode": ManualMode.FORCE_CHARGE,
            "active": 1,
            "source": "smart_flex",
            "phase": InverterRequestPhase.OVERRIDE,
        }

    def get(self):
        return self.state

    def clear(self):
        print("CLEAR CALLED")
        self.state = None


class FakeInverterService:
    def __init__(self):
        self.write_calls = []

    def write_work_mode(self, work_mode, manual_mode):
        self.write_calls.append(
            (work_mode, manual_mode)
        )


class FakeSnapshot:
    work_mode = WorkMode.MANUAL
    manual_mode = ManualMode.FORCE_CHARGE


def main():
    repository = FakeRepository()
    service = FakeInverterService()

    reconciler = InverterReconciler(
        repository,
        service,
    )

    snapshot = FakeSnapshot()

    reconciler.process(snapshot)

    print()
    print("=" * 60)
    print("RESULT")
    print("=" * 60)

    pprint(repository.state)

    print()
    print("WRITE CALLS:")
    pprint(service.write_calls)

    assert repository.state is not None
    assert repository.state["source"] == "smart_flex"
    assert repository.state["phase"] == InverterRequestPhase.OVERRIDE

    assert (
        repository.state["requested_work_mode"]
        == WorkMode.MANUAL
    )

    assert (
        repository.state["requested_manual_mode"]
        == ManualMode.FORCE_CHARGE
    )

    assert (
        repository.state["underlying_work_mode"]
        == WorkMode.MANUAL
    )

    assert (
        repository.state["underlying_manual_mode"]
        == ManualMode.FORCE_CHARGE
    )

    assert service.write_calls == []

    print()
    print("=" * 60)
    print("PASS")
    print("=" * 60)


if __name__ == "__main__":
    main()