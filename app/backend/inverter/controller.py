class InverterController:

    def __init__(
        self,
        client,
    ):

        self.client = client

    def force_charge(
            self,
    ):
        self.client.client.write_register(
            address=32,
            value=1,
            device_id=self.client.slave_id,
        )

        self.client.client.write_register(
            address=31,
            value=3,
            device_id=self.client.slave_id,
        )

    def force_discharge(
            self,
    ):
        self.client.client.write_register(
            address=32,
            value=2,
            device_id=self.client.slave_id,
        )

        self.client.client.write_register(
            address=31,
            value=3,
            device_id=self.client.slave_id,
        )

    def self_use(
            self,
    ):
        self.client.client.write_register(
            address=31,
            value=0,
            device_id=self.client.slave_id,
        )