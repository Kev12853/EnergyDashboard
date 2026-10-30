"""Deterministic regression tests for the SolaX poller/control separation, Smart Flex dispatch-data safety, reconciliation and database path resolution."""

import sqlite3
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
import pandas as pd

from app.solax.backend.polling.inverter_service import InverterPollingService
from app.solax.backend.automation.inverter_state_repository import InverterStateRepository
from app.solax.backend.automation.automation_repository import ScheduleRepository
from app.solax.backend.automation.models import SchedulePeriod
from app.solax.backend.automation.scheduler import Scheduler
from app.solax.backend.storage.schema import create_automation_tables
from app.solax.backend.services.control_service import (
    DispatchData,
    _fresh_vehicle_status,
    _persisted_dispatches,
    _snapshot_is_control_safe,
    apply_smartflex,
)
from app.solax.backend.smart_flex.smart_flex_controller import SmartFlexController
from app.solax.telemetry import modbus_service
from app.config.project_paths import resolve_paths
from app.enums.inverter_state_enums import InverterRequestPhase
from app.enums.solax_enums import WorkMode, ManualMode
from app.enums.automation_enums import InverterWorkMode
from app.solax.backend.automation.smart_flex_orchestrator import SmartFlexOrchestrator
from app.solax.backend.inverter.inverter_reconciler import InverterReconciler
from app.solax.telemetry.models import PowerFlowSnapshot
from app.octopus.service import octopus_service
from app.octopus.storage.octopus_schema import create_smartflex_vehicle_status_table


def test_polling_service_has_no_write_api():
    with patch("app.solax.backend.polling.inverter_service.SolaxModbusService"):
        service = InverterPollingService()
    assert not hasattr(service, "write_work_mode")


def test_vehicle_input_must_be_recent_and_octopus_heartbeat_current():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("CREATE TABLE octopus_vehicle_status (id INTEGER, connected INTEGER, charging INTEGER, observed_at TEXT)")
    connection.execute("CREATE TABLE service_heartbeat (service_name TEXT, last_seen TEXT)")
    now = datetime.now(timezone.utc)
    connection.execute("INSERT INTO octopus_vehicle_status VALUES (1,1,1,?)", (now.isoformat(),))
    connection.execute("INSERT INTO service_heartbeat VALUES ('Octopus',?)", (now.isoformat(),))
    assert _fresh_vehicle_status(connection) == {"connected": True, "charging": True}
    stale = now - timedelta(minutes=20)
    connection.execute("UPDATE octopus_vehicle_status SET observed_at=?", (stale.isoformat(),))
    assert _fresh_vehicle_status(connection) is None


def test_modbus_exception_response_is_reported_without_real_write():
    with patch.object(modbus_service, "DRY_RUN", False), patch.object(
        modbus_service, "ModbusTcpClient"
    ) as client_factory:
        client = client_factory.return_value
        client.connect.return_value = True
        response = MagicMock()
        response.isError.return_value = True
        client.write_register.return_value = response
        service = modbus_service.SolaxModbusService("127.0.0.1")
        with pytest.raises(RuntimeError, match="Work-mode write rejected"):
            service.write_work_mode(3, 1)
        client.close.assert_called_once()


def test_manual_write_failure_reports_partial_work_mode_write():
    with patch.object(modbus_service, "DRY_RUN", False), patch.object(
        modbus_service, "ModbusTcpClient"
    ) as client_factory:
        client = client_factory.return_value
        client.connect.return_value = True
        ok = MagicMock()
        ok.isError.return_value = False
        failed = MagicMock()
        failed.isError.return_value = True
        client.write_register.side_effect = [ok, failed]
        service = modbus_service.SolaxModbusService("127.0.0.1")
        with pytest.raises(RuntimeError, match="Work-mode write acknowledged but manual-mode write failed"):
            service.write_work_mode(3, 1)
        assert client.write_register.call_count == 2


def test_state_schema_initialises_idle_singleton_and_guards_stale_clear():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_automation_tables(connection)
    repo = InverterStateRepository(connection)
    assert repo.get() is None
    repo.set(3, 1, 0, 0, phase="OVERRIDE", source="scheduler")
    old_request = repo.get()
    repo.set(0, 0, 2, 0, phase="OVERRIDE", source="scheduler")
    assert repo.clear_if_current(old_request) is False
    assert repo.get()["requested_work_mode"] == 0


