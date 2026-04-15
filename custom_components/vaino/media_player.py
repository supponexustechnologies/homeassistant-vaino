"""Media player entity for Väinö MusicMaster."""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
    RepeatMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import VainoDataUpdateCoordinator
from .api import PlaybackState, RepeatMode as VainoRepeatMode, VainoApiClient
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SUPPORTED_FEATURES = (
    MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.SEEK
    | MediaPlayerEntityFeature.SHUFFLE_SET
    | MediaPlayerEntityFeature.REPEAT_SET
    | MediaPlayerEntityFeature.BROWSE_MEDIA
)

# Map Väinö repeat modes to HA repeat modes
_REPEAT_TO_HA: dict[VainoRepeatMode, RepeatMode] = {
    VainoRepeatMode.OFF:    RepeatMode.OFF,
    VainoRepeatMode.SINGLE: RepeatMode.ONE,
    VainoRepeatMode.ALL:    RepeatMode.ALL,
}

_REPEAT_FROM_HA: dict[RepeatMode, VainoRepeatMode] = {
    v: k for k, v in _REPEAT_TO_HA.items()
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Väinö media player from a config entry."""
    data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VainoMediaPlayer(data["coordinator"], data["client"], entry)])


class VainoMediaPlayer(CoordinatorEntity[VainoDataUpdateCoordinator], MediaPlayerEntity):
    """Representation of the Väinö media player."""

    _attr_has_entity_name = True
    _attr_name = None  # Use device name as entity name
    _attr_media_content_type = MediaType.MUSIC
    _attr_supported_features = SUPPORTED_FEATURES

    def __init__(
        self,
        coordinator: VainoDataUpdateCoordinator,
        client: VainoApiClient,
        entry: ConfigEntry,
    ) -> None:
        super().__init__(coordinator)
        self._client = client
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_media_player"
        self._position_updated_at: datetime | None = None
        self._last_song_id: int | None = None

    @property
    def device_info(self) -> dict:
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Väinö",
            "manufacturer": "SuppoNexus Technologies",
            "model": "MusicMaster Pi",
        }

    # ── State ─────────────────────────────────────────────────────────────────

    @property
    def state(self) -> MediaPlayerState:
        match self.coordinator.data.state:
            case PlaybackState.PLAYING:
                return MediaPlayerState.PLAYING
            case PlaybackState.PAUSED:
                return MediaPlayerState.PAUSED
            case _:
                return MediaPlayerState.IDLE

    # ── Volume ────────────────────────────────────────────────────────────────

    @property
    def volume_level(self) -> float:
        return self.coordinator.data.volume / 100

    # ── Now playing ───────────────────────────────────────────────────────────

    @property
    def media_title(self) -> str | None:
        track = self.coordinator.data.current_track
        return track.title if track else None

    @property
    def media_artist(self) -> str | None:
        track = self.coordinator.data.current_track
        return track.artist if track else None

    @property
    def media_album_name(self) -> str | None:
        track = self.coordinator.data.current_track
        return track.album if track else None

    @property
    def media_duration(self) -> float | None:
        return self.coordinator.data.duration or None

    @property
    def media_position(self) -> float | None:
        return self.coordinator.data.position or None

    @property
    def media_position_updated_at(self) -> datetime | None:
        return self._position_updated_at

    # ── Album art ─────────────────────────────────────────────────────────────

    @property
    def media_image_url(self) -> str | None:
        track = self.coordinator.data.current_track
        if track and track.id:
            return self._client.album_art_url(track.id)
        return None

    @property
    def media_image_remotely_accessible(self) -> bool:
        # The Pi is on the local network — HA can proxy it
        return False

    # ── Shuffle / repeat ──────────────────────────────────────────────────────

    @property
    def shuffle(self) -> bool:
        return self.coordinator.data.shuffle

    @property
    def repeat(self) -> RepeatMode:
        return _REPEAT_TO_HA.get(self.coordinator.data.repeat, RepeatMode.OFF)

    # ── Coordinator callback ──────────────────────────────────────────────────

    def _handle_coordinator_update(self) -> None:
        """Track position timestamp when song changes or state changes to playing."""
        data = self.coordinator.data
        if (
            data.state == PlaybackState.PLAYING
            and data.song_id != self._last_song_id
        ):
            self._position_updated_at = datetime.now(timezone.utc)
            self._last_song_id = data.song_id
        elif data.state != PlaybackState.PLAYING:
            self._last_song_id = None
        super()._handle_coordinator_update()

    # ── Transport controls ────────────────────────────────────────────────────

    async def async_media_play(self) -> None:
        await self._client.play()
        await self.coordinator.async_request_refresh()

    async def async_media_pause(self) -> None:
        await self._client.pause()
        await self.coordinator.async_request_refresh()

    async def async_media_stop(self) -> None:
        await self._client.stop()
        await self.coordinator.async_request_refresh()

    async def async_media_next_track(self) -> None:
        await self._client.next_track()
        await self.coordinator.async_request_refresh()

    async def async_media_previous_track(self) -> None:
        await self._client.previous_track()
        await self.coordinator.async_request_refresh()

    async def async_set_volume_level(self, volume: float) -> None:
        await self._client.set_volume(round(volume * 100))
        await self.coordinator.async_request_refresh()

    async def async_media_seek(self, position: float) -> None:
        await self._client.seek(position)
        self._position_updated_at = datetime.now(timezone.utc)
        await self.coordinator.async_request_refresh()

    async def async_set_shuffle(self, shuffle: bool) -> None:
        await self._client.set_shuffle(shuffle)
        await self.coordinator.async_request_refresh()

    async def async_set_repeat(self, repeat: RepeatMode) -> None:
        vaino_mode = _REPEAT_FROM_HA.get(repeat, VainoRepeatMode.OFF)
        await self._client.set_repeat(vaino_mode)
        await self.coordinator.async_request_refresh()

    # ── Media browser ─────────────────────────────────────────────────────────

    async def async_browse_media(
        self,
        media_content_type: str | None = None,
        media_content_id: str | None = None,
    ) -> Any:
        """Browse the Väinö library — implemented in Phase 3."""
        from homeassistant.components.media_player import BrowseMedia
        from homeassistant.components.media_player.errors import BrowseError
        raise BrowseError("Media browsing coming in Phase 3")

    async def async_play_media(
        self,
        media_type: str,
        media_id: str,
        **kwargs: Any,
    ) -> None:
        """Play media selected from the browser — implemented in Phase 3."""
        _LOGGER.warning("async_play_media called before Phase 3 is implemented: %s / %s", media_type, media_id)
