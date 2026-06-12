class InverterController:
    def __init__(
        self,
        client,
    ):

        self.client = client

    def get_work_mode(self):

        mode_registers = self.client.read_work_mode_registers()

        work_mode = mode_registers[0x008B]
        manual_mode = mode_registers[0x008C]

        return self.decode_work_mode(
            work_mode,
            manual_mode,
        )

    @staticmethod
    def decode_work_mode(
        work_mode,
        manual_mode,
    ):

        if work_mode == 0:
            return "Self Use"

        if work_mode == 1:
            return "Feed In Priority"

        if work_mode == 2:
            return "Backup"

        if work_mode == 3:
            if manual_mode == 0:
                return "Manual"

            if manual_mode == 1:
                return "Force Charge"

            if manual_mode == 2:
                return "Force Discharge"

            return f"Manual ({manual_mode})"

        if work_mode == 4:
            return "Peak Shaving"

        if work_mode == 5:
            return "TOU"

        return f"Unknown ({work_mode})"

    def force_charge(
        self,
    ):
        pass
        #set workmode to manual
        self.client.client.write_register(
            address=31,
            value=3,
            device_id=self.client.slave_id,
        )

        #set manual mode to Force Charge
        self.client.client.write_register(
            address=32,
            value=1,
            device_id=self.client.slave_id,
        )
        #


    def force_discharge(
        self,
    ):
        pass
        #set workmode to manual
        self.client.client.write_register(
            address=31,
            value=3,
            device_id=self.client.slave_id,
        )

        #set manual mode to Force Discharge
        self.client.client.write_register(
            address=32,
            value=2,
            device_id=self.client.slave_id,
        )




    def self_use(
        self,
    ):
        pass
        # set work mode to Self Use
        # self.client.client.write_register(
        #     address=31,
        #     value=0,
        #     device_id=self.client.slave_id,
        # )
