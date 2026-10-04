"""Discovery and configuration for Moonboon Motor Connect."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.data_entry_flow import FlowResult

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
            return self.async_abort(reason="no_devices_found")
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
