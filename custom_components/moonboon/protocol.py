"""Encode the BLE commands observed from the Moonboon iPhone app.

The format is a small device header followed by CBOR. The speed programs and
their first timer values were captured twice on a Motor Connect Basic.
"""

from __future__ import annotations

import time

PROGRAMS: dict[str, tuple[tuple[int, ...], int]] = {
    "low": ((15, 12, 10, 7, 5, 2), 101),
    "medium": ((50, 41, 33, 25, 16, 8), 102),
    "high": ((100, 83, 66, 50, 33, 16), 103),
}


def _uint(value: int) -> bytes:
    if value < 0:
        raise ValueError("Negative CBOR integer")
    if value < 24:
        return bytes((value,))
    if value <= 0xFF:
        return bytes((0x18, value))
    if value <= 0xFFFF:
        return b"\x19" + value.to_bytes(2, "big")
    return b"\x1b" + value.to_bytes(8, "big")


def _text(value: str) -> bytes:
    raw = value.encode("utf-8")
    if len(raw) >= 24:
        raise ValueError("CBOR text too long")
    return bytes((0x60 | len(raw),)) + raw


def encode_command(command: str, now_ms: int | None = None) -> bytes:
    """Build a complete GATT write value for one supported command."""
    if command in PROGRAMS:
        speeds, first_timer = PROGRAMS[command]
        timestamp = int(time.time() * 1000) if now_ms is None else now_ms
        cbor = b"\xa2" + _text("sequence") + bytes((0x80 | len(speeds),))
        for index, speed in enumerate(speeds):
            cbor += (
                b"\xbf"
                + _text("speed")
                + _uint(speed)
                + _text("timer")
                + _uint(first_timer if index == 0 else 1)
                + b"\xff"
            )
        cbor += _text("time now") + b"\x1b" + timestamp.to_bytes(8, "big")
        message_type = 2
    elif command in ("start", "stop"):
        cbor = b"\xa1" + _text("command") + _text(command)
        message_type = 1
    else:
        raise ValueError(f"Unsupported Moonboon command: {command}")

    return b"\x0a\x00\x00" + len(cbor).to_bytes(2, "little") + b"\x41\x00" + bytes((message_type,)) + cbor