def test_state_schema_migration_preserves_existing_override():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("""CREATE TABLE inverter_state (
        id INTEGER PRIMARY KEY CHECK (id=1), requested_work_mode INTEGER,
        requested_manual_mode INTEGER, restore_work_mode_to INTEGER,
        restore_manual_mode_to INTEGER, underlying_work_mode INTEGER,
        underlying_manual_mode INTEGER, active INTEGER NOT NULL DEFAULT 0,
        phase TEXT NOT NULL, source TEXT)""")
    connection.execute(
        "INSERT INTO inverter_state VALUES (1,3,1,0,0,0,0,1,'OVERRIDE','smart_flex')"
    )
    create_automation_tables(connection)
    state = InverterStateRepository(connection).get()
    assert state["source"] == "smart_flex"
    assert state["requested_work_mode"] == 3
    assert state["updated_at"] is None


def test_dispatch_matching_uses_timezone_aware_instants():
    controller = SmartFlexController()
    dispatches = pd.DataFrame([{
        "dispatch_start": "2026-10-25T00:30:00+00:00",
        "dispatch_end": "2026-10-25T01:00:00+00:00",
    }])
    # 01:30 BST is 00:30 UTC during the autumn clock change.
    local_time = datetime.fromisoformat("2026-10-25T01:30:00+01:00")
    assert controller.get_active_dispatch(dispatches, local_time) is not None


def test_control_rejects_missing_stale_and_invalid_local_telemetry():
    from app.solax.telemetry.models import PowerFlowSnapshot

    now = datetime.now(timezone.utc)
    complete = PowerFlowSnapshot(timestamp=now, work_mode=0, manual_mode=0,
                                 battery_soc_pct=50)
    assert _snapshot_is_control_safe(complete, now)
    complete.timestamp = now - timedelta(minutes=5)
    assert not _snapshot_is_control_safe(complete, now)
    complete.timestamp = now
    complete.work_mode = None
    assert not _snapshot_is_control_safe(complete, now)


def _dispatch_connection(dispatch_rows=(), refresh=None, heartbeat=None):
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("CREATE TABLE octopus_dispatches (dispatch_start TEXT, dispatch_end TEXT, status TEXT, last_seen TEXT)")
    connection.execute("CREATE TABLE octopus_data_status (data_name TEXT PRIMARY KEY, updated_at TEXT)")
    connection.execute("CREATE TABLE service_heartbeat (service_name TEXT PRIMARY KEY, last_seen TEXT)")
    if refresh is not None:
        connection.execute("INSERT INTO octopus_data_status VALUES ('dispatches',?)", (refresh.isoformat(),))
    if heartbeat is not None:
        connection.execute("INSERT INTO service_heartbeat VALUES ('Octopus',?)", (heartbeat.isoformat(),))
    seen_at = (refresh or datetime.now(timezone.utc)).isoformat()
    connection.executemany(
        "INSERT INTO octopus_dispatches VALUES (?,?,?,?)",
        [(*row, seen_at) for row in dispatch_rows],
    )
    return connection


def _active_flex_state(connection):
    create_automation_tables(connection)
    repository = InverterStateRepository(connection)
    repository.set(
        requested_work_mode=WorkMode.MANUAL,
        requested_manual_mode=ManualMode.FORCE_CHARGE,
        restore_work_mode_to=WorkMode.PEAK_SHAVING,
        restore_manual_mode_to=ManualMode.IDLE,
        underlying_work_mode=WorkMode.SELF_USE,
        underlying_manual_mode=ManualMode.IDLE,
        phase=InverterRequestPhase.OVERRIDE,
        active=True,
        source="smart_flex",
    )
    return repository


def test_valid_empty_dispatch_result_confirms_end_and_restores_underlying():
    now = datetime.now(timezone.utc)
    connection = _dispatch_connection(refresh=now, heartbeat=now)
    data = _persisted_dispatches(connection, now=now)
    assert data.valid and data.dispatches.empty

    state_repo = _active_flex_state(connection)
    snapshot = SimpleNamespace(timestamp=now)
    ok, reason = apply_smartflex(
        snapshot, data, None, SmartFlexController(),
        SmartFlexOrchestrator(state_repo), state_repo,
    )
    assert ok and reason is None
    restored = state_repo.get()
    assert restored["source"] == "scheduler"
    assert restored["requested_work_mode"] == WorkMode.SELF_USE
    assert restored["restore_work_mode_to"] == WorkMode.PEAK_SHAVING


