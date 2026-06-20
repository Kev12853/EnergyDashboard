from app.solax.storage.inverter_state import (
    get_inverter_state,
    set_inverter_state,
    clear_inverter_state,
    has_pending_inverter_state,
)


class InverterStateRepository:

    def __init__(self, connection):
        self.connection = connection

    def get(self):
        return get_inverter_state(
            self.connection
        )

    def set(
        self,
        work_mode,
        manual_mode=None,
        source="scheduler",
    ):
        return set_inverter_state(
            self.connection,
            work_mode,
            manual_mode,
            source,
        )

    def clear(self):
        return clear_inverter_state(
            self.connection
        )

    def has_pending(self):
        return has_pending_inverter_state(
            self.connection
        )