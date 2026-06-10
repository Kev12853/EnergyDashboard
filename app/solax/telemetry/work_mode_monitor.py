from datetime import datetime


class WorkModeMonitor:

    def __init__(self):

        self.current_mode = None
        self.last_changed = None

    @property
    def mode(self):
        return self.current_mode

    def update(
        self,
        mode: str,
    ):

        #
        # First observation.
        #

        if self.current_mode is None:

            self.current_mode = mode

            return None

        #
        # No change.
        #

        if mode == self.current_mode:

            return None

        #
        # Mode changed.
        #

        previous = self.current_mode

        self.current_mode = mode

        self.last_changed = datetime.now()

        return {
            "previous": previous,
            "current": mode,
            "timestamp": self.last_changed,
        }