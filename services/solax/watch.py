import time

from pymodbus.client import ModbusTcpClient

from services.solax.registers import (
    REGISTERS,
    decode_register,
)

INVERTER_IP = "192.168.1.66"


client = ModbusTcpClient(
    host=INVERTER_IP,
    port=502,
    timeout=5
)


def read_register(address: int):

    result = client.read_holding_registers(
        address,
        count=1,
        device_id=1
    )

    if result.isError():
        return None

    return result.registers[0]


print("Connecting...")

if not client.connect():
    print("Connection failed")
    raise SystemExit

print("Connected\n")


try:

    while True:

        print("=" * 50)

        for name, definition in REGISTERS.items():

            raw = read_register(definition.address)

            if raw is None:
                print(f"{name:<25} ERROR")
                continue

            decoded = decode_register(definition, raw)

            print(
                f"{name:<25} "
                f"raw={raw:<8} "
                f"value={decoded} {definition.unit or ''}"
            )

        print()

        time.sleep(2)

finally:

    client.close()

    print("Connection closed")