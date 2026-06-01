# test_schedule.py

from pymodbus.client import ModbusTcpClient


HOST = "192.168.1.66"
SLAVE_ID = 1

def decode_time(register_value):

    minute = (
        register_value >> 8
    ) & 0xFF

    hour = (
        register_value
    ) & 0xFF

    return (
        f"{hour:02d}:"
        f"{minute:02d}"
    )


client = ModbusTcpClient(HOST)

client.connect()

result = client.read_holding_registers(
    address=0x0097,
    count=9,
    device_id=SLAVE_ID,
)

for offset, value in enumerate(result.registers):

    reg = 0x0097 + offset

    print(
        f"0x{reg:04X} = "
        f"{value} "
        f"(0x{value:04X})"
    )

print(
    "Charge 1 Start:",
    decode_time(result.registers[0])
)

print(
    "Charge 1 End:",
    decode_time(result.registers[1])
)

print(
    "Discharge 1 Start:",
    decode_time(result.registers[2])
)

print(
    "Discharge 1 End:",
    decode_time(result.registers[3])
)

print(
    "Period 2 Enabled:",
    result.registers[4]
)

print(
    "Charge 2 Start:",
    decode_time(result.registers[5])
)

print(
    "Charge 2 End:",
    decode_time(result.registers[6])
)

print(
    "Discharge 2 Start:",
    decode_time(registers[7])
)

print(
    "Discharge 2 End:",
    decode_time(registers[8])
)
client.close()