def test_confirmed_dispatch_end_from_fresh_rows_restores_even_if_vehicle_is_stale():
    now = datetime.now(timezone.utc)
    earlier_start = (now - timedelta(minutes=40)).isoformat()
    earlier_end = (now - timedelta(minutes=10)).isoformat()
    connection = _dispatch_connection(
        [(earlier_start, earlier_end, "Completed")], refresh=now, heartbeat=now
    )
    data = _persisted_dispatches(connection, now=now)
    assert data.valid
    state_repo = _active_flex_state(connection)
    apply_smartflex(
        SimpleNamespace(timestamp=now), data, None, SmartFlexController(),
        SmartFlexOrchestrator(state_repo), state_repo,
    )
    assert state_repo.get()["source"] == "scheduler"


def test_successful_refresh_omitting_old_planned_row_confirms_dispatch_end():
    now = datetime.now(timezone.utc)
    connection = _dispatch_connection(
        [((now - timedelta(minutes=10)).isoformat(),
          (now + timedelta(minutes=20)).isoformat(), "Planned")],
        refresh=now, heartbeat=now,
    )
    stale_observation = (now - timedelta(minutes=15)).isoformat()
    connection.execute("UPDATE octopus_dispatches SET last_seen=?", (stale_observation,))
    data = _persisted_dispatches(connection, now=now)
    assert data.valid and data.dispatches.empty
    state_repo = _active_flex_state(connection)
    apply_smartflex(
        SimpleNamespace(timestamp=now), data, None, SmartFlexController(),
        SmartFlexOrchestrator(state_repo), state_repo,
    )
    assert state_repo.get()["source"] == "scheduler"


def test_active_dispatch_with_stale_vehicle_status_preserves_smartflex_latch():
    now = datetime.now(timezone.utc)
    active_start = (now - timedelta(minutes=10)).isoformat()
    active_end = (now + timedelta(minutes=20)).isoformat()
    connection = _dispatch_connection(
        [(active_start, active_end, "Planned")], refresh=now, heartbeat=now
    )
    data = _persisted_dispatches(connection, now=now)
    state_repo = _active_flex_state(connection)
    before = state_repo.get()
    apply_smartflex(
        SimpleNamespace(timestamp=now), data, None, SmartFlexController(),
        SmartFlexOrchestrator(state_repo), state_repo,
    )
    assert state_repo.get() == before


def test_stale_vehicle_status_cannot_start_smartflex():
    now = datetime.now(timezone.utc)
    connection = _dispatch_connection(
        [((now - timedelta(minutes=5)).isoformat(),
          (now + timedelta(minutes=20)).isoformat(), "Planned")],
        refresh=now, heartbeat=now,
    )
    state_repo = InverterStateRepository(connection)
    create_automation_tables(connection)
    data = _persisted_dispatches(connection, now=now)
    ready, _reason = apply_smartflex(
        SimpleNamespace(timestamp=now, battery_soc_pct=40, work_mode=WorkMode.SELF_USE,
                        manual_mode=ManualMode.IDLE),
        data, None, SmartFlexController(), SmartFlexOrchestrator(state_repo), state_repo,
    )
    assert not ready
    assert state_repo.get() is None


def test_dispatch_table_query_failure_and_missing_table_are_unavailable():
    connection = sqlite3.connect(":memory:")
    assert not _persisted_dispatches(connection).valid

    class BrokenConnection:
        def execute(self, *_args):
            raise sqlite3.OperationalError("database is locked")

    assert not _persisted_dispatches(BrokenConnection()).valid


def test_dispatch_refresh_and_octopus_heartbeat_staleness_are_unavailable():
    now = datetime.now(timezone.utc)
    stale = now - timedelta(minutes=20)
    connection = _dispatch_connection(refresh=stale, heartbeat=now)
    assert not _persisted_dispatches(connection, now=now).valid
    connection.execute("UPDATE octopus_data_status SET updated_at=?", (now.isoformat(),))
    connection.execute("UPDATE service_heartbeat SET last_seen=?", (stale.isoformat(),))
    assert not _persisted_dispatches(connection, now=now).valid


