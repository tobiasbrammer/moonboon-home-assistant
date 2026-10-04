"""Discovery and configuration for Moonboon Motor Connect."""

from __future__ import annotations

from ipaddress import IPv4Address
from typing import Any

import voluptuous as vol
from aiohttp import ClientError, ClientTimeout

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, NAME, SERVICE_UUID


class MoonboonConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Choose a connectable Moonboon motor."""

    VERSION = 1

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle Bluetooth discovery."""
        if not discovery_info.connectable:
            return self.async_abort(reason="not_connectable")
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self.context["title_placeholders"] = {"name": NAME}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Ask the user to confirm the discovered motor."""
        if user_input is not None:
            return self.async_create_entry(
                title=NAME, data={"address": self.unique_id}
            )
        return self.async_show_form(step_id="bluetooth_confirm")

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Offer all Moonboon motors currently visible to Home Assistant."""
        devices = {
            info.address: info
            for info in bluetooth.async_discovered_service_info(
                self.hass, connectable=True
            )
            if info.name == "Moonboon"
            and SERVICE_UUID in (uuid.lower() for uuid in info.service_uuids)
        }
        if not devices:
            return await self.async_step_gateway()
        if user_input is not None:
            address = user_input["address"]
            if address not in devices:
                return self.async_abort(reason="no_devices_found")
            await self.async_set_unique_id(address)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=NAME, data={"address": address})
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("address"): vol.In(
                        {address: f"Moonboon ({address})" for address in devices}
                    )
                }
            ),
        )

    async def async_step_gateway(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Configure an existing Raspberry Pi gateway."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input["host"].strip()
            try:
                IPv4Address(host)
                async with async_get_clientsession(self.hass).get(
                    f"http://{host}:8765/health", timeout=ClientTimeout(total=5)
                ) as response:
                    if response.status != 200 or not (await response.json()).get("ok"):
                        errors["base"] = "cannot_connect"
            except (ClientError, TimeoutError, ValueError):
                errors["base"] = "cannot_connect"
            if not errors:
                await self.async_set_unique_id(f"gateway_{host}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"{NAME} (Pi)", data={"gateway_host": host}
                )
        return self.async_show_form(
            step_id="gateway",
            data_schema=vol.Schema({vol.Required("host", default="192.168.1.10"): str}),
            errors=errors,
        )
