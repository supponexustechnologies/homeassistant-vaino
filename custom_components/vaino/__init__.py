"""Väinö MusicMaster integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import VainoApiClient, PlaybackStatus, VainoApiError
from .const import CONF_HOST, CONF_PORT, DEFAULT_PORT, DOMAIN, PLATFORMS, POLLING_INTERVAL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Väinö from a config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)

    # Reuse HA's shared aiohttp session — do not create our own
    session = async_get_clientsession(hass)
    client = VainoApiClient(host, port, session)

    coordinator = VainoDataUpdateCoordinator(hass, client)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "coordinator": coordinator,
        "client": client,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Väinö config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok


class VainoDataUpdateCoordinator(DataUpdateCoordinator[PlaybackStatus]):
    """Polls the Väinö API on a fixed interval and distributes data to all entities."""

    def __init__(self, hass: HomeAssistant, client: VainoApiClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=POLLING_INTERVAL),
        )
        self.client = client

    async def _async_update_data(self) -> PlaybackStatus:
        try:
            return await self.client.get_playback()
        except VainoApiError as err:
            raise UpdateFailed(f"Error communicating with Väinö: {err}") from err
