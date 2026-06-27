import os
import time

from app.backend.automation.automation_repository import ScheduleRepository
from app.backend.automation.inverter_state_repository import InverterStateRepository
from app.backend.automation.scheduler import Scheduler
from app.backend.inverter.inverter_controller import InverterController
from app.backend.notifications.email_sender import EmailSender
from app.backend.notifications.pushover_sender import PushoverSender
from app.backend.notifications.work_mode_email import send_work_mode_email
from app.backend.notifications.work_mode_push import send_work_mode_push
from app.backend.polling.inverter_service import InverterPollingService
from app.backend.storage.db import get_connection
from app.backend.storage.schema import create_all_tables
from app.solax.storage.storage_repository import TelemetryRepository
from app.solax.telemetry.work_mode_monitor import WorkModeMonitor
from app.backend.common.logging_utils import setup_logger
from app.backend.inverter.inverter_reconciler import InverterReconciler
from utils.inverter_operations import determine_required_actions

COMMUNICATION_TIMEOUT = 1800  # 1800 = 30 minutes

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_ADDRESS = "kev12853@gmail.com"
APP_PASSWORD = "ulnr ftnv qxvc zlvn"

PUSHOVER_API_TOKEN = "azgnthk84czu8ujxqmjqkoday1qi78"
PUSHOVER_USER_KEY = "u4qekmin97kp8tfstg85au6qjoaxz5"

WORK_MODE_SELF_USE = 0
WORK_MODE_FEED_IN = 1
WORK_MODE_BACKUP = 2
WORK_MODE_MANUAL = 3

MANUAL_MODE_IDLE = 0
MANUAL_MODE_FORCE_CHARGE = 1
MANUAL_MODE_FORCE_DISCHARGE = 2

email_sender = EmailSender(
    smtp_server="smtp.gmail.com",
    smtp_port=465,
    username=EMAIL_ADDRESS,
    password=APP_PASSWORD,
    sender=EMAIL_ADDRESS,
    recipient=EMAIL_ADDRESS,
)

logger = setup_logger("EnergyDashboard_Poller")

# ============================================================
# POLLER ARCHITECTURE
# ============================================================
#
# The poller has two independent responsibilities:
#
# 1. MONITORING
#
#    Poll the inverter and record its ACTUAL state.
#
#    Inverter
#        ↓
#    Snapshot
#        ↓
#    Database
#
#    The snapshot is always considered the source of truth
#    for the inverter's current state.
#
#
# 2. RECONCILIATION
#
#    Compare the ACTUAL inverter state against the DESIRED
#    inverter state requested by the scheduler.
#
#    Scheduler
#        ↓
#    inverter_state table
#        ↓
#    Desired State
#
#    compared with
#
#    Snapshot
#        ↓
#    Actual State
#
#    If they differ:
#
#        action_required = True
#
#    If they match:
#
#        action_required = False
#
#
# IMPORTANT
#
#    inverter_state does NOT represent the current inverter
#    state.
#
#    inverter_state represents the state the scheduler
#    believes the inverter SHOULD currently be in.
#
# ============================================================

