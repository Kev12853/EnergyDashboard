"""Read local Modbus work-mode and telemetry registers and assemble a PowerFlowSnapshot. This read-only poller interface feeds storage and control decisions but exposes no inverter write method."""


from app.solax.backend.inverter.inverter_controller import InverterController
from app.logging.logger import setup_logger
from app.solax.telemetry.modbus_service import SolaxModbusService
from app.config.solax_config import SOLAX_HOST, SOLAX_PORT

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
    """Read local Modbus registers and build snapshots for storage/control; it exposes no write method."""
    def __init__(
        self,
        host=SOLAX_HOST,
        port=SOLAX_PORT,
    ):

        self._modbus_service = SolaxModbusService(
            host=host,
            port=port,
        )
        # Decoding is pure; this service deliberately exposes no write method.

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
             1. Work decoded_work_mode information
             2. Power flow telemetry

        :return: snapshot of the current inverter registers
        """

        logger.info("Inside Get Snapshot")
        logger.info("Getting Work Mode")

        #
        # Read all registers required for:
        #
        #     1. Work decoded_work_mode information
        #     2. Power flow telemetry
        #
        # The work decoded_work_mode registers are read separately because
        # they are not part of the standard telemetry block.
        #

        (
            mode_registers,
            telemetry_registers,
        ) = self._modbus_service.read_polling_registers()

        #
        # Convert raw register values into a human-readable
        # decoded_work_mode name.
        #
        # Examples:
        #
        #     (0, None) -> "Self Use"
        #     (3, 1)    -> "Force Charge"
        #     (3, 2)    -> "Force Discharge"
        #
        # IMPORTANT:
        #
        # The poller_status_card uses the raw register values for
        # comparison and reconciliation.
        #
        # This decoded value exists primarily for logging,
        # notifications and UI display.
        #

        decoded_work_mode = InverterController.decode_work_mode(
            mode_registers[0x008B],
            mode_registers[0x008C],
        )

        logger.info("Got Work Mode")
        logger.info("Getting Poll Once")
        snapshot = self._modbus_service.build_snapshot(telemetry_registers)
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
        snapshot.work_mode_name = decoded_work_mode

        logger.info("Leaving Get Snapshot")

        return snapshot

    def close(
        self,
    ):

        """Close the polling Modbus client and release its connection resources."""
        self._modbus_service.close()
