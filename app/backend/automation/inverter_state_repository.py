from app.solax.storage.inverter_state import (
    get_inverter_state,
    set_inverter_state,
    clear_inverter_state,
    has_pending_inverter_state,
    request_restore,
)


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

    The poller compares the requested state with the actual
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

        The repository hides the database representation from callers.
        Although the inverter_state table always contains a row, a row
        with a NULL requested_work_mode represents "no request" and is
        therefore returned as None.
        """

        state = get_inverter_state(
            self.connection,
        )

        #
        # No inverter_state row.
        #

        if state is None:
            return None

        #
        # The table always contains one row.
        #
        # A NULL requested_work_mode means there is currently no
        # outstanding request.
        #

        if state["requested_work_mode"] is None:
            return None

        return state
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
        active,
        source,
    ):
        """
        Create or update an override request.

        requested_* values describe the temporary inverter state
        that the scheduler wishes to apply.

        restore_* values describe the operating mode that should
        be restored when the override ends.

        This method records the request only.

        The poller is responsible for:
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
            active,
            source,
        )

    def request_restore(self):
        """
        Request restoration of the inverter operating mode that
        was active before the temporary override began.

        The scheduler calls this when leaving a schedule window.
        The poller will detect the new requested state and restore
        the inverter.
        """

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

        Called once the poller has successfully restored the
        inverter to its normal operating mode.
        """

        return clear_inverter_state(
            self.connection,
        )

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