# =====================================================
# INVERTER STATE TERMINOLOGY
# =====================================================
#
# snapshot
# --------
# Current live state read from the inverter.
#
# snapshot.work_mode
#     Human-readable mode reported by the inverter.
#
# Examples:
#     "Self Use"
#     "Force Charge"
#     "Force Discharge"
#
#
# =====================================================
# INVERTER_STATE TABLE
# =====================================================
#
# The inverter_state table stores the DESIRED inverter
# state.
#
# It is NOT the actual inverter state.
#
# Actual inverter state always comes from:
#
#     snapshot
#
# ***********************The scheduler writes requests into inverter_state.***************************
#
# The poller reads inverter_state and compares the
# requested state against the actual inverter state.
#
#
# Example:
#
# Scheduler:
#
#     "I want Force Discharge"
#
# inverter_state:
#
#     work_mode   = 3
#     manual_mode = 2
#
# Inverter:
#
#     Self Use
#
# Poller:
#
#     Mismatch detected
#     Action required
#
#
# Example:
#
# Scheduler:
#
#     "I want Force Discharge"
#
# inverter_state:
#
#     work_mode   = 3
#     manual_mode = 2
#
# Inverter:
#
#     Force Discharge
#
# Poller:
#
#     Requested state already achieved
#
#
# =====================================================
# PENDING
# =====================================================
#
# pending is the current row read from inverter_state.
#
# Example:
#
#     pending = inverter_state_repo.get()
#
# Returns:
#
#     {
#         "work_mode": 3,
#         "manual_mode": 2,
#         "source": "scheduler",
#         "updated_at": "2026-06-21T08:30:00"
#     }
#
#
# pending["requested_work_mode"]
#
#     Raw inverter work mode register value.
#
#     0 = Self Use
#     1 = Feed In Priority
#     2 = Backup
#     3 = Manual
#
#
# pending["requested_manual_mode"]
#
#     Raw inverter manual mode register value.
#
#     0 = Manual
#     1 = Force Charge
#     2 = Force Discharge
#
#
# pending["source"]
#
#     Who created the request.
#
# Examples:
#
#     "scheduler"
#     "user"
#     "test"
#
#
# pending["updated_at"]
#
#     When the request was created or last modified.
#
#
# IMPORTANT
#
# pending contains the REQUESTED state.
#
# It does NOT tell us what the inverter is currently
# doing.
#
# The inverter is always the source of truth.
#
# =====================================================
#
# requested_work_mode
# -------------------
# Raw work mode register value that should eventually
# be written to the inverter.
#
# Examples:
#     0
#     3
#
#
# requested_manual_mode
# ---------------------
# Raw manual mode register value that should eventually
# be written to the inverter.
#
# Examples:
#     1
#     2
#
#
# desired_mode_name
# -----------------
# Human-readable interpretation of the requested state.
#
# Generated using:
#
#     decode_work_mode(
#         requested_work_mode,
#         requested_manual_mode,
#     )
#
# Examples:
#     "Self Use"
#     "Force Charge"
#     "Force Discharge"
#
#
# actual_mode
# -----------
# Normalised representation of the inverter's current
# mode used for comparison logic.
#
# Derived from:
#
#     snapshot.work_mode
#
# Examples:
#     "SELF_USE"
#     "FORCE_CHARGE"
#     "FORCE_DISCHARGE"
#
#
# actions
# -------
# List of logical actions required to move the inverter
# from its current state to the requested state.
#
# Examples:
#     ["Force Discharge"]
#     ["Self Use"]
#     []
#
#
# action_required
# ---------------
# Final decision made by the poller.
#
# True
#     Desired state differs from actual state.
#
# False
#     Inverter already matches requested state.
#
#
# IMPORTANT
# ---------
# Use human-readable values for comparison and logging:
#
#     desired_mode_name
#     actual_mode
#
# Use raw register values for inverter writes:
#
#     requested_work_mode
#     requested_manual_mode
#
# Never write:
#
#     "Force Discharge"
#
# to the inverter.
#
# Always write:
#
#     work_mode = 3
#     manual_mode = 2
#
# =====================================================


def main():

    logger.info(f"Poller starting, PID = {os.getpid()}")

    last_heartbeat = 0

    last_successful_poll = time.time()

    failure_notification_sent = False

    connection = get_connection()

    create_all_tables(connection)

    service = InverterPollingService()
    logger.info("F sleep")
    time.sleep(5)

    telemetry_repository = TelemetryRepository(connection)
    scheduler_repository = ScheduleRepository(connection)
    inverter_state_repository = InverterStateRepository(connection)
    work_mode_monitor = WorkModeMonitor()

    pushover = PushoverSender(
        api_token=PUSHOVER_API_TOKEN,
        user_key=PUSHOVER_USER_KEY,
    )

    logger.info("Creating Scheduler")
    scheduler = Scheduler(
        scheduler_repository,
        inverter_state_repository,
    )
    logger.info("Created Scheduler")

    logger.info("Creating Reconciler")
    reconciler = InverterReconciler(
        inverter_state_repository,
        service,
    )
    logger.info("Created Reconciler")

    communication_lost = False

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
                logger.info("Getting Snapshot")
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
                        #
                        # send_work_mode_email(
                        #     email_sender,
                        #     change,
                        # )
                        # send_work_mode_push(
                        #     pushover,
                        #     change,
                        # )

                    except Exception as exc:
                        logger.exception(f"Email failed: {exc}")

                if communication_lost:
                    logger.info("Communication restored")
                    communication_lost = False

                last_successful_poll = time.time()

                if failure_notification_sent:
                    # pushover.send_push(
                    #     title="🟢 Energy Dashboard",
                    #     message=(
                    #         "Communication with the SolaX inverter has been restored."
                    #     ),
                    # )

                    failure_notification_sent = False


                # ============================================================
                # STAGE 3 - SAVE SNAPSHOT
                #
                # Persist the current inverter state for dashboards,
                # graphs and historical analysis.
                #
                # ============================================================
