"""HTTP transport for a Moonboon motor controlled by a Raspberry Pi."""

from __future__ import annotations

import asyncio

from aiohttp import ClientError, ClientTimeout

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import NAME


class MoonboonGateway:
    """Send commands to a LAN-only Pi gateway."""

    def __init__(self, hass: HomeAssistant, host: str) -> None:
        self.hass = hass
        self.host = host
        self.address = f"gateway_{host}"
        self._lock = asyncio.Lock()

    async def async_send(self, command: str) -> None:
        """Send a command and wait for the Pi to confirm the BLE response."""
        async with self._lock:
            try:
                async with async_get_clientsession(self.hass).post(
                    f"http://{self.host}:8765/command/{command}",
                    timeout=ClientTimeout(total=70),
                ) as response:
                    result = await response.json()
                    if response.status != 200:
                        raise HomeAssistantError(result.get("error", NAME))
            except (ClientError, TimeoutError) as err:
                raise HomeAssistantError(f"Could not reach Moonboon Pi gateway: {err}") from err
