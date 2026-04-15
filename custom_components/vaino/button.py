"""Button entities for Väinö MusicMaster."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import VainoApiClient, VainoApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    client: VainoApiClient = hass.data[DOMAIN][entry.entry_id]["client"]
    async_add_entities([
        VainoScanLibraryButton(client, entry),
        VainoRebootButton(client, entry),
    ])


class VainoScanLibraryButton(ButtonEntity):
    """Trigger a library scan on the Väinö device."""

    _attr_has_entity_name = True
    _attr_name = "Scan Library"
    _attr_icon = "mdi:database-refresh"

    def __init__(self, client: VainoApiClient, entry: ConfigEntry) -> None:
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_button_scan_library"
        self._entry = entry

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Väinö",
            "manufacturer": "SuppoNexus Technologies",
            "model": "MusicMaster Pi",
        }

    async def async_press(self) -> None:
        try:
            await self._client.scan_library()
            _LOGGER.info("Väinö library scan triggered.")
        except VainoApiError as err:
            _LOGGER.error("Failed to trigger library scan: %s", err)


class VainoRebootButton(ButtonEntity):
    """Reboot the Väinö Pi device."""

    _attr_has_entity_name = True
    _attr_name = "Reboot"
    _attr_icon = "mdi:restart"

    def __init__(self, client: VainoApiClient, entry: ConfigEntry) -> None:
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_button_reboot"
        self._entry = entry

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Väinö",
            "manufacturer": "SuppoNexus Technologies",
            "model": "MusicMaster Pi",
        }

    async def async_press(self) -> None:
        try:
            await self._client.reboot()
            _LOGGER.warning("Väinö reboot initiated.")
        except VainoApiError as err:
            _LOGGER.error("Failed to reboot Väinö: %s", err)