def test_octopus_records_successful_empty_refresh_but_not_api_failure():
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as temp_dir:
        db_path = Path(temp_dir) / "octopus.sqlite"
        connection = sqlite3.connect(db_path)
        create_smartflex_vehicle_status_table(connection)
        connection.close()
        empty = pd.DataFrame(columns=[
            "dispatch_start", "dispatch_end", "scheduled_energy_kwh", "status"
        ])
        with patch.object(octopus_service, "get_intelligent_dispatches", return_value=empty), \
             patch.object(octopus_service, "get_completed_dispatches", return_value=empty), \
             patch.object(octopus_service, "get_connection", side_effect=lambda: sqlite3.connect(db_path)):
            octopus_service.update_dispatches(MagicMock())
        connection = sqlite3.connect(db_path)
        row = connection.execute(
            "SELECT updated_at FROM octopus_data_status WHERE data_name='dispatches'"
        ).fetchone()
        assert row is not None

        with patch.object(octopus_service, "get_intelligent_dispatches", side_effect=RuntimeError("offline")):
            with pytest.raises(RuntimeError, match="offline"):
                octopus_service.update_dispatches(MagicMock())
        assert connection.execute(
            "SELECT COUNT(*) FROM octopus_data_status WHERE data_name='dispatches'"
        ).fetchone()[0] == 1
        connection.close()
def test_stale_vehicle_record_and_stale_octopus_heartbeat_both_fail_closed():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("CREATE TABLE octopus_vehicle_status (id INTEGER, connected INTEGER, charging INTEGER, observed_at TEXT)")
    connection.execute("CREATE TABLE service_heartbeat (service_name TEXT, last_seen TEXT)")
    now = datetime.now(timezone.utc)
    fresh = now.isoformat()
    stale = (now - timedelta(minutes=20)).isoformat()
    connection.execute("INSERT INTO octopus_vehicle_status VALUES (1,1,1,?)", (stale,))
    connection.execute("INSERT INTO service_heartbeat VALUES ('Octopus',?)", (fresh,))
    assert _fresh_vehicle_status(connection, now=now) is None
    connection.execute("UPDATE octopus_vehicle_status SET observed_at=?", (fresh,))
    connection.execute("UPDATE service_heartbeat SET last_seen=?", (stale,))
    assert _fresh_vehicle_status(connection, now=now) is None


def test_restart_uses_persisted_smartflex_latch_and_restores_only_on_fresh_empty_feed():
    now = datetime.now(timezone.utc)
    state_connection = sqlite3.connect(":memory:")
    state_connection.row_factory = sqlite3.Row
    state_repo = _active_flex_state(state_connection)
    restart_controller = SmartFlexController()  # in-memory slot latch starts empty
    orchestrator = SmartFlexOrchestrator(state_repo)

    active_feed = DispatchData(True, pd.DataFrame([{
        "dispatch_start": now - timedelta(minutes=10),
        "dispatch_end": now + timedelta(minutes=20),
        "status": "Planned",
    }]))
    apply_smartflex(SimpleNamespace(timestamp=now), active_feed, None,
                    restart_controller, orchestrator, state_repo)
    assert state_repo.get()["source"] == "smart_flex"

    unavailable = DispatchData(False, pd.DataFrame(), "missing dispatch refresh")
    apply_smartflex(SimpleNamespace(timestamp=now), unavailable, None,
                    restart_controller, orchestrator, state_repo)
    assert state_repo.get()["source"] == "smart_flex"

    ended = DispatchData(True, pd.DataFrame(columns=["dispatch_start", "dispatch_end", "status"]))
    apply_smartflex(SimpleNamespace(timestamp=now), ended, None,
                    restart_controller, orchestrator, state_repo)
    assert state_repo.get()["source"] == "scheduler"


def test_database_path_resolution_prefers_explicit_path_and_preserves_legacy():
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as temp_dir:
        root = Path(temp_dir)
        home = root / "home"
        repo = root / "repo"
        legacy = repo / "app" / "data" / "energy_dashboard.db"
        legacy.parent.mkdir(parents=True)
        legacy.write_bytes(b"db")
        data_dir, _logs, db_path = resolve_paths(
            repo, platform_name="Linux", environ={}, home=home
        )
        assert db_path == legacy
        assert data_dir == legacy.parent

        explicit = root / "chosen" / "energy.db"
        _data, _logs, db_path = resolve_paths(
            repo, platform_name="Linux",
            environ={"ENERGY_DASHBOARD_DB": str(explicit)}, home=home,
        )
        assert db_path == explicit


