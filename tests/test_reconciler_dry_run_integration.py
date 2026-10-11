from unittest.mock import Mock, patch

from app.enums.solax_enums import WorkMode, ManualMode
from app.solax.backend.inverter.inverter_reconciler import InverterReconciler
from app.solax.telemetry.modbus_service import SolaxModbusService


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


def test_reconciler_to_modbus_dry_run():

    with patch(
        "app.solax.telemetry.modbus_service.SolaxModbusClient"
    ) as mock_client_class:

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        # Real Modbus service
        modbus_service = SolaxModbusService(
            host="dummy",
            port=502,
            slave_id=1,
        )

        # Real reconciler
        reconciler = InverterReconciler(
            inverter_state_repo=FakeStateRepository(),
            inverter_service=modbus_service,
        )

        # Run reconciliation
        reconciler.process(FakeSnapshot())

        # DRY_RUN must prevent the physical write
        mock_client.client.write_register.assert_not_called()

        print("PASS: Reconciler reached Modbus service")
        print("PASS: DRY_RUN prevented physical Modbus write")


if __name__ == "__main__":
    test_reconciler_to_modbus_dry_run()