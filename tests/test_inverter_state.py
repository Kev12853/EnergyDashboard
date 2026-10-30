"""Exercise compatibility helpers for reading, setting and clearing the durable inverter request in SQLite."""

from app.solax.backend.storage.db import (
    get_connection,
)
from app.enums.inverter_state_enums import InverterRequestPhase

from app.solax.storage.inverter_state import (
    get_inverter_state,
    set_inverter_state,
    clear_inverter_state,
    request_restore,
)

from app.solax.backend.automation.inverter_state_repository import InverterStateRepository
from app.solax.backend.storage.schema import create_solax_tables



connection = get_connection()
create_solax_tables(connection)

clear_inverter_state(connection)

print("INITIAL")
print(
    get_inverter_state(
        connection,
    )
)

print()
print("SETTING")
set_inverter_state(
    connection,
    requested_work_mode=3,
    requested_manual_mode=1,
    restore_work_mode_to=0,
    restore_manual_mode_to=0,
    underlying_work_mode=0,
    underlying_manual_mode=0,
    active= True,
    source="Test",
    phase= InverterRequestPhase.OVERRIDE,
)

print(
    get_inverter_state(
        connection,
    )
)

repository = InverterStateRepository(connection)

print()
print("SETTING UNDERLYING")
repository.set_underlying(1, 0)
print(repository.get())

print()
print("ACTIVATE UNDERLYING")
repository.activate_underlying()
print(repository.get())

print()
print("CLEAR UNDERLYING")
repository.clear_underlying()
print(repository.get())


print()
print("REQUEST RESTORE")

request_restore(connection)

print(get_inverter_state(connection))

print()
print("CLEARING")
clear_inverter_state(
    connection,
)

print(
    get_inverter_state(
        connection,
    )
)