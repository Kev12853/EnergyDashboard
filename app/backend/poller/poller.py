import time
import os

from app.backend.automation.repository import AutomationRepository
from app.backend.automation.scheduler import Scheduler
from app.backend.inverter.controller import InverterController
from app.backend.notifications.email_sender import EmailSender
from app.backend.notifications.work_mode_email import send_work_mode_email
from app.backend.notifications.work_mode_push import send_work_mode_push
from app.backend.notifications.pushover_sender import PushoverSender

from app.backend.storage.db import get_connection
from app.backend.storage.schema import create_all_tables
from app.backend.common.logging_utils import setup_logger

from app.solax.storage.repository import TelemetryRepository
from app.solax.telemetry.modbus_client import SolaxModbusClient
from app.solax.telemetry.work_mode_monitor import WorkModeMonitor


COMMUNICATION_TIMEOUT = 1800  # 1800 = 30 minutes

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

EMAIL_ADDRESS = "kev12853@gmail.com"
APP_PASSWORD = "ulnr ftnv qxvc zlvn"

PUSHOVER_API_TOKEN = "azgnthk84czu8ujxqmjqkoday1qi78"
PUSHOVER_USER_KEY = "u4qekmin97kp8tfstg85au6qjoaxz5"

email_sender = EmailSender(
    smtp_server="smtp.gmail.com",
    smtp_port=465,
    username=EMAIL_ADDRESS,
    password=APP_PASSWORD,
    sender=EMAIL_ADDRESS,
    recipient=EMAIL_ADDRESS,
)


def main():

    logger = setup_logger(
        "poller",
    )
    logger.info("Poller starting")

    last_heartbeat = 0

    last_successful_poll = time.time()

    failure_notification_sent = False

    connection = get_connection()

    create_all_tables(connection)

    client = SolaxModbusClient(
        host="192.168.1.67",
    )
    
    time.sleep(5)

    repository = TelemetryRepository(connection)

    logger.info("Starting to Poll")

    logger.info(f"Starting poller PID={os.getpid()}")
    automation_repo = AutomationRepository(connection)

    controller = InverterController(client)

    work_mode_monitor = WorkModeMonitor()

    scheduler = Scheduler(
        automation_repo,
        controller,
    )

    pushover = PushoverSender(
        api_token=PUSHOVER_API_TOKEN,
        user_key=PUSHOVER_USER_KEY,
    )
    communication_lost = False
    try:
        while True:
            try:
                snapshot = poll_inverter(
                    client,
                    controller,
                )

                mode = snapshot.work_mode
                change = work_mode_monitor.update(
                    mode,
                )
                if change:
                    try:
                        logger.info(f"Current work mode: {mode}")

                        send_work_mode_email(
                            email_sender,
                            change,
                        )
                        send_work_mode_push(
                            pushover,
                            change,
                        )

                    except Exception as exc:
                        logger.exception(f"Email failed: {exc}")

                # #napshot = client.poll_once()

                if communication_lost:
                    logger.info("Communication restored")

                    communication_lost = False

                # snapshot.work_mode = mode

                last_successful_poll = time.time()

                if failure_notification_sent:
                    pushover.send_push(
                        title="🟢 Energy Dashboard",
                        message=(
                            "Communication with the SolaX inverter has been restored."
                        ),
                    )

                    failure_notification_sent = False

                repository.save_snapshot(snapshot)
                scheduler.evaluate()

                now = time.time()

                if now - last_heartbeat >= 300:
                    logger.info(f"Poller healthy (PID={os.getpid()})")
                    last_heartbeat = now
                    #
                    logger.info(snapshot.work_mode)

            except Exception as exc:
                logger.warning(f"Inverter communication lost: {exc}")

                communication_lost = True
                # Fresh connections are established
                # on every poll cycle, so simply
                # wait and try again.
                time.sleep(10)
                continue

            downtime = time.time() - last_successful_poll

            if downtime >= COMMUNICATION_TIMEOUT and not failure_notification_sent:
                try:
                    pushover.send_push(
                        title="🔴 Energy Dashboard",
                        message=(
                            "No successful communication "
                            "with the SolaX inverter "
                            "for 30 minutes.\n\n"
                            "Automatic recovery "
                            "continues."
                        ),
                    )

                except Exception:
                    logger.exception("Unable to send outage notification")

                failure_notification_sent = True
            if communication_lost:
                time.sleep(10)
            else:
                time.sleep(25)

    except KeyboardInterrupt:
        logger.info("Poller stopping")
    finally:
        logger.info("Poller stopping")
        client.close()
        connection.close()
        logger.info("Poller stopped")


def close(self):

    try:
        self.client.close()

    except Exception:
        pass


def poll_inverter(
    client,
    controller,
):

    mode = controller.get_work_mode()

    snapshot = client.poll_once()

    snapshot.work_mode = mode

    return snapshot


if __name__ == "__main__":
    main()
