from app.solax.telemetry import (
    SolaxModbusClient,
)

client = SolaxModbusClient(
    host="192.168.1.66",
)

#
# Read current values
#

mode_result = client.client.read_holding_registers(
    address=139,
    count=2,
    device_id=client.slave_id,
)

if mode_result.isError():
    raise RuntimeError(mode_result)

current_work_mode = mode_result.registers[0]
current_manual_mode = mode_result.registers[1]

print(
    f"Work Mode   : {current_work_mode}"
)

print(
    f"Manual Mode : {current_manual_mode}"
)

#
# Write same values back
#
#
# result = client.client.write_register(
#     address=31,
#     value=3,
#     device_id=client.slave_id,
# )
#
# print(
#     f"Write 31 result: {result}"
# )
#
#
# print(
#     f"Write 32 result: {result}"
# )
#
# #
# # Read back to verify
# #

verify = client.client.read_holding_registers(
    address=139,
    count=2,
    device_id=client.slave_id,
)

print(
    f"Readback Work Mode   : {verify.registers[0]}"
)

print(
    f"Readback Manual Mode : {verify.registers[1]}"
)