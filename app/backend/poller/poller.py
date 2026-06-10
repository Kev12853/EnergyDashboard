import time
from app.backend.automation.repository import AutomationRepository
from app.backend.automation.scheduler import Scheduler
from app.backend.inverter.controller import InverterController

from app.backend.notifications.email_sender import EmailSender


from app.backend.notifications.work_mode_email import send_work_mode_email
from app.backend.notifications.work_mode_push import send_work_mode_push

from app.solax.telemetry.modbus_client import (
    SolaxModbusClient,
)

from app.solax.storage.repository import (
    TelemetryRepository,
)

from app.backend.storage.db import (
    get_connection,
)

from app.backend.storage.schema import (
    create_all_tables,
)
from app.solax.telemetry.work_mode_monitor import WorkModeMonitor

from app.backend.common.logging_utils import (
    setup_logger,
)

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
        host="192.168.1.66",
    )

    repository = TelemetryRepository(connection)

    logger.info("Starting to Poll")
    import os

    logger.info(f"Starting poller PID={os.getpid()}")
    automation_repo = AutomationRepository(connection)

    controller = InverterController(client)

    work_mode_monitor = WorkModeMonitor()

    scheduler = Scheduler(
        automation_repo,
        controller,
    )

    from app.backend.notifications.pushover_sender import PushoverSender

    pushover = PushoverSender(
        api_token=PUSHOVER_API_TOKEN,
        user_key=PUSHOVER_USER_KEY,
    )

    while True:
        try:
            # mode = controller.get_work_mode()
            # change = work_mode_monitor.update(
            #     mode,
            # )
            #if change:
            #     try:
            #         logger.info(f"Current work mode: {mode}")
            #
            #         send_work_mode_email(
            #             email_sender,
            #             change,
            #         )
            #         send_work_mode_push(
            #             pushover,
            #             change,
            #         )
            #
            #     except Exception as exc:
            #         logger.exception(f"Email failed: {exc}")
            #
            snapshot = client.poll_once()

            #snapshot.work_mode = mode

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

            try:
                logger.info("Attempting reconnect")

                client.reconnect()

                logger.info("Communication restored")
                time.sleep(2)
                continue

            except Exception:
                logger.exception("Reconnect failed")

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
        time.sleep(5)


if __name__ == "__main__":
    main()
