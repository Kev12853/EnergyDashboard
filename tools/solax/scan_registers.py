from pymodbus.client import ModbusTcpClient


INVERTER_IP = "192.168.1.67"


client = ModbusTcpClient(host=INVERTER_IP, port=502, timeout=5)

print("Connecting...")

if not client.connect():
    print("Connection failed")
    raise SystemExit

print("Connected\n")


START = 0
END = 200

BLOCK_SIZE = 10


for address in range(START, END, BLOCK_SIZE):
    try:
        result = client.read_holding_registers(address, count=BLOCK_SIZE, device_id=1)

        if result.isError():
            print(f"{address:04d}: ERROR")

        else:
            values = result.registers

            print(f"{address:04d}: {values}")

    except Exception as e:
        print(f"{address:04d}: EXCEPTION -> {e}")


client.close()

print("\nDone")
