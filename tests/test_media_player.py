"""Tests for the Väinö media player entity."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.components.media_player import MediaPlayerState, RepeatMode

from custom_components.vaino.api import (
    PlaybackState,
    PlaybackStatus,
    RepeatMode as VainoRepeatMode,
    TrackInfo,
)
from custom_components.vaino.media_player import VainoMediaPlayer


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_player(playback: PlaybackStatus, client=None) -> VainoMediaPlayer:
    coordinator = MagicMock()
    coordinator.data = playback
    coordinator.async_request_refresh = AsyncMock()
    entry = MagicMock()
    entry.entry_id = "test_entry"
    player = VainoMediaPlayer(coordinator, client or MagicMock(), entry)
    player._client._base = "http://192.168.5.248:5000"
    return player


def stopped() -> PlaybackStatus:
    return PlaybackStatus(
        state=PlaybackState.STOPPED, volume=50,
        repeat=VainoRepeatMode.OFF, shuffle=False,
    )


def playing(track: TrackInfo | None = None) -> PlaybackStatus:
    return PlaybackStatus(
        state=PlaybackState.PLAYING, volume=75,
        repeat=VainoRepeatMode.OFF, shuffle=False,
        position=42.0, duration=312.0,
        song_id=1, current_track=track,
    )


def paused() -> PlaybackStatus:
    return PlaybackStatus(
        state=PlaybackState.PAUSED, volume=60,
        repeat=VainoRepeatMode.ALL, shuffle=True,
    )


def make_track(**kwargs) -> TrackInfo:
    defaults = dict(
        id=1, title="Hells Bells", artist="AC/DC",
        album="Back in Black", duration=312.0,
        track_number=1, disc_number=1,
        album_art_url="/api/art/album/5",
    )
    defaults.update(kwargs)
    return TrackInfo(**defaults)


# ── State mapping ─────────────────────────────────────────────────────────────

class TestState:

    def test_playing(self):
        assert make_player(playing()).state == MediaPlayerState.PLAYING

    def test_paused(self):
        assert make_player(paused()).state == MediaPlayerState.PAUSED

    def test_stopped(self):
        assert make_player(stopped()).state == MediaPlayerState.IDLE


# ── Volume ────────────────────────────────────────────────────────────────────

class TestVolume:

    def test_volume_converts_to_float(self):
        assert make_player(playing()).volume_level == pytest.approx(0.75)

    def test_volume_zero(self):
        s = stopped()
        s.volume = 0
        assert make_player(s).volume_level == pytest.approx(0.0)

    def test_volume_max(self):
        s = stopped()
        s.volume = 100
        assert make_player(s).volume_level == pytest.approx(1.0)


# ── Now playing ───────────────────────────────────────────────────────────────

class TestNowPlaying:

    def test_title(self):
        assert make_player(playing(make_track())).media_title == "Hells Bells"

    def test_artist(self):
        assert make_player(playing(make_track())).media_artist == "AC/DC"

    def test_album(self):
        assert make_player(playing(make_track())).media_album_name == "Back in Black"

    def test_duration(self):
        assert make_player(playing(make_track())).media_duration == pytest.approx(312.0)

    def test_position(self):
        assert make_player(playing(make_track())).media_position == pytest.approx(42.0)

    def test_no_track_returns_none(self):
        player = make_player(stopped())
        assert player.media_title is None
        assert player.media_artist is None
        assert player.media_album_name is None


# ── Album art ─────────────────────────────────────────────────────────────────

class TestMediaImageUrl:

    def test_relative_url_made_absolute(self):
        player = make_player(playing(make_track(album_art_url="/api/art/album/5")))
        assert player.media_image_url == "http://192.168.5.248:5000/api/art/album/5"

    def test_absolute_url_returned_as_is(self):
        player = make_player(playing(make_track(album_art_url="http://192.168.5.248:5000/api/art/album/5")))
        assert player.media_image_url == "http://192.168.5.248:5000/api/art/album/5"

    def test_no_track_returns_none(self):
        assert make_player(stopped()).media_image_url is None

    def test_track_with_no_art_returns_none(self):
        player = make_player(playing(make_track(album_art_url=None)))
        assert player.media_image_url is None


# ── Shuffle and repeat ────────────────────────────────────────────────────────

class TestShuffleRepeat:

    def test_shuffle_false(self):
        assert make_player(playing()).shuffle is False

    def test_shuffle_true(self):
        assert make_player(paused()).shuffle is True

    def test_repeat_off(self):
        assert make_player(playing()).repeat == RepeatMode.OFF

    def test_repeat_all(self):
        assert make_player(paused()).repeat == RepeatMode.ALL

    def test_repeat_single(self):
        s = stopped()
        s.repeat = VainoRepeatMode.SINGLE
        assert make_player(s).repeat == RepeatMode.ONE


# ── Transport controls ────────────────────────────────────────────────────────

class TestTransportControls:

    @pytest.mark.asyncio
    async def test_play(self):
        client = MagicMock()
        client.play = AsyncMock()
        player = make_player(stopped(), client)
        await player.async_media_play()
        client.play.assert_called_once()

    @pytest.mark.asyncio
    async def test_pause(self):
        client = MagicMock()
        client.pause = AsyncMock()
        player = make_player(playing(), client)
        await player.async_media_pause()
        client.pause.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop(self):
        client = MagicMock()
        client.stop = AsyncMock()
        player = make_player(playing(), client)
        await player.async_media_stop()
        client.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_next_track(self):
        client = MagicMock()
        client.next_track = AsyncMock()
        player = make_player(playing(), client)
        await player.async_media_next_track()
        client.next_track.assert_called_once()

    @pytest.mark.asyncio
    async def test_previous_track(self):
        client = MagicMock()
        client.previous_track = AsyncMock()
        player = make_player(playing(), client)
        await player.async_media_previous_track()
        client.previous_track.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_volume_converts_to_int(self):
        client = MagicMock()
        client.set_volume = AsyncMock()
        player = make_player(playing(), client)
        await player.async_set_volume_level(0.75)
        client.set_volume.assert_called_once_with(75)

    @pytest.mark.asyncio
    async def test_set_shuffle(self):
        client = MagicMock()
        client.set_shuffle = AsyncMock()
        player = make_player(playing(), client)
        await player.async_set_shuffle(True)
        client.set_shuffle.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_set_repeat_all(self):
        client = MagicMock()
        client.set_repeat = AsyncMock()
        player = make_player(playing(), client)
        await player.async_set_repeat(RepeatMode.ALL)
        client.set_repeat.assert_called_once_with(VainoRepeatMode.ALL)