#todo guard agains db locks
                
                logger.info("Saving Snapshot")
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
                logger.info(
                    f"Before scheduler: {inverter_state_repository.get()}"
                )

                scheduler.evaluate(snapshot)

                logger.info(
                    f"After scheduler: {inverter_state_repository.get()}"
                )
                logger.info("Scheduler Complete")

                logger.info("Running Reconciler")
                reconciler.process(snapshot)
                logger.info("Reconciler Complete")

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

                # pending = reconciler.process(snapshot)

                #pending = inverter_state_repository.get()

                # ============================================================
                # RECONCILIATION RULES
                #
                # work_mode = 3 (Manual)
                #
                #     Compare both:
                #
                #         work_mode
                #         manual_mode
                #
                # work_mode != 3
                #
                #     Compare work_mode only.
                #
                #     manual_mode is ignored by the inverter when not in
                #     Manual work mode and may contain a stale value from a
                #     previous Force Charge / Force Discharge request.
                #
                # ============================================================
                # TERMINOLOGY
                #
                # requested_*  -> Desired state from inverter_state table
                #
                # snapshot_*   -> Actual state reported by inverter
                #
                # action_required
                #
                #     True  = Desired state differs from Actual state
                #
                #     False = Desired state already achieved
                # ==============================================================

                # if pending and pending["active"]:
                #     requested_work_mode = pending["requested_work_mode"]
                #     requested_manual_mode = pending["requested_manual_mode"]
                #
                #     logger.info(
                #         f"Desired inverter state: "
                #         f"work_mode={requested_work_mode}, "
                #         f"manual_mode={requested_manual_mode}"
                #     )
                #
                #     if requested_work_mode == WORK_MODE_MANUAL:
                #         logger.info("Required operation: Set Work Mode -> Manual")
                #
                #         if requested_manual_mode == MANUAL_MODE_IDLE:
                #             logger.info("Required operation: Set Manual Mode -> Idle")
                #
                #         elif requested_manual_mode == MANUAL_MODE_FORCE_CHARGE:
                #             logger.info(
                #                 "Required operation: Set Manual Mode -> Force Charge"
                #             )
                #
                #         elif requested_manual_mode == MANUAL_MODE_FORCE_DISCHARGE:
                #             logger.info(
                #                 "Required operation: Set Manual Mode -> Force Discharge"
                #             )
                #
                #     elif requested_work_mode == WORK_MODE_SELF_USE:
                #         logger.info("Required operation: Set Work Mode -> Self Use")
                #
                #     logger.info(
                #         f"Current inverter state: "
                #         f"work_mode={snapshot.work_mode}, "
                #         f"manual_mode={snapshot.manual_mode}"
                #     )
                #
                #     if requested_work_mode == WORK_MODE_MANUAL:
                #         # Manual work mode active so check for charge or discharge or neither
                #         action_required = (
                #             requested_work_mode != snapshot.work_mode
                #             or requested_manual_mode != snapshot.manual_mode
                #         )
                #     else:
                #         # Manual mode ignored by inverter
                #         action_required = requested_work_mode != snapshot.work_mode
                #     logger.info(
                #         f"Action required: {'YES' if action_required else 'NO'}"
                #     )
                #
                #     if action_required:
                #         InverterController.write_work_mode(
                #             requested_work_mode,
                #             requested_manual_mode,
                #         )
                #     else:
                #         logger.info("Requested state already achieved")

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
        service.close()
        connection.close()
        logger.info("Poller stopped")


if __name__ == "__main__":
    main()


# todo sort out enable v disabled detection in scheduler
