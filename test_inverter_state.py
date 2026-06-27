from pprint import pprint

from app.backend.storage.db import (
    get_connection,
)

from app.solax.storage.inverter_state import (
    get_inverter_state,
    set_inverter_state,
    clear_inverter_state,
    request_restore,
)

connection = get_connection()

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
    active= True,
    source="Test",
)

print(
    get_inverter_state(
        connection,
    )
)

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