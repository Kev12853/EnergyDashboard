import time
from datetime import datetime

from pymodbus.client import ModbusTcpClient

INVERTER_IP = "192.168.1.67"

START_REGISTER = 20
REGISTER_COUNT = 20

POLL_INTERVAL = 5


client = ModbusTcpClient(host=INVERTER_IP, port=502, timeout=5)


print("Connecting...")

if not client.connect():
    print("Connection failed")
    raise SystemExit

print("Connected")


try:
    while True:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print("\n" + "=" * 80)
        print(timestamp)
        print("=" * 80)

        try:
            result = client.read_holding_registers(
                START_REGISTER, count=REGISTER_COUNT, device_id=1
            )

            if result.isError():
                print("Read error")
                print(result)

            else:
                for i, value in enumerate(result.registers):
                    register = START_REGISTER + i

                    print(f"Register {register:03d}: {value}")

        except Exception as e:
            print(f"ERROR: {e}")

        time.sleep(POLL_INTERVAL)

finally:
    client.close()

    print("Connection closed")
