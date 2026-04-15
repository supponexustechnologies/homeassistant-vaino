"""Tests for the Väinö API client."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import aiohttp
import pytest

from custom_components.vaino.api import (
    AudioOutputType,
    CannotConnect,
    PlaybackState,
    RepeatMode,
    VainoApiClient,
    VainoApiError,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_client(session=None) -> VainoApiClient:
    return VainoApiClient("192.168.5.248", 5000, session or MagicMock())


# ── Enum parsing — integer values (C# default serialization) ──────────────────

class TestEnumParsingIntegers:
    """C# serializes enums as integers by default — these must parse correctly."""

    def test_playback_state_stopped(self):
        client = make_client()
        result = client._parse_playback({"state": 0, "volume": 50, "repeat": 0, "shuffle": False})
        assert result.state == PlaybackState.STOPPED

    def test_playback_state_playing(self):
        client = make_client()
        result = client._parse_playback({"state": 1, "volume": 75, "repeat": 0, "shuffle": False})
        assert result.state == PlaybackState.PLAYING

    def test_playback_state_paused(self):
        client = make_client()
        result = client._parse_playback({"state": 2, "volume": 75, "repeat": 0, "shuffle": False})
        assert result.state == PlaybackState.PAUSED

    def test_repeat_off(self):
        client = make_client()
        result = client._parse_playback({"state": 0, "volume": 50, "repeat": 0, "shuffle": False})
        assert result.repeat == RepeatMode.OFF

    def test_repeat_single(self):
        client = make_client()
        result = client._parse_playback({"state": 0, "volume": 50, "repeat": 1, "shuffle": False})
        assert result.repeat == RepeatMode.SINGLE

    def test_repeat_all(self):
        client = make_client()
        result = client._parse_playback({"state": 0, "volume": 50, "repeat": 2, "shuffle": False})
        assert result.repeat == RepeatMode.ALL

    def test_audio_output_type_integer(self):
        client = make_client()
        result = client._parse_output({"id": 0, "name": "Analog", "type": 1, "isEnabled": True})
        assert result.type == AudioOutputType.ANALOG

    def test_audio_output_type_hdmi(self):
        client = make_client()
        result = client._parse_output({"id": 1, "name": "HDMI", "type": 0, "isEnabled": False})
        assert result.type == AudioOutputType.HDMI

    def test_audio_output_type_bluetooth(self):
        client = make_client()
        result = client._parse_output({"id": 2, "name": "BT Speaker", "type": 4, "isEnabled": False})
        assert result.type == AudioOutputType.BLUETOOTH


# ── Enum parsing — string values ──────────────────────────────────────────────

class TestEnumParsingStrings:
    """String enum values should also parse correctly."""

    def test_playback_state_string(self):
        client = make_client()
        result = client._parse_playback({"state": "Playing", "volume": 75, "repeat": "Off", "shuffle": False})
        assert result.state == PlaybackState.PLAYING

    def test_repeat_string(self):
        client = make_client()
        result = client._parse_playback({"state": "Stopped", "volume": 50, "repeat": "All", "shuffle": False})
        assert result.repeat == RepeatMode.ALL

    def test_output_type_string(self):
        client = make_client()
        result = client._parse_output({"id": 0, "name": "Analog", "type": "Analog", "isEnabled": True})
        assert result.type == AudioOutputType.ANALOG


# ── Playback parsing ──────────────────────────────────────────────────────────

