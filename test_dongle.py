from time import sleep
from datetime import datetime

from pymodbus.client import ModbusTcpClient
import os

from app.backend.poller.poller import close

HOST = "192.168.1.67"
PORT = 502
SLAVE_ID = 1
REGISTER_BLOCK_START = 0
REGISTER_BLOCK_SIZE = 10
successes = 0
failures = 0
cycle = 0

while True:
    print()
    print("=" * 50)
    print(f"PID = {os.getpid()}")
    print("=" * 50)
    print()
    cycle += 1

    print()
    print("=" * 60)
    print(f"Cycle {cycle} : {datetime.now():%H:%M:%S}")

    client = ModbusTcpClient(
        host=HOST,
        port=PORT,
    )

    try:
        connected = client.connect()

        result1 = client.read_holding_registers(
            address=0x008B,
            count=2,
            device_id=1,
        )

        print(result1)

        result2 = client.read_input_registers(
            address=0,
            count=10,
            device_id=1,
        )

        print(result2)
        client.close()
        #
        # if not connected:
        #     raise RuntimeError("Connect failed")
        #
        # result = client.read_input_registers(
        #     address=REGISTER_BLOCK_START,
        #     count=REGISTER_BLOCK_SIZE,
        #     device_id=SLAVE_ID,
        # )
        #
        # if result.isError():
        #     raise RuntimeError(result)
        #
        print(f"Successfully read registers")
        #print(f"Successfully read {len(result.registers)} registers")
        # successes += 1

    except Exception as exc:

        failures += 1

        print(f"FAILED  : {type(exc).__name__}")
        print(exc)

    finally:

        try:
            client.close()
        except Exception:
            pass

    print()
    print(
        f"Success={successes}  "
        f"Failures={failures}  "
        #f"Success Rate={100 * successes / (successes + failures):.1f}%"
    )

    sleep(10)