def test_database_path_resolution_refuses_two_existing_databases():
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as temp_dir:
        root = Path(temp_dir)
        repo = root / "repo"
        new_db = repo / "data" / "energy_dashboard.db"
        old_db = repo / "app" / "data" / "energy_dashboard.db"
        new_db.parent.mkdir(parents=True)
        old_db.parent.mkdir(parents=True)
        new_db.write_bytes(b"new")
        old_db.write_bytes(b"old")
        with pytest.raises(RuntimeError, match="Multiple EnergyDashboard databases"):
            resolve_paths(repo, platform_name="Linux", environ={}, home=root / "home")


def test_windows_database_path_falls_back_to_previous_home_relative_location():
    with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[1]) as temp_dir:
        root = Path(temp_dir)
        home = root / "profile"
        repo = root / "checkout"
        old_db = home / "OffLine Documents" / "EnergyDashboard" / "data" / "energy_dashboard.db"
        old_db.parent.mkdir(parents=True)
        old_db.write_bytes(b"existing windows database")
        data_dir, _logs, selected = resolve_paths(
            repo, platform_name="Windows", environ={}, home=home
        )
        assert selected == old_db
        assert data_dir == old_db.parent


def _memory_automation():
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    create_automation_tables(connection)
    state_repo = InverterStateRepository(connection)
    return connection, state_repo


def _snapshot(at, work_mode=WorkMode.FEED_IN, manual_mode=ManualMode.IDLE, soc=50):
    return PowerFlowSnapshot(timestamp=at, work_mode=work_mode,
                             manual_mode=manual_mode, battery_soc_pct=soc)


def test_scheduler_entry_exit_and_telemetry_confirmed_restore():
    connection, state_repo = _memory_automation()
    schedules = ScheduleRepository(connection)
    schedules.save_period(SchedulePeriod(
        id=None, name="Charge", source="test", enabled=True,
        start_time="08:00", end_time="10:00",
        mode=InverterWorkMode.MANUAL_CHARGE, priority=1,
        updated_at=datetime.now(),
    ))
    scheduler = Scheduler(schedules, state_repo)
    snapshot = _snapshot(datetime.now(timezone.utc))
    scheduler.evaluate(snapshot, current_time="09:00")
    entered = state_repo.get()
    assert entered["source"] == "scheduler"
    assert entered["requested_work_mode"] == WorkMode.MANUAL
    assert entered["restore_work_mode_to"] == WorkMode.FEED_IN

    scheduler.evaluate(snapshot, current_time="10:01")
    restoring = state_repo.get()
    assert restoring["phase"] == InverterRequestPhase.RESTORE
    assert restoring["requested_work_mode"] == WorkMode.FEED_IN

    writer = MagicMock()
    InverterReconciler(state_repo, writer).process(snapshot)
    assert state_repo.get() is None
    writer.write_work_mode.assert_not_called()


def test_scheduler_restart_does_not_overwrite_pending_restoration():
    connection, state_repo = _memory_automation()
    schedules = ScheduleRepository(connection)
    schedules.save_period(SchedulePeriod(
        id=None, name="Charge", source="test", enabled=True,
        start_time="08:00", end_time="10:00",
        mode=InverterWorkMode.MANUAL_CHARGE, priority=1,
        updated_at=datetime.now(),
    ))
    state_repo.set(
        requested_work_mode=WorkMode.FEED_IN,
        requested_manual_mode=ManualMode.IDLE,
        restore_work_mode_to=None,
        restore_manual_mode_to=None,
        phase=InverterRequestPhase.RESTORE,
        active=True,
        source="scheduler",
    )
    before = state_repo.get()
    scheduler = Scheduler(schedules, state_repo)  # fresh process: inactive memory
    scheduler.evaluate(_snapshot(datetime.now(timezone.utc)), current_time="09:00")
    assert state_repo.get() == before
    assert not scheduler.is_active


