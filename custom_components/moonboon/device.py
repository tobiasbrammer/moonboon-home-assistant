"""Bluetooth transport for a Moonboon Motor Connect."""

from __future__ import annotations

import asyncio
import logging

from bleak import BleakClient
from bleak.exc import BleakError
from bleak_retry_connector import establish_connection

from homeassistant.components import bluetooth
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from .const import CONTROL_UUID, NAME
from .protocol import encode_command

_LOGGER = logging.getLogger(__name__)


class MoonboonDevice:
    """Send one command at a time, releasing the BLE connection afterward."""

    def __init__(self, hass: HomeAssistant, address: str) -> None:
        self.hass = hass
        self.address = address
        self._lock = asyncio.Lock()

    async def async_send(self, command: str) -> None:
        """Send a command and wait for the motor's notification."""
        async with self._lock:
            ble_device = bluetooth.async_ble_device_from_address(
                self.hass, self.address, connectable=True
            )
            if ble_device is None:
                raise HomeAssistantError(
                    "Moonboon is out of range or no connectable Bluetooth adapter is available"
                )

            client: BleakClient | None = None
            acknowledged = asyncio.Event()

            def notification(_: int, data: bytearray) -> None:
                if b"rc" in data:
                    acknowledged.set()

            try:
                client = await establish_connection(BleakClient, ble_device, NAME)
                await client.start_notify(CONTROL_UUID, notification)
                await client.write_gatt_char(
                    CONTROL_UUID, encode_command(command), response=False
                )
                try:
                    await asyncio.wait_for(acknowledged.wait(), timeout=5)
                except TimeoutError as err:
                    raise HomeAssistantError(
                        "Moonboon command was sent but no acknowledgement arrived"
                    ) from err
            except (BleakError, TimeoutError) as err:
                raise HomeAssistantError(f"Could not control Moonboon: {err}") from err
            finally:
                if client is not None and client.is_connected:
                    try:
                        await client.disconnect()
                    except BleakError:
                        _LOGGER.debug("Moonboon disconnect failed", exc_info=True)
