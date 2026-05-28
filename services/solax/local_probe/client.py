from pymodbus.client import ModbusTcpClient

from .registers import (
    REGISTER_BLOCK_START,
    REGISTER_BLOCK_SIZE,
)


class SolaxModbusClient:

    def __init__(

        self,
        host: str,
        port: int = 502,
        slave_id: int = 1,

    ):

        self.host = host
        self.port = port
        self.slave_id = slave_id

        self.client = ModbusTcpClient(
            host=self.host,
            port=self.port,
        )

    def read_register_block(self) -> dict[int, int]:

        result = self.client.read_input_registers(

            address=REGISTER_BLOCK_START,
            count=REGISTER_BLOCK_SIZE,
            device_id=self.slave_id,

        )

        if result.isError():

            raise RuntimeError(
                f"Modbus read failed: {result}"
            )

        return {

            REGISTER_BLOCK_START + index: value

            for index, value
            in enumerate(result.registers)

        }