# services/solax/local_probe/scanner.py

from pymodbus.client import ModbusTcpClient
import csv
from datetime import datetime


HOST = "192.168.1.66"
PORT = 502
SLAVE = 1


def read_register(
    client,
    reg,
    register_type="holding",
):

    try:

        if register_type == "holding":

            result = client.read_holding_registers(
                address=reg,
                count=2,
                device_id=SLAVE,
            )

        else:

            result = client.read_input_registers(
                address=reg,
                count=2,
                device_id=SLAVE,
            )

        if result.isError():

            return None

        return result.registers

    except:

        return None


client = ModbusTcpClient(
    HOST,
    port=PORT,
)

client.connect()

timestamp = datetime.utcnow().isoformat()

rows = []

for reg in range(0, 500):

    for reg_type in (
        "holding",
        "input",
    ):

        value = read_register(
            client,
            reg,
            reg_type,
        )

        if value:

            rows.append(
                [
                    timestamp,
                    reg_type,
                    reg,
                    value,
                ]
            )

client.close()

with open(
    "scan.csv",
    "w",
    newline="",
) as f:

    writer = csv.writer(f)

    writer.writerow(
        [
            "timestamp",
            "type",
            "register",
            "raw",
        ]
    )

    writer.writerows(rows)

print(
    f"Captured {len(rows)} registers"
)