"""Sensor entities for Väinö MusicMaster."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import VainoApiClient, VainoApiError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(minutes=5)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    client: VainoApiClient = hass.data[DOMAIN][entry.entry_id]["client"]
    async_add_entities([
        VainoLibrarySensor(client, entry, "songs",   "Tracks",  "mdi:music-note"),
        VainoLibrarySensor(client, entry, "artists", "Artists", "mdi:account-music"),
        VainoLibrarySensor(client, entry, "albums",  "Albums",  "mdi:album"),
    ])


class VainoLibrarySensor(SensorEntity):
    """Reports a single library count statistic from Väinö."""

    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = None
    _attr_has_entity_name = True

    def __init__(
        self,
        client: VainoApiClient,
        entry: ConfigEntry,
        stat_key: str,
        label: str,
        icon: str,
    ) -> None:
        self._client = client
        self._stat_key = stat_key
        self._attr_name = label
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_sensor_{stat_key}"
        self._attr_native_value: int | None = None
        self._entry = entry

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Väinö",
            "manufacturer": "SuppoNexus Technologies",
            "model": "MusicMaster Pi",
        }

    async def async_update(self) -> None:
        try:
            stats = await self._client.get_library_stats()
            self._attr_native_value = getattr(stats, self._stat_key)
        except VainoApiError as err:
            _LOGGER.warning("Could not fetch library stats: %s", err)
