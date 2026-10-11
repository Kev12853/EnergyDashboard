from app.octopus.api.octopus_api import get_smartflex_vehicle_status

CAR_CONNECTED_STATES = {
    "SMART_CONTROL_CAPABLE",
    "SMART_CONTROL_IN_PROGRESS",
}

if __name__ == "__main__":

    status = get_smartflex_vehicle_status()

    print()
    print("BMW Smart Flex status")
    print("---------------------")

    if status is None:
        print("No Smart Flex vehicle found")
    else:
        print(f"Vehicle:       {status['vehicle']}")
        print(f"State:         {status['state']}")
        print(f"Lifecycle:     {status['lifecycle']}")
        print(f"Suspended:     {status['suspended']}")
        print(f"BMW connected: {status['connected']}")
        print(f"BMW SOC:       {status['soc']:.1f} %")
        print(f"BMW charging:  {status['charging']}")
        print(f"Active power:  {status['active_power_kw']:.1f} kW")