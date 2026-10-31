"""Standalone, monitoring-only SolaX Modbus poller."""
import os
import time

from app.config.email_config import APP_PASSWORD, EMAIL_ADDRESS
from app.config.notification_config import PUSHOVER_API_TOKEN, PUSHOVER_USER_KEY
from app.config.solax_config import COMMUNICATION_TIMEOUT
from app.connections.connection import get_connection
from app.enums.service_enums import ServiceName
from app.logging.logger import setup_logger
from app.solax.backend.notifications.email_sender import EmailSender
from app.solax.backend.notifications.pushover_sender import PushoverSender
from app.solax.backend.notifications.work_mode_email import send_work_mode_email
from app.solax.backend.notifications.work_mode_push import send_work_mode_push
from app.solax.backend.polling.inverter_service import InverterPollingService
from app.solax.backend.storage.schema import create_solax_tables
from app.solax.storage.solax_repository import TelemetryRepository
from app.solax.telemetry.work_mode_monitor import WorkModeMonitor

logger = setup_logger("Poller")


def _heartbeat(repository, status, message):
    try:
        repository.save_heartbeat(ServiceName.POLLER, status, message)
    except Exception:
        logger.exception("Unable to persist poller heartbeat")


def main():
    """Run the monitoring poll loop, persist local telemetry and heartbeat status, and send outage/work-mode notifications. This entry point never writes inverter registers."""
    logger.info("SolaX monitoring poller starting, PID=%s", os.getpid())
    connection = get_connection()
    create_solax_tables(connection)
    repository = TelemetryRepository(connection)
    service = InverterPollingService()
    monitor = WorkModeMonitor()
    push = PushoverSender(api_token=PUSHOVER_API_TOKEN, user_key=PUSHOVER_USER_KEY)
    email = EmailSender(smtp_server="smtp.gmail.com", smtp_port=465,
                        username=EMAIL_ADDRESS, password=APP_PASSWORD,
                        sender=EMAIL_ADDRESS, recipient=EMAIL_ADDRESS)
    last_success = time.monotonic()
    outage_notified = False
    in_outage = False
    try:
        while True:
            try:
                snapshot = service.poll()
            except Exception as exc:
                in_outage = True
                downtime = time.monotonic() - last_success
                _heartbeat(repository, "Warning",
                           f"Local Modbus poll failed; outage {int(downtime)}s: {exc}")
                if downtime >= COMMUNICATION_TIMEOUT and not outage_notified:
                    try:
                        push.send_push(title="🔴 Energy Dashboard",
                                       message="No successful local Modbus communication with the SolaX inverter for 30 minutes. Cloud readings are monitoring-only.")
                        outage_notified = True
                    except Exception:
                        logger.exception("Outage notification failed")
                time.sleep(10)
                continue

            try:
                repository.save_snapshot(snapshot, source="modbus")
            except Exception as exc:
                # Database failures are not inverter communication failures.
                logger.exception("Unable to persist local telemetry")
                _heartbeat(repository, "Error", f"Telemetry database error: {exc}")
                time.sleep(10)
                continue
            last_success = time.monotonic()
            _heartbeat(repository, "Running", "Local Modbus telemetry current")
            change = monitor.update(snapshot.work_mode)
            if change:
                try:
                    send_work_mode_email(email, change)
                    send_work_mode_push(push, change)
                except Exception:
                    logger.exception("Work mode notification failed")
            if in_outage:
                logger.info("Local Modbus communication restored")
                in_outage = False
            if outage_notified:
                try:
                    push.send_push(title="🟢 Energy Dashboard",
                                   message="Communication with the SolaX inverter has been restored.")
                except Exception:
                    logger.exception("Recovery notification failed")
                outage_notified = False
            time.sleep(25)
    except KeyboardInterrupt:
        logger.info("Poller stopping")
    finally:
        service.close()
        connection.close()


if __name__ == "__main__":
    main()
