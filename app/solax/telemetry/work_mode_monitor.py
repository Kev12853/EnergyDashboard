from datetime import datetime

class WorkModeMonitor:
    '''
     ============================================================
     WORK MODE MONITOR
     ============================================================

     Tracks inverter work mode changes between poll cycles.

     Purpose:

         Detect changes in inverter operating mode and
         generate change notifications.

     Examples:

         Self Use
             ↓
         Force Charge

         Force Charge
             ↓
         Force Discharge

     The monitor maintains the last observed mode and
     compares it with the latest snapshot.

     This class is completely independent of:

         - Scheduler
         - inverter_state table
         - Reconciliation logic

     It only answers one question:

         "Has the inverter work mode changed?"

     ============================================================
    '''

    def __init__(self):

        self.current_mode = None
        self.last_changed = None


    @property
    def mode(self):
        return self.current_mode

    def update(
        self,
        mode: int,
    ):
        """
        Determines whether there is a change in the inverters work mode since the last poll loop.
        :param mode:
        :return: None or previous and current mode and timestamp
        """



        # Poller startup.
        #
        # Record the initial mode but do not
        # generate a change notification.

        if self.current_mode is None:

            self.current_mode = mode

            return None

        # Subsequent loops of the poller may or may not record a change

        # No change.
        if mode == self.current_mode:
            return None

        # Mode changed.
        previous = self.current_mode
        self.current_mode = mode
        self.last_changed = datetime.now()

        return {
            "previous": previous,
            "current": mode,
            "timestamp": self.last_changed,
        }