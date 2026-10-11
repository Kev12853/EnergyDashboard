from unittest.mock import Mock

from app.enums.solax_enums import ManualMode, WorkMode
from app.solax.backend.inverter.inverter_reconciler import InverterReconciler


class FakeStateRepository:
    def get(self):
        return {
            "requested_work_mode": WorkMode.MANUAL,
            "requested_manual_mode": ManualMode.FORCE_CHARGE,
            "restore_work_mode_to": WorkMode.SELF_USE,
            "restore_manual_mode_to": ManualMode.IDLE,
            "phase": "OVERRIDE",
            "source": "smart_flex",
        }


class FakeSnapshot:
    work_mode = WorkMode.SELF_USE
    manual_mode = ManualMode.IDLE


def test_reconciler_requests_force_charge():

    inverter_service = Mock()

    reconciler = InverterReconciler(
        inverter_state_repo=FakeStateRepository(),
        inverter_service=inverter_service,
    )

    reconciler.process(FakeSnapshot())

    inverter_service.write_work_mode.assert_called_once_with(
        WorkMode.MANUAL,
        ManualMode.FORCE_CHARGE,
    )

    print("PASS: Reconciler requested Force Charge")


if __name__ == "__main__":
    test_reconciler_requests_force_charge()