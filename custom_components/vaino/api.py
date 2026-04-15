"""Async HTTP client for the Väinö MusicMaster Server API."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

import aiohttp


# ── Exceptions ────────────────────────────────────────────────────────────────

class VainoApiError(Exception):
    """Raised when the API returns an unexpected error."""


class CannotConnect(VainoApiError):
    """Raised when the connection to the Väinö server fails."""


# ── Enums (mirror MusicMaster.Shared) ─────────────────────────────────────────

class PlaybackState(str, Enum):
    STOPPED = "Stopped"
    PLAYING = "Playing"
    PAUSED  = "Paused"


class RepeatMode(str, Enum):
    OFF    = "Off"
    SINGLE = "Single"
    ALL    = "All"


class AudioOutputType(str, Enum):
    HDMI      = "Hdmi"
    ANALOG    = "Analog"
    USB_DAC   = "UsbDac"
    AUDIO_HAT = "AudioHat"
    BLUETOOTH = "Bluetooth"


# ── Data classes ──────────────────────────────────────────────────────────────

@dataclass
class TrackInfo:
    id: int
    title: str
    artist: str
    album: str
    duration: float
    track_number: int
    disc_number: int
    genre: str | None = None
    file_path: str = ""
    album_art_url: str | None = None
    play_count: int = 0


@dataclass
class PlaybackStatus:
    state: PlaybackState
    volume: int
    repeat: RepeatMode
    shuffle: bool
    position: float = 0.0
    duration: float = 0.0
    audio_output: str | None = None
    song_id: int | None = None
    is_indexing: bool = False
    current_track: TrackInfo | None = None


@dataclass
class AudioOutput:
    id: int
    name: str
    type: AudioOutputType
    is_enabled: bool


@dataclass
class LibraryStats:
    artists: int
    albums: int
    songs: int


@dataclass
class EqPreset:
    id: int
    name: str
    bands: list[float]
    is_room_tuned: bool = False


@dataclass
class SystemStatus:
    version: str
    mpd_connected: bool
    database_track_count: int
    uptime: str


# ── API client ────────────────────────────────────────────────────────────────

class VainoApiClient:
    """Async HTTP client for the Väinö MusicMaster Server API."""

    def __init__(
        self,
        host: str,
        port: int = 5000,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._base = f"http://{host}:{port}"
        self._session = session
        self._owns_session = session is None

    async def __aenter__(self) -> VainoApiClient:
        if self._owns_session:
            self._session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._owns_session and self._session:
            await self._session.close()

    # ── Internal helpers ──────────────────────────────────────────────────────

    async def _get(self, path: str) -> Any:
        try:
            async with self._session.get(
                f"{self._base}{path}",
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientConnectorError as err:
            raise CannotConnect(f"Cannot connect to Väinö at {self._base}") from err
        except aiohttp.ClientError as err:
            raise VainoApiError(str(err)) from err

    async def _post(self, path: str, json: Any = None) -> Any:
        try:
            async with self._session.post(
                f"{self._base}{path}",
                json=json,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                resp.raise_for_status()
                if resp.content_type == "application/json":
                    return await resp.json()
        except aiohttp.ClientConnectorError as err:
            raise CannotConnect(f"Cannot connect to Väinö at {self._base}") from err
        except aiohttp.ClientError as err:
            raise VainoApiError(str(err)) from err

    # ── Connection test ───────────────────────────────────────────────────────

    async def test_connection(self) -> SystemStatus:
        """Verify connectivity and return system status. Raises CannotConnect on failure."""
        data = await self._get("/api/system/status")
        return self._parse_system_status(data)

    # ── Playback ──────────────────────────────────────────────────────────────

    async def get_playback(self) -> PlaybackStatus:
        return self._parse_playback(await self._get("/api/playback"))

    async def play(self) -> None:
        await self._post("/api/playback/play")

    async def pause(self) -> None:
        await self._post("/api/playback/pause")

    async def stop(self) -> None:
        await self._post("/api/playback/stop")

    async def next_track(self) -> None:
        await self._post("/api/playback/next")

    async def previous_track(self) -> None:
        await self._post("/api/playback/previous")

    async def set_volume(self, level: int) -> None:
        await self._post("/api/playback/volume", {"level": level})

    async def seek(self, position: float) -> None:
        await self._post("/api/playback/seek", {"position": position})

    async def set_shuffle(self, enabled: bool) -> None:
        await self._post("/api/playback/shuffle", {"enabled": enabled})

    async def set_repeat(self, mode: RepeatMode) -> None:
        await self._post("/api/playback/repeat", {"mode": mode.value})

    # ── Audio outputs ─────────────────────────────────────────────────────────

    async def get_outputs(self) -> list[AudioOutput]:
        return [self._parse_output(o) for o in await self._get("/api/outputs")]

    async def enable_output(self, output_id: int) -> None:
        await self._post(f"/api/outputs/enable/{output_id}")

    async def disable_output(self, output_id: int) -> None:
        await self._post(f"/api/outputs/disable/{output_id}")

    # ── Library ───────────────────────────────────────────────────────────────

    async def get_library_stats(self) -> LibraryStats:
        data = await self._get("/api/library/stats")
        return LibraryStats(
            artists=data["artists"],
            albums=data["albums"],
            songs=data["songs"],
        )

    async def get_artists(self) -> list[dict]:
        return await self._get("/api/library/artists")

    async def get_albums(self, artist_id: int | None = None) -> list[dict]:
        path = "/api/library/albums"
        if artist_id is not None:
            path += f"?artistId={artist_id}"
        return await self._get(path)

    async def get_tracks(
        self,
        album_id: int | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> list[dict]:
        params = f"?page={page}&pageSize={page_size}"
        if album_id is not None:
            params += f"&albumId={album_id}"
        return await self._get(f"/api/library/tracks{params}")

    async def scan_library(self) -> None:
        await self._post("/api/library/scan")

    # ── Queue / play ──────────────────────────────────────────────────────────

    async def play_from_queue(self, position: int) -> None:
        await self._post("/api/queue/play", {"position": position})

    async def play_artist(self, artist_id: int, shuffle: bool = False) -> None:
        await self._post("/api/queue/play-artist", {"artistId": artist_id, "shuffle": shuffle})

    async def play_album(self, album_id: int, shuffle: bool = False) -> None:
        """Clear queue, enqueue all tracks from an album, and play."""
        await self._post("/api/queue/clear")
        tracks = await self.get_tracks(album_id=album_id, page_size=500)
        for track in tracks:
            await self._post("/api/queue/add", {"uri": track["filePath"]})
        if tracks:
            await self.play_from_queue(0)

    # ── EQ presets ────────────────────────────────────────────────────────────

    async def get_eq_presets(self) -> list[EqPreset]:
        return [self._parse_eq_preset(p) for p in await self._get("/api/equalizer/presets")]

    async def apply_eq_preset(self, preset_id: int) -> None:
        await self._post(f"/api/equalizer/presets/{preset_id}/apply")

    # ── System ────────────────────────────────────────────────────────────────

    async def get_system_status(self) -> SystemStatus:
        return self._parse_system_status(await self._get("/api/system/status"))

    async def reboot(self) -> None:
        await self._post("/api/system/reboot")

    # ── Art URLs (returned as proxy-friendly absolute URLs) ───────────────────

    def album_art_url(self, album_id: int) -> str:
        return f"{self._base}/api/art/album/{album_id}"

    def artist_art_url(self, artist_id: int) -> str:
        return f"{self._base}/api/art/artist/{artist_id}"

    # ── Parsers ───────────────────────────────────────────────────────────────

    def _parse_playback(self, data: dict) -> PlaybackStatus:
        track: TrackInfo | None = None
        if data.get("currentTrack"):
            t = data["currentTrack"]
            track = TrackInfo(
                id=t["id"],
                title=t["title"],
                artist=t["artist"],
                album=t["album"],
                duration=t["duration"],
                track_number=t.get("trackNumber", 0),
                disc_number=t.get("discNumber", 0),
                genre=t.get("genre"),
                file_path=t.get("filePath", ""),
                album_art_url=t.get("albumArtUrl"),
                play_count=t.get("playCount", 0),
            )
        return PlaybackStatus(
            state=PlaybackState(data["state"]),
            volume=data["volume"],
            repeat=RepeatMode(data["repeat"]),
            shuffle=data["shuffle"],
            position=data.get("position", 0.0),
            duration=data.get("duration", 0.0),
            audio_output=data.get("audioOutput"),
            song_id=data.get("songId"),
            is_indexing=data.get("isIndexing", False),
            current_track=track,
        )

    def _parse_output(self, data: dict) -> AudioOutput:
        return AudioOutput(
            id=data["id"],
            name=data["name"],
            type=AudioOutputType(data["type"]),
            is_enabled=data["isEnabled"],
        )

    def _parse_eq_preset(self, data: dict) -> EqPreset:
        return EqPreset(
            id=data["id"],
            name=data["name"],
            bands=data["bands"],
            is_room_tuned=data.get("isRoomTuned", False),
        )

    def _parse_system_status(self, data: dict) -> SystemStatus:
        return SystemStatus(
            version=data["version"],
            mpd_connected=data["mpdConnected"],
            database_track_count=data["databaseTrackCount"],
            uptime=str(data.get("uptime", "")),
        )
