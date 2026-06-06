from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient(host="192.168.1.66")

print(client.connect())

result = client.read_input_registers(
    address=0,
    count=1,
    device_id=1,
)

print(result)
