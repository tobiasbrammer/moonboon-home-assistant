"""Action buttons for Moonboon Motor Connect."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import COMMANDS, DOMAIN, NAME
from .device import MoonboonDevice


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Create speed and transport buttons."""
    device: MoonboonDevice = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(MoonboonButton(device, action) for action in COMMANDS)


class MoonboonButton(ButtonEntity):
    """A verified command for the motor."""

    _attr_has_entity_name = True

    def __init__(self, device: MoonboonDevice, action: str) -> None:
        self._device = device
        self._action = action
        self._attr_unique_id = f"{device.address}_{action}"
        self._attr_translation_key = action
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device.address)},
            name=NAME,
            manufacturer="Moonboon",
            model="Motor Connect Basic",
        )

    async def async_press(self) -> None:
        """Send the command over Bluetooth."""
        await self._device.async_send(self._action)
