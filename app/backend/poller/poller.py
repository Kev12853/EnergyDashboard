# Poller Responsibilities
#
# 1. Poll the inverter and obtain the current snapshot.
#
# 2. Persist the snapshot for historical storage.
#
# 3. Run the scheduler.
#
#    The scheduler determines the desired inverter state and
#    records it in the inverter_state table.
#
# 4. Run the reconciler.
#
#    The reconciler compares:
#
#        Desired State (inverter_state)
#
#    with
#
#        Actual State (snapshot)
#
#    and performs inverter writes only when necessary.
#
# The poller never decides which inverter mode should be active.
# It simply orchestrates the monitoring and control pipeline.


import os
import time

from app.backend.automation.automation_repository import ScheduleRepository
from app.backend.automation.inverter_state_repository import InverterStateRepository
from app.backend.automation.scheduler import Scheduler

from app.backend.common.logging_utils import setup_logger

from app.backend.inverter.inverter_reconciler import InverterReconciler

from app.backend.notifications.email_sender import EmailSender
from app.backend.notifications.pushover_sender import PushoverSender
from app.backend.notifications.work_mode_email import send_work_mode_email
from app.backend.notifications.work_mode_push import send_work_mode_push

from app.backend.polling.inverter_service import InverterPollingService

from app.backend.storage.db import get_connection
from app.backend.storage.schema import create_all_tables

from app.config.email_config import APP_PASSWORD, EMAIL_ADDRESS
from app.config.notification_config import PUSHOVER_API_TOKEN, PUSHOVER_USER_KEY
from app.config.solax_config import COMMUNICATION_TIMEOUT

from app.solax.storage.storage_repository import TelemetryRepository
from app.solax.telemetry.work_mode_monitor import WorkModeMonitor

from utils.inverter_operations import determine_required_actions


email_sender = EmailSender(
    smtp_server="smtp.gmail.com",
    smtp_port=465,
    username=EMAIL_ADDRESS,
    password=APP_PASSWORD,
    sender=EMAIL_ADDRESS,
    recipient=EMAIL_ADDRESS,
)

logger = setup_logger("Poller")



def main():

    try:

        logger.info(f"Poller starting, PID = {os.getpid()}")

        last_heartbeat = 0

        failure_notification_sent = False
        communication_lost = False

        connection = get_connection()

        create_all_tables(connection)

        service = InverterPollingService()

        telemetry_repository = TelemetryRepository(connection)
        scheduler_repository = ScheduleRepository(connection)
        inverter_state_repository = InverterStateRepository(connection)
        work_mode_monitor = WorkModeMonitor()

        pushover = PushoverSender(
            api_token=PUSHOVER_API_TOKEN,
            user_key=PUSHOVER_USER_KEY,
        )

        scheduler = Scheduler(
            scheduler_repository,
            inverter_state_repository,
        )
        logger.info("Created Scheduler")

        reconciler = InverterReconciler(
            inverter_state_repository,
            service,
        )
        logger.info("Created Reconciler")


        # Main Loop
        try:
            logger.info("Entering Main Loop")

            while True:
                try:
                    # ============================================================
                    # STAGE 1 - POLL THE INVERTER
                    #
                    # Read the current inverter state from the Solax inverter.
                    #
                    # This produces a snapshot representing the ACTUAL state
                    # of the inverter at this moment.
                    #
                    # ============================================================
                    snapshot = service.poll()
                    logger.info("Got Snapshot")
                    logger.info(
                        f"Current SnapShot Timestamp = {snapshot.timestamp}, WorkMode = {snapshot.work_mode}"
                    )
                    # Get current state of the inverter
                    snapshot_work_mode = snapshot.work_mode

                    # ============================================================
                    # STAGE 2 - WORK MODE CHANGE DETECTION
                    #
                    # Detect inverter work mode changes and generate
                    # notifications.
                    #
                    # This is independent of scheduling and reconciliation.
                    #
                    # ============================================================

                    change = work_mode_monitor.update(
                        snapshot_work_mode,
                    )
                    if change:  # the inverter has been changed so notify the user
                        try:
                            logger.info(
                                f"Workmode has changed. Sending messages: {snapshot_work_mode}"
                            )
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

                    if communication_lost:
                        logger.info("Communication restored")
                        communication_lost = False

                    last_successful_poll = time.time()

                    if failure_notification_sent:
                        pushover.send_push(
                            title="🟢 Energy Dashboard",
                            message=(
                                "Communication with the SolaX inverter has been restored."
                            ),
                        )

                        failure_notification_sent = False

                    # ============================================================
                    # STAGE 3 - SAVE SNAPSHOT
                    #
                    # Persist the current inverter state for dashboards,
                    # graphs and historical analysis.
                    #
                    # ============================================================
                    # todo guard agains db locks

                    telemetry_repository.save_snapshot(snapshot)
                    logger.info("Saved Snapshot")

                    """
                    Check the scheduler to see if any schedules should be run.
    
                    This is the start of gathering evidence about whether the
                    inverter state should change.
    
                    If evaluate() determines that a different inverter state is
                    required, it writes the desired state into the inverter_state
                    table.
    
                    The inverter_state table is effectively:
                        "What state should the inverter be in right now?"
    
                    It is NOT:
                        "What state is the inverter actually in right now?"
    
                    The actual inverter state always comes from a live poll of
                    the inverter (snapshot).
    
                    The poller later compares:
                        Desired state (inverter_state)
                    against:
                        Actual state (snapshot)
                    and decides whether any action is required.
                    """
                    # ============================================================
                    # STAGE 4 - EVALUATE SCHEDULES
                    #
                    # Examine all enabled schedules.
                    #
                    # If a schedule determines that the inverter SHOULD be in
                    # a different state, the scheduler writes the desired state
                    # into the inverter_state table.
                    #
                    # The scheduler does NOT communicate with the inverter.
                    #
                    # ============================================================

                    logger.info("Running Scheduler")
                    logger.info(f"Before scheduler: {inverter_state_repository.get()}")

                    scheduler.evaluate(snapshot)

                    logger.info(f"After scheduler: {inverter_state_repository.get()}")
                    logger.info("Scheduler Complete")

                    # ============================================================
                    # STAGE 5 - RECONCILE DESIRED VS ACTUAL STATE
                    #
                    # Desired State:
                    #
                    #     inverter_state table
                    #
                    # Actual State:
                    #
                    #     snapshot
                    #
                    # If they differ:
                    #
                    #     action_required = True
                    #
                    # If they match:
                    #
                    #     action_required = False
                    #
                    # ============================================================

                    reconciler.process(snapshot)
                    logger.info("Reconciler Complete")

                    now = time.time()

                    if now - last_heartbeat >= 300: #
                        logger.info(f"Poller healthy (PID={os.getpid()})")
                        last_heartbeat = now

                        logger.info(snapshot.work_mode)

                except Exception as exc:
                    logger.warning(f"Inverter communication lost: {exc}")

                    communication_lost = True
                    # Fresh connections are established on every poll cycle, so simply wait and try again.
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
            service.close()
            connection.close()
            logger.info("Poller stopped")

    except Exception:
        logger.exception("Poller terminated unexpectedly")
        raise

    finally:
        logger.info("Poller stopping")

if __name__ == "__main__":
    main()
