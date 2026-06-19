from app.backend.storage.db import (
    get_connection,
)

from app.solax.storage.inverter_state import (
    get_inverter_state,
    set_inverter_state,
    clear_inverter_state,
)

connection = get_connection()

print()
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
    work_mode=3,
    manual_mode=1,
    source="test",
)

print(
    get_inverter_state(
        connection,
    )
)

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