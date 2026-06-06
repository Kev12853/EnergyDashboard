from pymodbus.client import ModbusTcpClient


INVERTER_IP = "192.168.1.66"


client = ModbusTcpClient(host=INVERTER_IP, port=502, timeout=5)

print("Connecting...")

if client.connect():
    print("Connected OK")

    result = client.read_holding_registers(0, count=10, device_id=1)

    print(result)

    if not result.isError():
        print("\nRegisters:\n")

        for i, value in enumerate(result.registers):
            print(f"Register {i}: {value}")

    client.close()

    print("\nConnection closed")

else:
    print("Connection failed")
