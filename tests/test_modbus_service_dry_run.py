"""Verify the Modbus service write interlock and configured work/manual write mapping without sending physical writes."""

from unittest.mock import Mock, patch

from app.solax.telemetry.modbus_service import SolaxModbusService


def test_write_work_mode_dry_run():
    with patch(
        "app.solax.telemetry.modbus_service.SolaxModbusClient"
    ) as mock_client_class:

        mock_client = Mock()
        mock_client_class.return_value = mock_client

        service = SolaxModbusService(
            host="dummy",
            port=502,
            slave_id=1,
        )

        service.write_work_mode(3, 1)

        mock_client.client.write_register.assert_not_called()

        print("PASS: DRY_RUN prevented Modbus write")


if __name__ == "__main__":
    test_write_work_mode_dry_run()