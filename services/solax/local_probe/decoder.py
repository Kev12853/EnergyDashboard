def signed16(value: int) -> int:

    if value > 32767:
        return value - 65536

    return value


def signed32(msb: int, lsb: int) -> int:

    unsigned32 = (msb * 65536) + lsb

    if unsigned32 > 2147483647:
        return unsigned32 - 4294967296

    return unsigned32