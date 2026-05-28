from pymodbus.client import ModbusTcpClient


HOST = "192.168.1.66"
PORT = 502

client = ModbusTcpClient(
    HOST,
    port=PORT,
)

print("Connecting...")

connected = client.connect()

print(
    "Connected:",
    connected,
)

if connected:

    try:

        result = client.read_holding_registers(
            address=0,
            count=1,
            device_id=1,
        )

        print(
            "Holding result:",
            result,
        )

    except Exception as e:

        print(
            "Holding failed:",
            e,
        )

    try:

        result = client.read_input_registers(
            address=0,
            count=1,
            device_id=1,
        )

        print(
            "Input result:",
            result,
        )

    except Exception as e:

        print(
            "Input failed:",
            e,
        )

client.close()