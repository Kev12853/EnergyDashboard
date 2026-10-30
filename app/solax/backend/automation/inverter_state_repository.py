"""Persist the durable desired inverter state and its ownership/restoration lifecycle in SQLite. Scheduler, Smart Flex and InverterReconciler share this request record; this repository does not communicate over Modbus."""

from app.enums.inverter_state_enums import InverterRequestPhase
from app.logging.logger import setup_logger
from app.solax.storage.inverter_state import (
    get_inverter_state,
    set_inverter_state,
    clear_inverter_state,
    has_pending_inverter_state,
    request_restore,
)

logger = setup_logger(__name__)

class InverterStateRepository:
    """
    Repository for the inverter_state table.

    Purpose
    -------
    The inverter_state table represents the CURRENT OVERRIDE REQUEST.

    It is the hand-off point between the Scheduler and the Poller.

        Scheduler
            ↓
        inverter_state
            ↓
        Poller
            ↓
        Inverter

    The scheduler never communicates directly with the inverter.
    It simply records the state the inverter should temporarily
    be changed to.

    The poller_status_card compares the requested state with the actual
    inverter state (from the latest snapshot) and performs any
    required inverter updates.

    The table also stores the operating mode that should be
    restored once the override has completed.
    """

    def __init__(self, connection):
        self.connection = connection

    #
    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    #

    def get(self):
        """
        Return the current override request.

        Returns:
            A dictionary describing the outstanding override request,
            or None if there is no outstanding request.
        requested_*   = current highest-priority request
        underlying_*  = request to resume when the current override ends
        restore_*     = state to restore when the underlying override finishes
        The repository hides the database representation from callers.
        Although the inverter_state table always contains a row, a row
        with a NULL requested_work_mode represents "no request" and is
        therefore returned as None.
        """

        inverter_state = get_inverter_state(
            self.connection,
        )

        if inverter_state is None:
            return None

        if (
            inverter_state["phase"] == InverterRequestPhase.IDLE
            and inverter_state["requested_work_mode"] is not None
        ):
            logger.warning(
                "Inverter state is inconsistent: "
                "phase is IDLE but a requested work mode exists."
            )
        #
        # No inverter_state row.
        #
        # phase is the authoritative request lifecycle.
        #
        # IDLE      -> no outstanding request
        # OVERRIDE  -> override requested/active
        # RESTORE   -> restoration requested/in progress
        #
        # Other columns contain payload associated with the current phase.
        #
        if inverter_state["phase"] == InverterRequestPhase.IDLE:
            return None

        return inverter_state
    #
    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------
    #

    def set(
        self,
        requested_work_mode,
        requested_manual_mode,
        restore_work_mode_to,
        restore_manual_mode_to,
        underlying_work_mode=None,
        underlying_manual_mode=None,
        phase=InverterRequestPhase.OVERRIDE,
        active=True,
        source="scheduler",
    ):
        """
        Create or update an override request.

        requested_* values describe the temporary inverter state
        that the scheduler wishes to apply.

        restore_* values describe the operating mode that should
        be restored when the override ends.

        This method records the request only.

        The poller_status_card is responsible for:
            - detecting the request
            - updating the inverter
            - verifying the change
            - completing the request
        """

        return set_inverter_state(
            self.connection,
            requested_work_mode,
            requested_manual_mode,
            restore_work_mode_to,
            restore_manual_mode_to,
            underlying_work_mode,
            underlying_manual_mode,
            phase,
            active,
            source,
        )

    def request_restore(self):
        """
        Request restoration of the inverter operating mode that
        was active before the temporary override began.

        The scheduler calls this when leaving a schedule window.
        The poller_status_card will detect the new requested state and restore
        the inverter.
        """
        # Move the saved state into the active request.
        # The restore_* fields are deliberately cleared here to indicate that
        # the restore has been requested and to prevent repeated requests.

        state = self.get()

        if state["restore_work_mode_to"] is None:
            raise RuntimeError("No stored operating mode to restore.")

        return request_restore(
            self.connection,
        )


    #
    # ------------------------------------------------------------------
    # Clear
    # ------------------------------------------------------------------
    #

    def clear(self):
        """
        Clear the current override request.

        Called once the poller_status_card has successfully restored the
        inverter to its normal operating mode.
        """

        return clear_inverter_state(
            self.connection,
        )

    def clear_if_current(self, state):
        """Clear only the request that was actually verified by telemetry."""
        cursor = self.connection.execute(
            """UPDATE inverter_state SET requested_work_mode=NULL,
                   requested_manual_mode=NULL, restore_work_mode_to=NULL,
                   restore_manual_mode_to=NULL, underlying_work_mode=NULL,
                   underlying_manual_mode=NULL, active=0, source=NULL,
                   phase=?, updated_at=CURRENT_TIMESTAMP
               WHERE id=1 AND phase=? AND source IS ? AND active IS ?
                 AND requested_work_mode IS ? AND requested_manual_mode IS ?
                 AND restore_work_mode_to IS ? AND restore_manual_mode_to IS ?
                 AND underlying_work_mode IS ? AND underlying_manual_mode IS ?
                 AND updated_at IS ?""",
            (InverterRequestPhase.IDLE, state["phase"], state["source"],
             state["active"], state["requested_work_mode"], state["requested_manual_mode"],
             state["restore_work_mode_to"], state["restore_manual_mode_to"],
             state["underlying_work_mode"], state["underlying_manual_mode"],
             state["updated_at"]),
        )
        self.connection.commit()
        return cursor.rowcount == 1

    #
    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------
    #

    def has_pending(self):
        """
        Return True if an override request is active.
        """

        return has_pending_inverter_state(
            self.connection,
        )

    def set_underlying(self, work_mode, manual_mode):
        """Replace the saved underlying request while preserving the current owner, active request, phase and restoration target; commits through set()."""
        state = self.get()

        self.set(
            requested_work_mode=state["requested_work_mode"],
            requested_manual_mode=state["requested_manual_mode"],
            restore_work_mode_to=state["restore_work_mode_to"],
            restore_manual_mode_to=state["restore_manual_mode_to"],
            underlying_work_mode=work_mode,
            underlying_manual_mode=manual_mode,
            phase=state["phase"],
            active=state["active"],
            source=state["source"],
        )

    def clear_underlying(self):
        """Clear the saved underlying request while leaving the current active request and ownership intact; commits through set()."""
        state = self.get()

        self.set(
            requested_work_mode=state["requested_work_mode"],
            requested_manual_mode=state["requested_manual_mode"],
            restore_work_mode_to=state["restore_work_mode_to"],
            restore_manual_mode_to=state["restore_manual_mode_to"],
            underlying_work_mode=None,
            underlying_manual_mode=None,
            phase=state["phase"],
            active=state["active"],
            source=state["source"],
        )

    def activate_underlying(self):
        """Promote the saved underlying request to the active scheduler request; raises RuntimeError when no request is available."""
        state = self.get()

        if state is None:
            raise RuntimeError("No inverter state to activate underlying request.")

        if state["underlying_work_mode"] is None:
            raise RuntimeError("No underlying inverter state to activate.")

        self.set(
            requested_work_mode=state["underlying_work_mode"],
            requested_manual_mode=state["underlying_manual_mode"],
            restore_work_mode_to=state["restore_work_mode_to"],
            restore_manual_mode_to=state["restore_manual_mode_to"],
            underlying_work_mode=None,
            underlying_manual_mode=None,
            phase=InverterRequestPhase.OVERRIDE,
            active=state["active"],
            source="scheduler",
        )
