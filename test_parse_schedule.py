from app.solax.analytics.decoders import parse_schedule


def test_parse_schedule():

    registers = {
        0x0097: 0x1E17,  # 23:30
        0x0098: 0x1E05,  # 05:30

        0x0099: 0x0000,  # 00:00
        0x009A: 0x3B17,  # 23:59

        0x009B: 0,

        0x009C: 0,
        0x009D: 0,
        0x009E: 0,
        0x009F: 0,
    }

    schedule = parse_schedule(registers)

    print(schedule)

    assert schedule.charge1_start == "23:30"
    assert schedule.charge1_end == "05:30"

    assert schedule.discharge1_start == "00:00"
    assert schedule.discharge1_end == "23:59"

    assert schedule.period2_enabled is False

    assert schedule.charge2_start is None
    assert schedule.charge2_end is None

if __name__ == "__main__":
    test_parse_schedule()
    print("Test passed")

    from app.solax.telemetry import (
        SolaxModbusClient,
    )

    client = SolaxModbusClient(
        host="192.168.1.66",
    )

    schedule = client.read_charge_schedule()

    print(schedule)