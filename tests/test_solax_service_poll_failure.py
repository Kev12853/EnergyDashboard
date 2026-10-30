from unittest.mock import MagicMock, patch

import app.solax.backend.polling.solax_service as poller
from app.solax.telemetry.models import PowerFlowSnapshot
from datetime import datetime, timezone


def test_poller_records_modbus_failure_and_retries_without_control_calls():
    fake_service = MagicMock()
    fake_service.poll.side_effect = [RuntimeError("offline"), KeyboardInterrupt]
    fake_connection = MagicMock()
    telemetry = MagicMock()
    cloud = MagicMock()

    with patch.object(poller, "get_connection", return_value=fake_connection), \
         patch.object(poller, "create_solax_tables"), \
         patch.object(poller, "InverterPollingService", return_value=fake_service), \
         patch.object(poller, "SolaxCloudTelemetryService", return_value=cloud), \
         patch.object(poller, "TelemetryRepository", return_value=telemetry), \
         patch.object(poller, "PushoverSender"), \
         patch.object(poller, "EmailSender"), \
         patch.object(poller, "WorkModeMonitor"), \
         patch.object(poller.time, "sleep") as sleep:
        poller.main()

    assert fake_service.poll.call_count == 2
    telemetry.save_heartbeat.assert_called_once()
    assert telemetry.save_heartbeat.call_args.args[1] == "Warning"
    telemetry.save_snapshot.assert_called_once_with(cloud.poll.return_value, source="cloud")
    sleep.assert_called_once_with(10)
    assert not hasattr(poller, "Scheduler")
    assert not hasattr(poller, "InverterReconciler")


def test_poller_recovers_after_modbus_failure_and_notifies_once_each_way():
    fake_service = MagicMock()
    snapshot = PowerFlowSnapshot(
        timestamp=datetime.now(timezone.utc), work_mode=0, manual_mode=0,
        battery_soc_pct=50,
    )
    fake_service.poll.side_effect = [RuntimeError("offline"), snapshot, KeyboardInterrupt]
    fake_connection = MagicMock()
    telemetry = MagicMock()
    push_instance = MagicMock()
    monitor_instance = MagicMock()
    monitor_instance.update.return_value = None

    with patch.object(poller, "get_connection", return_value=fake_connection), \
         patch.object(poller, "create_solax_tables"), \
         patch.object(poller, "InverterPollingService", return_value=fake_service), \
         patch.object(poller, "SolaxCloudTelemetryService"), \
         patch.object(poller, "TelemetryRepository", return_value=telemetry), \
         patch.object(poller, "PushoverSender", return_value=push_instance), \
         patch.object(poller, "EmailSender"), \
         patch.object(poller, "WorkModeMonitor", return_value=monitor_instance), \
         patch.object(poller, "COMMUNICATION_TIMEOUT", 0), \
         patch.object(poller.time, "sleep"):
        poller.main()

    assert fake_service.poll.call_count == 3
    assert telemetry.save_snapshot.call_args_list[-1].args == (snapshot,)
    assert telemetry.save_snapshot.call_args_list[-1].kwargs == {"source": "modbus"}
    assert push_instance.send_push.call_count == 2
    assert "restored" in push_instance.send_push.call_args_list[-1].kwargs["message"].lower()
