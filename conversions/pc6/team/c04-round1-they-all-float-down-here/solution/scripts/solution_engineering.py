import struct


def int_to_float(in_val: int) -> float:
    packed = struct.pack('>q', in_val)
    return struct.unpack('>d', packed)[0]


def bytes_to_int(in_bytes: bytes) -> int:
    return struct.unpack('>q', in_bytes)[0]


def bits_to_byte(
    b1: bool,
    b2: bool,
    b3: bool,
    b4: bool,
    b5: bool,
    b6: bool,
    b7: bool,
    b8: bool
) -> int:
    return int(b1) * 128 \
        + int(b2) * 64 \
        + int(b3) * 32 \
        + int(b4) * 16 \
        + int(b5) * 8 \
        + int(b6) * 4 \
        + int(b7) * 2 \
        + int(b8)


def main():
    print(int_to_float(1))
    print(int_to_float(2))
    print(int_to_float(3))

    q3_first_byte = bits_to_byte(0, 0, 1, 1, 1, 1, 1, 1)
    q3_second_byte = bits_to_byte(1, 1, 1, 1, 1, 0, 0, 0)
    q3_bytes = bytes([q3_first_byte, q3_second_byte, 0, 0, 0, 0, 0, 0])
    q3_int_val = bytes_to_int(q3_bytes)
    print(int_to_float(q3_int_val))


if __name__ == "__main__":
    main()
