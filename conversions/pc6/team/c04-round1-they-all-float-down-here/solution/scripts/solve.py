#!/usr/bin/env python3
"""
Automated solver for They All Float Down Here.
Sends the correct value pairs for all four parts and prints the tokens.
"""

import json
import struct
import sys
import urllib.request

SERVER = "http://float-server:8000"


def int_to_float(in_val: int) -> float:
    """Convert a 64-bit integer (bit pattern) to its IEEE 754 double representation."""
    packed = struct.pack(">q", in_val)
    return struct.unpack(">d", packed)[0]


def submit(part: int, v1: float, v2: float) -> str:
    payload = json.dumps({"value1": v1, "value2": v2}).encode()
    req = urllib.request.Request(
        f"{SERVER}/part{part}",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return resp.read().decode()


def main():
    global SERVER
    if len(sys.argv) > 1:
        SERVER = sys.argv[1].rstrip("/")

    solutions = [
        (1, 1e308, 1e308),        # addition overflow -> inf
        (2, 0.0, 9.785),          # 0/0 -> NaN
        (3, 1.5, 5e-324),         # bitwise left shift -> inf
        (4, -1.0, 2.0),           # bitwise XOR -> -inf
    ]

    for part, v1, v2 in solutions:
        print(f"Part {part}: submitting v1={v1}, v2={v2}")
        result = submit(part, v1, v2)
        print(f"  => {result}")
        print()


if __name__ == "__main__":
    main()
