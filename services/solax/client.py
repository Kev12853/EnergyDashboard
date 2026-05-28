import time

from pymodbus.client import ModbusTcpClient


class SolaxModbusClient:

    def __init__(
        self,
        host: str,
        port: int = 502,
        device_id: int = 1,
        timeout: int = 5,
    ):

        self.host = host
        self.port = port
        self.device_id = device_id
        self.timeout = timeout

        self.client = ModbusTcpClient(
            host=self.host,
            port=self.port,
            timeout=self.timeout,
        )

        self.connected = False

    # =====================================================
    # CONNECTION
    # =====================================================

    def connect(self) -> bool:

        if self.connected:
            return True

        try:

            self.connected = self.client.connect()

            return self.connected

        except Exception as e:

            print(f"CONNECT ERROR: {e}")

            self.connected = False

            return False

    def close(self):

        try:

            self.client.close()

        finally:

            self.connected = False

    # =====================================================
    # SAFE BLOCK READ
    # =====================================================

    def read_block(
        self,
        start: int,
        count: int,
    ):

        if not self.connected:

            if not self.connect():
                return None

        try:

            result = self.client.read_holding_registers(
                start,
                count=count,
                device_id=self.device_id,
            )

            # Gentle throttling for fragile dongles
            time.sleep(0.2)

            if result.isError():

                print(f"MODBUS ERROR: {result}")

                return None

            return result.registers

        except Exception as e:

            print(f"READ ERROR: {e}")

            self.connected = False

            return None


