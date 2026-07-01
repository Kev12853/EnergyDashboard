from app.backend.common.logging_utils import setup_logger

from app.backend.inverter.inverter_controller import InverterController
from app.solax.telemetry.modbus_service import SolaxModbusService

logger = setup_logger("Inverter Service")

# ============================================================
# INVERTER POLLING SERVICE
# ============================================================
#
# Responsibility
#
#    Communicate with the inverter and produce a snapshot
#    representing the inverter's ACTUAL current state.
#
#
# Architecture
#
#    Inverter
#        ↓
#    Modbus Registers
#        ↓
#    InverterPollingService
#        ↓
#    PowerFlowSnapshot
#
#
# Important
#
#    This service does NOT:
#
#        - Evaluate schedules
#        - Compare desired vs actual state
#        - Decide whether inverter changes are required
#        - Write inverter settings
#
#    Those responsibilities belong elsewhere.
#
#
# Output
#
#    The returned snapshot is considered the source of truth
#    for the inverter's current state.
#
# ============================================================

class InverterPollingService:
    def __init__(
        self,
        host="192.168.1.67",
    ):

        self.modbus_service = SolaxModbusService(
            host=host,
        )
        self.controller = InverterController(self.modbus_service)

        """
        Poll the inverter and return a PowerFlowSnapshot.

        The snapshot contains:

            - Current telemetry values
            - Current inverter work mode
            - Current inverter manual mode

        Raw register values are preserved wherever possible to
        allow reliable comparison logic elsewhere in the system.

        Human-readable names are provided only for logging,
        display and notifications.
        """

    def poll(
        self,
    ):
        """
         Read all registers required for:
             1. Work mode information
             2. Power flow telemetry

        :return: snapshot of the current inverter registers
        """

        logger.info("Inside Get Snapshot")
        logger.info("Getting Work Mode")

        #
        # Read all registers required for:
        #
        #     1. Work mode information
        #     2. Power flow telemetry
        #
        # The work mode registers are read separately because
        # they are not part of the standard telemetry block.
        #

        (
            mode_registers,
            telemetry_registers,
        ) = self.modbus_service.read_polling_registers()

        #
        # Convert raw register values into a human-readable
        # mode name.
        #
        # Examples:
        #
        #     (0, None) -> "Self Use"
        #     (3, 1)    -> "Force Charge"
        #     (3, 2)    -> "Force Discharge"
        #
        # IMPORTANT:
        #
        # The poller uses the raw register values for
        # comparison and reconciliation.
        #
        # This decoded value exists primarily for logging,
        # notifications and UI display.
        #

        mode = self.controller.decode_work_mode(
            mode_registers[0x008B],
            mode_registers[0x008C],
        )

        logger.info("Got Work Mode")
        logger.info("Getting Poll Once")
        snapshot = self.modbus_service.build_snapshot(telemetry_registers)
        logger.info("Got Poll Once")

        #
        # Store both:
        #
        #     Raw values
        #
        #         work_mode
        #         manual_mode
        #
        #     Human-readable value
        #
        #         work_mode_name
        #
        # Raw values are used for reconciliation.
        # Human-readable values are used for display.
        #

        snapshot.work_mode = mode_registers[0x008B]
        snapshot.manual_mode = mode_registers[0x008C]
        snapshot.work_mode_name = mode

        logger.info("Leaving Get Snapshot")

        return snapshot

    def write_work_mode(
        self,
        work_mode,
        manual_mode,
    ):
        """
        Write a new operating mode to the inverter.

        The reconciler requests operating mode changes via the
        polling service. The actual Modbus write is delegated
        to the underlying Modbus service.
        """

        logger.info(
            f"Writing inverter mode: "
            f"work_mode={work_mode}, "
            f"manual_mode={manual_mode}"
        )

        self.modbus_service.write_work_mode(
            work_mode,
            manual_mode,
        )

    def close(
        self,
    ):

        self.modbus_service.close()
