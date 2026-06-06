from app.solax.telemetry.models import ChargeSchedule


def decode_time(register_value: int) -> str:
    minute = (register_value >> 8) & 0xFF
    hour = register_value & 0xFF

    return f"{hour:02d}:{minute:02d}"


def parse_schedule(registers: dict[int, int]) -> ChargeSchedule:
    """
    Convert raw Solax schedule registers into a ChargeSchedule.

    Expected registers:

    0x0097 Charge Period 1 Start
    0x0098 Charge Period 1 End
    0x0099 Discharge Period 1 Start
    0x009A Discharge Period 1 End

    0x009B Period 2 Enabled

    0x009C Charge Period 2 Start
    0x009D Charge Period 2 End
    0x009E Discharge Period 2 Start
    0x009F Discharge Period 2 End
    """

    period2_enabled = registers[0x009B] != 0

    return ChargeSchedule(
        charge1_start=decode_time(registers[0x0097]),
        charge1_end=decode_time(registers[0x0098]),
        discharge1_start=decode_time(registers[0x0099]),
        discharge1_end=decode_time(registers[0x009A]),
        period2_enabled=period2_enabled,
        charge2_start=(decode_time(registers[0x009C]) if period2_enabled else None),
        charge2_end=(decode_time(registers[0x009D]) if period2_enabled else None),
        discharge2_start=(decode_time(registers[0x009E]) if period2_enabled else None),
        discharge2_end=(decode_time(registers[0x009F]) if period2_enabled else None),
    )
