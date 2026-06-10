from pprint import pprint

from app.solax.telemetry.modbus_client import SolaxModbusClient

client = SolaxModbusClient(
    host="192.168.1.66",
)

try:

    snapshot = client.poll_once()

    print()
    print("SUCCESS")
    print()

    pprint(snapshot)

except Exception as exc:

    print()
    print("FAILED")
    print()
    print(exc)

finally:

    try:
        client.client.close()
    except Exception:
        pass