class TestParsePlayback:

    def test_no_current_track(self):
        client = make_client()
        result = client._parse_playback({
            "state": 0, "volume": 50, "repeat": 0, "shuffle": False,
            "currentTrack": None,
        })
        assert result.current_track is None

    def test_with_current_track(self):
        client = make_client()
        result = client._parse_playback({
            "state": 1, "volume": 75, "repeat": 0, "shuffle": False,
            "position": 42.5, "duration": 312.0,
            "currentTrack": {
                "id": 1, "title": "Hells Bells", "artist": "AC/DC",
                "album": "Back in Black", "duration": 312.0,
                "trackNumber": 1, "discNumber": 1,
                "genre": "Rock", "filePath": "/music/hells_bells.mp3",
                "albumArtUrl": "/api/art/album/5", "playCount": 3,
            },
        })
        assert result.current_track is not None
        assert result.current_track.title == "Hells Bells"
        assert result.current_track.artist == "AC/DC"
        assert result.current_track.album_art_url == "/api/art/album/5"
        assert result.position == 42.5
        assert result.duration == 312.0

    def test_shuffle_true(self):
        client = make_client()
        result = client._parse_playback({"state": 1, "volume": 80, "repeat": 0, "shuffle": True})
        assert result.shuffle is True

    def test_is_indexing(self):
        client = make_client()
        result = client._parse_playback({"state": 0, "volume": 50, "repeat": 0, "shuffle": False, "isIndexing": True})
        assert result.is_indexing is True

    def test_optional_fields_default(self):
        client = make_client()
        result = client._parse_playback({"state": 0, "volume": 50, "repeat": 0, "shuffle": False})
        assert result.position == 0.0
        assert result.duration == 0.0
        assert result.audio_output is None
        assert result.song_id is None
        assert result.is_indexing is False


# ── System status parsing ─────────────────────────────────────────────────────

class TestParseSystemStatus:

    def test_parses_correctly(self):
        client = make_client()
        result = client._parse_system_status({
            "version": "1.0.0",
            "mpdConnected": True,
            "databaseTrackCount": 1234,
            "uptime": "01:23:45",
        })
        assert result.version == "1.0.0"
        assert result.mpd_connected is True
        assert result.database_track_count == 1234
        assert result.uptime == "01:23:45"


# ── EQ preset parsing ─────────────────────────────────────────────────────────

class TestParseEqPreset:

    def test_parses_correctly(self):
        client = make_client()
        result = client._parse_eq_preset({
            "id": 1, "name": "Rock", "bands": [1.0] * 15, "isRoomTuned": False,
        })
        assert result.id == 1
        assert result.name == "Rock"
        assert len(result.bands) == 15
        assert result.is_room_tuned is False

    def test_room_tuned(self):
        client = make_client()
        result = client._parse_eq_preset({
            "id": 2, "name": "Room Tuned", "bands": [0.5] * 15, "isRoomTuned": True,
        })
        assert result.is_room_tuned is True


# ── Art URL helpers ───────────────────────────────────────────────────────────

class TestArtUrls:

    def test_album_art_url(self):
        client = make_client()
        assert client.album_art_url(5) == "http://192.168.5.248:5000/api/art/album/5"

    def test_artist_art_url(self):
        client = make_client()
        assert client.artist_art_url(3) == "http://192.168.5.248:5000/api/art/artist/3"


# ── Connection error handling ─────────────────────────────────────────────────

class TestConnectionErrors:

    @pytest.mark.asyncio
    async def test_cannot_connect_raises_on_connector_error(self):
        session = MagicMock()
        session.get = MagicMock(side_effect=aiohttp.ClientConnectorError(
            MagicMock(), OSError("connection refused")
        ))
        client = VainoApiClient("192.168.5.248", 5000, session)
        with pytest.raises(CannotConnect):
            await client._get("/api/system/status")

    @pytest.mark.asyncio
    async def test_vaino_api_error_on_http_error(self):
        mock_resp = AsyncMock()
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=False)
        mock_resp.raise_for_status = MagicMock(side_effect=aiohttp.ClientResponseError(
            MagicMock(), MagicMock(), status=500
        ))
        session = MagicMock()
        session.get = MagicMock(return_value=mock_resp)
        client = VainoApiClient("192.168.5.248", 5000, session)
        with pytest.raises(VainoApiError):
            await client._get("/api/system/status")
