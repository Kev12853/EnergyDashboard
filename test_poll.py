from pprint import pprint

from services.solax.local_probe.client import (
    SolaxModbusClient,
)

from services.solax.local_probe.mapper import (
    map_registers_to_snapshot,
)


client = SolaxModbusClient(
    host="192.168.1.66",
)

registers = client.read_register_block()

snapshot = map_registers_to_snapshot(
    registers
)

pprint(snapshot)