def test_smartflex_overlaps_schedule_then_restores_and_schedule_exits():
    connection, state_repo = _memory_automation()
    schedules = ScheduleRepository(connection)
    schedules.save_period(SchedulePeriod(
        id=None, name="Scheduled charge", source="test", enabled=True,
        start_time="08:00", end_time="10:00",
        mode=InverterWorkMode.MANUAL_CHARGE, priority=1,
        updated_at=datetime.now(),
    ))
    scheduler = Scheduler(schedules, state_repo)
    now = datetime.now(timezone.utc)
    snapshot = _snapshot(now)
    scheduler.evaluate(snapshot, current_time="09:00")
    scheduler_state = state_repo.get()

    dispatch = pd.DataFrame([{
        "dispatch_start": now - timedelta(minutes=5),
        "dispatch_end": now + timedelta(minutes=20),
    }])
    controller = SmartFlexController()
    row = controller.get_active_dispatch(dispatch, now)
    assert controller.evaluate(snapshot, row, {"connected": True, "charging": True}) == "FORCE_CHARGE"
    orchestrator = SmartFlexOrchestrator(state_repo)
    orchestrator.apply_decision("FORCE_CHARGE", snapshot)
    flex_state = state_repo.get()
    assert flex_state["source"] == "smart_flex"
    assert flex_state["underlying_work_mode"] == scheduler_state["requested_work_mode"]
    assert flex_state["restore_work_mode_to"] == scheduler_state["restore_work_mode_to"]

    orchestrator.apply_decision("NORMAL", snapshot)
    restored_schedule = state_repo.get()
    assert restored_schedule["source"] == "scheduler"
    assert restored_schedule["requested_work_mode"] == scheduler_state["requested_work_mode"]
    assert restored_schedule["restore_work_mode_to"] == scheduler_state["restore_work_mode_to"]

    scheduler.evaluate(snapshot, current_time="10:01")
    assert state_repo.get()["phase"] == InverterRequestPhase.RESTORE


def test_reconciler_retries_with_backoff_and_confirms_on_following_telemetry():
    connection, state_repo = _memory_automation()
    state_repo.set(WorkMode.MANUAL, ManualMode.FORCE_CHARGE, None, None,
                   phase=InverterRequestPhase.OVERRIDE, source="scheduler")
    writer = MagicMock()
    writer.write_work_mode.side_effect = [RuntimeError("temporary failure"), None]
    reconciler = InverterReconciler(state_repo, writer)
    snapshots = iter([0, 30, 61])
    with patch("app.solax.backend.inverter.inverter_reconciler.time.monotonic",
               side_effect=lambda: next(snapshots)):
        with pytest.raises(RuntimeError, match="temporary failure"):
            reconciler.process(_snapshot(datetime.now(timezone.utc)))
        assert state_repo.get() is not None
        reconciler.process(_snapshot(datetime.now(timezone.utc)))
        assert writer.write_work_mode.call_count == 1
        reconciler.process(_snapshot(datetime.now(timezone.utc)))
    assert writer.write_work_mode.call_count == 2
    assert state_repo.get() is not None  # write return alone does not complete
    reconciler.process(_snapshot(datetime.now(timezone.utc), WorkMode.MANUAL, ManualMode.FORCE_CHARGE))
    assert state_repo.get() is None


def test_reconciler_defers_superseded_request_and_cannot_clear_newer_state():
    old = {"requested_work_mode": WorkMode.MANUAL,
           "requested_manual_mode": ManualMode.FORCE_CHARGE,
           "restore_work_mode_to": None, "restore_manual_mode_to": None,
           "underlying_work_mode": None, "underlying_manual_mode": None,
           "active": True, "source": "scheduler", "phase": InverterRequestPhase.OVERRIDE,
           "updated_at": "old"}
    new = {**old, "requested_work_mode": WorkMode.SELF_USE, "updated_at": "new"}

    class ChangesDuringRead:
        def __init__(self): self.reads = 0
        def get(self):
            self.reads += 1
            return old if self.reads == 1 else new

    writer = MagicMock()
    InverterReconciler(ChangesDuringRead(), writer).process(_snapshot(datetime.now(timezone.utc)))
    writer.write_work_mode.assert_not_called()

    connection, state_repo = _memory_automation()
    state_repo.set(WorkMode.MANUAL, ManualMode.FORCE_CHARGE, None, None,
                   phase=InverterRequestPhase.OVERRIDE, source="scheduler")
    stale = state_repo.get()
    state_repo.set(WorkMode.SELF_USE, None, WorkMode.FEED_IN, None,
                   phase=InverterRequestPhase.OVERRIDE, source="scheduler")
    assert not state_repo.clear_if_current(stale)
    assert state_repo.get()["requested_work_mode"] == WorkMode.SELF_USE
