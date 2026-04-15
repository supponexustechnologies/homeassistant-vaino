"""Test fixtures for Väinö integration tests."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.vaino.api import (
    AudioOutput,
    AudioOutputType,
    EqPreset,
    LibraryStats,
    PlaybackState,
    PlaybackStatus,
    RepeatMode,
    SystemStatus,
    TrackInfo,
    VainoApiClient,
)
from custom_components.vaino.const import CONF_HOST, CONF_PORT, DEFAULT_PORT, DOMAIN


# ── Shared data fixtures ──────────────────────────────────────────────────────

@pytest.fixture
def mock_track() -> TrackInfo:
    return TrackInfo(
        id=1,
        title="Hells Bells",
        artist="AC/DC",
        album="Back in Black",
        duration=312.0,
        track_number=1,
        disc_number=1,
        genre="Rock",
        file_path="/opt/musicmaster/music/acdc/hells_bells.mp3",
        album_art_url="/api/art/album/5",
        play_count=3,
    )


@pytest.fixture
def mock_playback_playing(mock_track) -> PlaybackStatus:
    return PlaybackStatus(
        state=PlaybackState.PLAYING,
        volume=75,
        repeat=RepeatMode.OFF,
        shuffle=False,
        position=42.0,
        duration=312.0,
        audio_output="Analog",
        song_id=1,
        is_indexing=False,
        current_track=mock_track,
    )


@pytest.fixture
def mock_playback_stopped() -> PlaybackStatus:
    return PlaybackStatus(
        state=PlaybackState.STOPPED,
        volume=50,
        repeat=RepeatMode.OFF,
        shuffle=False,
        current_track=None,
    )


@pytest.fixture
def mock_system_status() -> SystemStatus:
    return SystemStatus(
        version="1.0.0",
        mpd_connected=True,
        database_track_count=1234,
        uptime="01:23:45",
    )


@pytest.fixture
def mock_outputs() -> list[AudioOutput]:
    return [
        AudioOutput(id=0, name="Analog",    type=AudioOutputType.ANALOG,    is_enabled=True),
        AudioOutput(id=1, name="HDMI",      type=AudioOutputType.HDMI,      is_enabled=False),
        AudioOutput(id=2, name="Bluetooth", type=AudioOutputType.BLUETOOTH, is_enabled=False),
    ]


@pytest.fixture
def mock_eq_presets() -> list[EqPreset]:
    return [
        EqPreset(id=1, name="Flat",       bands=[0.0] * 15, is_room_tuned=False),
        EqPreset(id=2, name="Rock",       bands=[2.0, 1.5, 0.0, -1.0, -1.5, -1.0, 0.0, 1.5, 2.0, 2.5, 2.0, 1.5, 1.0, 0.5, 0.0], is_room_tuned=False),
        EqPreset(id=3, name="Room Tuned", bands=[1.0] * 15, is_room_tuned=True),
    ]


@pytest.fixture
def mock_library_stats() -> LibraryStats:
    return LibraryStats(artists=42, albums=187, songs=1234)


# ── API client fixture ────────────────────────────────────────────────────────

@pytest.fixture
def mock_client(mock_playback_playing, mock_system_status, mock_outputs, mock_eq_presets, mock_library_stats):
    client = MagicMock(spec=VainoApiClient)
    client._base = "http://192.168.5.248:5000"
    client.get_playback       = AsyncMock(return_value=mock_playback_playing)
    client.test_connection    = AsyncMock(return_value=mock_system_status)
    client.get_system_status  = AsyncMock(return_value=mock_system_status)
    client.get_outputs        = AsyncMock(return_value=mock_outputs)
    client.get_eq_presets     = AsyncMock(return_value=mock_eq_presets)
    client.get_library_stats  = AsyncMock(return_value=mock_library_stats)
    client.play               = AsyncMock()
    client.pause              = AsyncMock()
    client.stop               = AsyncMock()
    client.next_track         = AsyncMock()
    client.previous_track     = AsyncMock()
    client.set_volume         = AsyncMock()
    client.seek               = AsyncMock()
    client.set_shuffle        = AsyncMock()
    client.set_repeat         = AsyncMock()
    client.scan_library       = AsyncMock()
    client.reboot             = AsyncMock()
    client.enable_output      = AsyncMock()
    client.disable_output     = AsyncMock()
    client.apply_eq_preset    = AsyncMock()
    client.get_artists        = AsyncMock(return_value=[{"id": 1, "name": "AC/DC"}])
    client.get_albums         = AsyncMock(return_value=[{"id": 5, "title": "Back in Black", "artist": "AC/DC"}])
    client.get_tracks         = AsyncMock(return_value=[{"id": 1, "title": "Hells Bells", "filePath": "/music/hells_bells.mp3", "album": "Back in Black"}])
    client.album_art_url      = MagicMock(side_effect=lambda aid: f"http://192.168.5.248:5000/api/art/album/{aid}")
    client.artist_art_url     = MagicMock(side_effect=lambda aid: f"http://192.168.5.248:5000/api/art/artist/{aid}")
    return client


# ── Config entry fixture ──────────────────────────────────────────────────────

@pytest.fixture
def config_entry_data() -> dict:
    return {CONF_HOST: "192.168.5.248", CONF_PORT: DEFAULT_PORT}
