# services/solax/local_probe/scanner_input.py

from datetime import datetime

from pymodbus.client import ModbusTcpClient

import csv
import time


# =====================================================
# CONFIG
# =====================================================

HOST = "192.168.1.66"

PORT = 502

DEVICE_ID = 1

OUTPUT = "scan_input.csv"

REGISTERS = [

    0,
    2,
    7,
    10,11,
    22,
    25,
    28,
    70,71,
    72,73
]

# REGISTERS = list(
#     range(
#         0,
#         99,
#     )
# )

REGISTER_DELAY = 2

SWEEP_DELAY = 3


# =====================================================
# READ REGISTER
# =====================================================

def read_register(
    register,
):

    client = ModbusTcpClient(

        HOST,

        port=PORT,

        timeout=5,

    )

    try:

        connected = client.connect()

        if not connected:

            print(

                register,

                "connect failed",

            )

            return None

        result = client.read_input_registers(

            address=register,

            count=1,

            device_id=DEVICE_ID,

        )

        if result.isError():

            print(

                register,

                "error response",

            )

            return None

        value = result.registers[0]

        print(

            register,

            value,

        )

        return value

    except Exception as e:

        print(

            register,

            e,

        )

        return None

    finally:

        client.close()


# =====================================================
# CSV WRITE
# =====================================================

def write_row(

    register,

    value,

):

    timestamp = (

        datetime.now()

        .astimezone()

        .strftime(

            "%Y-%m-%d %H:%M:%S"

        )

    )

    file_exists = False

    try:

        with open(

            OUTPUT,

            "r",

        ):

            file_exists = True

    except FileNotFoundError:

        pass

    with open(

        OUTPUT,

        "a",

        newline="",

    ) as f:

        writer = csv.writer(

            f

        )

        if not file_exists:

            writer.writerow(

                [

                    "timestamp",

                    "type",

                    "register",

                    "raw",

                ]

            )

        writer.writerow(

            [

                timestamp,

                "input",

                register,

                value,

            ]

        )


# =====================================================
# MAIN
# =====================================================

def main():

    while True:

        sweep_start = (

            datetime.now()

            .astimezone()

            .strftime(

                "%Y-%m-%d %H:%M:%S"

            )

        )

        print()

        print(

            "Sweep started:",

            sweep_start,

        )

        for register in REGISTERS:

            value = read_register(

                register

            )

            if value is not None:

                write_row(

                    register,

                    value,

                )

            time.sleep(

                REGISTER_DELAY

            )

        print()

        print(

            "Sweep complete",

            "- sleeping",

            SWEEP_DELAY,

            "seconds",

        )

        time.sleep(

            SWEEP_DELAY

        )


if __name__ == "__main__":

    main()

