from app.enums.solax_enums import WorkMode


def decode_work_mode(value: str | int) -> WorkMode:
    return WorkMode(int(value))