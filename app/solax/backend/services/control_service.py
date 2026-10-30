"""Independent SolaX schedule, Smart Flex and inverter-control process.

The service intentionally polls Modbus itself before evaluating state. A cloud
sample or stale row in SQLite can therefore never authorise an inverter write.
"""
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone

import pandas as pd

from app.connections.connection import get_connection
from app.config.solax_config import CONTROL_MAX_TELEMETRY_AGE_SECONDS
from app.config.solax_config import SOLAX_HOST, SOLAX_PORT
from app.enums.service_enums import ServiceName
from app.logging.logger import setup_logger
from app.solax.backend.automation.automation_repository import ScheduleRepository
from app.solax.backend.automation.inverter_state_repository import InverterStateRepository
from app.solax.backend.automation.scheduler import Scheduler
from app.solax.backend.automation.smart_flex_orchestrator import SmartFlexOrchestrator
from app.solax.backend.inverter.inverter_reconciler import InverterReconciler
from app.solax.backend.polling.inverter_service import InverterPollingService
from app.solax.backend.smart_flex.smart_flex_controller import SmartFlexController
from app.solax.backend.storage.schema import create_solax_tables
from app.solax.backend.storage.service_heartbeat_repository import ServiceHeartbeatRepository
from app.solax.telemetry.modbus_service import SolaxModbusService

logger = setup_logger("SolaX Control")
OCTOPUS_DATA_MAX_AGE_SECONDS = 600


@dataclass(frozen=True)
class DispatchData:
    """Persisted dispatch view plus whether an empty result is authoritative."""

    valid: bool
    dispatches: pd.DataFrame
    reason: str | None = None


def _as_utc(value):
    stamp = datetime.fromisoformat(value) if isinstance(value, str) else value
    if stamp.tzinfo is None:
        stamp = stamp.astimezone()
    return stamp.astimezone(timezone.utc)


class _ControlInverterAdapter:
    """Control-only write surface around the shared read/poll implementation."""
    def __init__(self, polling_service, write_service):
        self.polling_service = polling_service
        self.write_service = write_service

    def write_work_mode(self, work_mode, manual_mode):
        return self.write_service.write_work_mode(work_mode, manual_mode)


def _persisted_dispatches(connection, now=None, max_age_seconds=OCTOPUS_DATA_MAX_AGE_SECONDS):
    """Return valid dispatch data only after a recent successful Octopus refresh.

    An empty DataFrame is authoritative only when the Octopus process recorded
    a successful dispatch query recently. Missing tables, stale refresh markers,
    stale service heartbeats and SQL/parse failures are represented as invalid.
    """
    now = now or datetime.now(timezone.utc)
    try:
        refresh = connection.execute(
            "SELECT updated_at FROM octopus_data_status WHERE data_name='dispatches'"
        ).fetchone()
        heartbeat = connection.execute(
            "SELECT last_seen FROM service_heartbeat WHERE service_name=?",
            (ServiceName.OCTOPUS.value,),
        ).fetchone()
        if refresh is None or heartbeat is None:
            return DispatchData(False, pd.DataFrame(), "Octopus dispatch refresh status is missing")
        refresh_age = (now.astimezone(timezone.utc) - _as_utc(refresh["updated_at"])).total_seconds()
        heartbeat_age = (now.astimezone(timezone.utc) - _as_utc(heartbeat["last_seen"])).total_seconds()
        if min(refresh_age, heartbeat_age) < -30:
            return DispatchData(False, pd.DataFrame(), "Octopus dispatch timestamps are future dated")
        if max(refresh_age, heartbeat_age) > max_age_seconds:
            return DispatchData(False, pd.DataFrame(), "Octopus dispatch data or heartbeat is stale")
        rows = connection.execute(
            "SELECT dispatch_start, dispatch_end, status, last_seen FROM octopus_dispatches "
            "WHERE lower(status)='planned'"
        ).fetchall()
    except Exception:
        return DispatchData(False, pd.DataFrame(), "Unable to read persisted Octopus dispatch data")
    try:
        frame = pd.DataFrame([dict(row) for row in rows], columns=[
            "dispatch_start", "dispatch_end", "status", "last_seen"
        ])
        if not frame.empty:
            frame["dispatch_start"] = pd.to_datetime(frame["dispatch_start"], utc=True, errors="raise")
            frame["dispatch_end"] = pd.to_datetime(frame["dispatch_end"], utc=True, errors="raise")
            # Old rows remain in the history table after an API refresh omits
            # them. Only recently observed planned rows represent current
            # dispatches; completed rows remain historical and cannot start
            # or extend a Smart Flex override.
            frame["last_seen"] = pd.to_datetime(frame["last_seen"], utc=True, errors="raise")
            cutoff = pd.Timestamp(now.astimezone(timezone.utc)) - pd.Timedelta(seconds=max_age_seconds)
            frame = frame[(frame["status"].str.casefold() == "planned") & (frame["last_seen"] >= cutoff)]
        else:
            frame = frame.drop(columns=["last_seen"])
        return DispatchData(True, frame)
    except Exception:
        return DispatchData(False, pd.DataFrame(), "Persisted Octopus dispatch rows are invalid")


