"""Select entities for Väinö MusicMaster."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
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
        VainoEqPresetSelect(client, entry),
        VainoAudioOutputSelect(client, entry),
    ])


class VainoEqPresetSelect(SelectEntity):
    """Select the active EQ preset on the Väinö device."""

    _attr_has_entity_name = True
    _attr_name = "EQ Preset"
    _attr_icon = "mdi:equalizer"

    def __init__(self, client: VainoApiClient, entry: ConfigEntry) -> None:
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_select_eq_preset"
        self._entry = entry
        self._presets: dict[str, int] = {}  # name → id
        self._attr_options: list[str] = []
        self._attr_current_option: str | None = None

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
            presets = await self._client.get_eq_presets()
            self._presets = {p.name: p.id for p in presets}
            self._attr_options = list(self._presets.keys())

            # Reflect the last-used preset as the current selection
            data = await self._client._get("/api/equalizer/presets/last-used")
            if data and data.get("name") in self._presets:
                self._attr_current_option = data["name"]
            elif self._attr_options:
                self._attr_current_option = self._attr_options[0]
        except VainoApiError as err:
            _LOGGER.warning("Could not fetch EQ presets: %s", err)

    async def async_select_option(self, option: str) -> None:
        preset_id = self._presets.get(option)
        if preset_id is None:
            _LOGGER.error("Unknown EQ preset: %s", option)
            return
        try:
            await self._client.apply_eq_preset(preset_id)
            self._attr_current_option = option
            self.async_write_ha_state()
        except VainoApiError as err:
            _LOGGER.error("Failed to apply EQ preset '%s': %s", option, err)


class VainoAudioOutputSelect(SelectEntity):
    """Select the active audio output on the Väinö device."""

    _attr_has_entity_name = True
    _attr_name = "Audio Output"
    _attr_icon = "mdi:speaker"

    def __init__(self, client: VainoApiClient, entry: ConfigEntry) -> None:
        self._client = client
        self._attr_unique_id = f"{entry.entry_id}_select_audio_output"
        self._entry = entry
        self._outputs: dict[str, int] = {}  # name → id
        self._attr_options: list[str] = []
        self._attr_current_option: str | None = None

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
            outputs = await self._client.get_outputs()
            self._outputs = {o.name: o.id for o in outputs}
            self._attr_options = list(self._outputs.keys())
            enabled = next((o for o in outputs if o.is_enabled), None)
            self._attr_current_option = enabled.name if enabled else (self._attr_options[0] if self._attr_options else None)
        except VainoApiError as err:
            _LOGGER.warning("Could not fetch audio outputs: %s", err)

    async def async_select_option(self, option: str) -> None:
        output_id = self._outputs.get(option)
        if output_id is None:
            _LOGGER.error("Unknown audio output: %s", option)
            return
        try:
            # Disable all other outputs, enable the selected one
            for name, oid in self._outputs.items():
                if name == option:
                    await self._client.enable_output(oid)
                else:
                    await self._client.disable_output(oid)
            self._attr_current_option = option
            self.async_write_ha_state()
        except VainoApiError as err:
            _LOGGER.error("Failed to switch audio output to '%s': %s", option, err)
