"""Small authenticated Moonboon BLE bridge for a Raspberry Pi."""

from __future__ import annotations

import asyncio
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from bleak import BleakClient, BleakScanner

from custom_components.moonboon.const import COMMANDS, CONTROL_UUID, SERVICE_UUID
from custom_components.moonboon.protocol import encode_command

HOST = os.environ.get("MOONBOON_HOST", "192.168.1.10")
PORT = int(os.environ.get("MOONBOON_PORT", "8765"))
ALLOWED_CLIENT = os.environ.get("MOONBOON_ALLOWED_CLIENT", "192.168.1.9")
LOCK = threading.Lock()


def is_moonboon(device, advertisement) -> bool:
    return device.name == "Moonboon" and SERVICE_UUID in (
        uuid.lower() for uuid in advertisement.service_uuids
    )


async def find_motor():
    found = await BleakScanner.discover(timeout=8, return_adv=True)
    for device, advertisement in found.values():
        if is_moonboon(device, advertisement):
            return device
    return None


async def send_command(command: str) -> None:
    with LOCK:
        motor = await find_motor()
        if motor is None:
            raise LookupError("Moonboon motor was not found; press its Bluetooth button once")
        acknowledged = asyncio.Event()

        def notification(_, data: bytearray) -> None:
            if b"rc" in data:
                acknowledged.set()

        async with BleakClient(motor, timeout=20) as client:
            await client.start_notify(CONTROL_UUID, notification)
            await client.write_gatt_char(CONTROL_UUID, encode_command(command), response=False)
            await asyncio.wait_for(acknowledged.wait(), timeout=5)


class Handler(BaseHTTPRequestHandler):
    def respond(self, code: int, body: dict) -> None:
        payload = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def authorized(self) -> bool:
        return self.client_address[0] in {ALLOWED_CLIENT, "127.0.0.1"}

    def do_GET(self) -> None:
        if not self.authorized():
            self.respond(403, {"error": "Forbidden"})
        elif self.path == "/health":
            self.respond(200, {"ok": True})
        elif self.path == "/motor":
            try:
                motor = asyncio.run(find_motor())
                self.respond(200, {"address": motor.address if motor else None})
            except Exception as err:
                self.respond(503, {"error": str(err)})
        else:
            self.respond(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if not self.authorized():
            self.respond(403, {"error": "Forbidden"})
        elif self.path not in {f"/command/{command}" for command in COMMANDS}:
            self.respond(404, {"error": "Unknown command"})
        else:
            try:
                asyncio.run(send_command(self.path.rsplit("/", 1)[1]))
                self.respond(200, {"ok": True})
            except LookupError as err:
                self.respond(404, {"error": str(err)})
            except Exception as err:
                self.respond(503, {"error": str(err)})


if __name__ == "__main__":
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