def _fresh_vehicle_status(connection, max_age_seconds=600, now=None):
    try:
        row = connection.execute(
            "SELECT connected, charging, observed_at FROM octopus_vehicle_status WHERE id=1"
        ).fetchone()
        beat = connection.execute(
            "SELECT last_seen FROM service_heartbeat WHERE service_name=?",
            (ServiceName.OCTOPUS.value,),
        ).fetchone()
        if row is None or beat is None:
            return None
        observed = datetime.fromisoformat(row["observed_at"])
        heartbeat = datetime.fromisoformat(beat["last_seen"])
        if observed.tzinfo is None:
            observed = observed.astimezone()
        if heartbeat.tzinfo is None:
            heartbeat = heartbeat.astimezone()
        now = now or datetime.now(timezone.utc)
        ages = ((now - observed.astimezone(timezone.utc)).total_seconds(),
                (now - heartbeat.astimezone(timezone.utc)).total_seconds())
        if max(ages) > max_age_seconds or min(ages) < -30:
            return None
        return {"connected": bool(row["connected"]), "charging": bool(row["charging"])}
    except Exception:
        return None


def apply_smartflex(snapshot, dispatch_data, vehicle_status, controller,
                    orchestrator, state_repo):
    """Apply Smart Flex only when dispatch data is authoritative.

    Unknown dispatch status preserves an active request. A fresh valid empty
    dispatch set proves the active slot has ended and allows restoration.
    Vehicle data is required to start a new request, but not to end a slot
    whose dispatch end is established by the current Octopus dispatch feed.
    """
    if not dispatch_data.valid:
        return False, dispatch_data.reason or "Octopus dispatch data unavailable"

    dispatch = controller.get_active_dispatch(dispatch_data.dispatches, snapshot.timestamp)
    state = state_repo.get()
    smartflex_owned = bool(state and state.get("source") == "smart_flex")
    active_override = bool(smartflex_owned and state.get("phase") == "OVERRIDE")

    if active_override:
        if dispatch is None:
            orchestrator.apply_decision("NORMAL", snapshot)
            controller.reset()
        # An active dispatch is the durable latch, including after restart.
        if dispatch is not None and vehicle_status is None:
            return False, "Vehicle status is missing or stale; active slot remains latched"
        return True, None

    if smartflex_owned:
        # A restore request is already in flight. Do not replace its lifecycle.
        return True, None

    if dispatch is None:
        return True, None
    if vehicle_status is None:
        return False, "Vehicle status is missing or stale; Smart Flex start refused"

    decision = controller.evaluate(snapshot, dispatch, vehicle_status)
    orchestrator.apply_decision(decision, snapshot)
    return True, None


def _snapshot_is_control_safe(snapshot, now=None):
    """A control decision requires complete, recent telemetry from local poll()."""
    if (snapshot is None or snapshot.timestamp is None or snapshot.work_mode is None
            or snapshot.manual_mode is None or snapshot.battery_soc_pct is None):
        return False
    sample_time = snapshot.timestamp
    if sample_time.tzinfo is None:
        sample_time = sample_time.astimezone()
    now = now or datetime.now(timezone.utc)
    age = (now - sample_time.astimezone(timezone.utc)).total_seconds()
    return -10 <= age <= CONTROL_MAX_TELEMETRY_AGE_SECONDS


def main():
    logger.info("SolaX control starting, PID=%s", os.getpid())
    connection = get_connection()
    create_solax_tables(connection)
    heartbeat = ServiceHeartbeatRepository(connection)
    state_repo = InverterStateRepository(connection)
    scheduler = Scheduler(ScheduleRepository(connection), state_repo)
    flex = SmartFlexController()
    orchestrator = SmartFlexOrchestrator(state_repo)
    service = InverterPollingService()
    write_service = SolaxModbusService(host=SOLAX_HOST, port=SOLAX_PORT)
    reconciler = InverterReconciler(state_repo, _ControlInverterAdapter(service, write_service))
    try:
        while True:
            try:
                # Only this fresh successful local Modbus sample gates all decisions.
                snapshot = service.poll()
                if not _snapshot_is_control_safe(snapshot):
                    raise ValueError("Local Modbus telemetry is stale, future dated, or missing control-critical fields")
                scheduler.evaluate(snapshot)

                dispatch_data = _persisted_dispatches(connection)
                vehicle_status = _fresh_vehicle_status(connection)
                external_ready, external_issue = apply_smartflex(
                    snapshot, dispatch_data, vehicle_status, flex, orchestrator, state_repo
                )
                reconciler.process(snapshot)
                heartbeat.save_heartbeat(
                    ServiceName.CONTROL,
                    "Running" if external_ready else "Warning",
                    external_issue or "Fresh local Modbus telemetry; control evaluated",
                )
            except Exception as exc:
                logger.exception("Control evaluation failed; writes suspended until a valid local poll")
                heartbeat.save_heartbeat(ServiceName.CONTROL, "Warning", str(exc))
            time.sleep(25)
    except KeyboardInterrupt:
        logger.info("SolaX control stopping")
    finally:
        try:
            service.close()
        finally:
            write_service.close()
            connection.close()


if __name__ == "__main__":
    main()
