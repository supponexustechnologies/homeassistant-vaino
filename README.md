# Väinö — Home Assistant Integration

[![HACS][hacs-badge]][hacs-url]
[![GitHub Release][release-badge]][release-url]
[![Hassfest][hassfest-badge]][hassfest-url]
[![HACS Validation][hacs-validate-badge]][hacs-validate-url]

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=supponexustechnologies&repository=homeassistant-vaino&category=Integration)
[![Add integration to My Home Assistant](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start?domain=vaino)

A [HACS](https://hacs.xyz)-compatible Home Assistant integration for the **[Väinö](https://supponexus.com/products/vaino)** Raspberry Pi music player.

Expose your Väinö device as a full-featured Home Assistant media player — browse your library, control playback, switch EQ presets, and trigger automations from a single HA entity.

---

## What It Does

| Capability | Detail |
|---|---|
| Media player entity | Play, pause, stop, next, previous, seek, volume, shuffle, repeat |
| Media browser | Browse Artists → Albums → Tracks from within HA |
| Now playing | Current track, artist, album art pushed to HA |
| EQ preset select | Switch presets from HA dashboard or automations |
| Audio output select | Switch between Analog, HDMI, and Bluetooth outputs |
| Library sensors | Track count, artist count, album count |
| Action buttons | Scan library, reboot device |
| Automations | Pause on doorbell, play at sunrise, volume by time-of-day |

---

## Requirements

- Home Assistant 2024.1 or later
- Väinö Pi running MusicMaster Server v1.0 or later
- Both devices on the same local network

No API key or authentication required — the integration connects directly to the MusicMaster API on port 5000.

---

## Installation

### Via HACS (recommended)

1. Open HACS → Integrations → ⋮ → Custom repositories
2. Add `supponexustechnologies/homeassistant-vaino` as type **Integration**
3. Search for **Väinö** and install
4. Restart Home Assistant

> **Note:** Submission to the HACS default store is in progress. Once accepted, Väinö will be searchable directly in HACS without adding a custom repository.

### Manual

Copy `custom_components/vaino/` into your HA `config/custom_components/` directory and restart.

---

## Configuration

1. Settings → Devices & Services → Add Integration → search **Väinö**
2. Enter your Pi's IP address or hostname (e.g. `192.168.1.100` or `vaino-server.local`)
3. Done — entities appear automatically

---

## Entities Created

| Entity | Type | Description |
|---|---|---|
| `media_player.vaino` | Media Player | Full playback control + media browser |
| `sensor.vaino_library_tracks` | Sensor | Total track count in library |
| `sensor.vaino_library_artists` | Sensor | Total artist count |
| `sensor.vaino_library_albums` | Sensor | Total album count |
| `select.vaino_eq_preset` | Select | Active EQ preset |
| `select.vaino_audio_output` | Select | Active audio output |
| `button.vaino_scan_library` | Button | Trigger a library scan |
| `button.vaino_reboot` | Button | Reboot the Pi |

---

## Example Automations

```yaml
# Pause music when the front doorbell rings
automation:
  trigger:
    platform: state
    entity_id: binary_sensor.doorbell
    to: "on"
  action:
    service: media_player.media_pause
    target:
      entity_id: media_player.vaino

# Play music at sunrise
automation:
  trigger:
    platform: sun
    event: sunrise
  action:
    service: media_player.media_play
    target:
      entity_id: media_player.vaino
```

---

## API

The integration communicates with the MusicMaster Server REST API on port 5000. All communication is HTTP on your local network — no cloud dependency, no external calls.

Key endpoints used:

| Endpoint | Purpose |
|---|---|
| `GET /api/playback` | Poll current state (track, position, volume, state) |
| `POST /api/playback/play` `pause` `stop` `next` `previous` | Transport controls |
| `POST /api/playback/volume` | Set volume |
| `POST /api/playback/seek` | Seek to position |
| `POST /api/playback/shuffle` | Toggle shuffle |
| `POST /api/playback/repeat` | Set repeat mode |
| `GET /api/library/artists` `albums` `tracks` | Media browser |
| `GET /api/art/album/{id}` | Album art |
| `GET /api/equalizer/presets` | EQ preset list |
| `POST /api/equalizer/presets/{id}/apply` | Apply EQ preset |
| `GET /api/outputs` | Audio output list |
| `POST /api/outputs/enable/{id}` | Switch audio output |
| `GET /api/library/stats` | Library counts |
| `POST /api/library/scan` | Trigger library scan |
| `POST /api/system/reboot` | Reboot device |

---

## Implementation Plan

### Phase 1 — Foundation ✅
- [x] Project structure and documentation
- [x] `api.py` — async HTTP client wrapping MusicMaster API
- [x] `config_flow.py` — UI setup: enter host, test connection, save entry
- [x] `__init__.py` — integration entry point, coordinator setup
- [x] `const.py` — constants (domain, default port, polling interval)
- [x] `manifest.json` and `hacs.json`

### Phase 2 — Core Entity ✅
- [x] `media_player.py` — full `MediaPlayerEntity` implementation
  - State: playing / paused / idle / off
  - Transport: play, pause, stop, next, previous
  - Volume: get and set
  - Seek: get position, set position
  - Shuffle and repeat modes
  - Now playing: title, artist, album, duration
  - Album art via `GET /api/art/album/{id}`
  - Polling via `DataUpdateCoordinator` (5-second interval)

### Phase 3 — Media Browser ✅
- [x] `async_browse_media()` on the media player
  - Root: Artists / Albums
  - Artists → Albums → Tracks
  - Thumbnails from `/api/art/artist/{id}` and `/api/art/album/{id}`
  - Play from browser: queue track/album/artist

### Phase 4 — Supporting Entities ✅
- [x] `select.py` — EQ preset selector, audio output selector
- [x] `sensor.py` — library track / artist / album counts
- [x] `button.py` — scan library, reboot

### Phase 5 — Polish and HACS Submission ✅
- [x] `strings.json` and `translations/en.json` — UI text
- [x] Icons and brand assets (icon 512x512, logo)
- [x] `tests/` — 59 unit tests across API client, config flow, media player, and init
- [x] Published to `supponexustechnologies/homeassistant-vaino` GitHub repo
- [ ] Submit to [HACS default repository](https://github.com/hacs/default) — in progress

---

## Project Structure

```
HAOS_Integration/
├── README.md                        ← this file
├── hacs.json                        ← HACS metadata
├── custom_components/
│   └── vaino/
│       ├── __init__.py              ← integration setup + DataUpdateCoordinator
│       ├── manifest.json            ← HA integration manifest
│       ├── const.py                 ← constants
│       ├── api.py                   ← async MusicMaster API client
│       ├── config_flow.py           ← UI configuration flow
│       ├── media_player.py          ← media_player entity
│       ├── sensor.py                ← sensor entities
│       ├── select.py                ← select entities
│       ├── button.py                ← button entities
│       ├── strings.json             ← UI strings
│       └── translations/
│           └── en.json
└── tests/
    ├── conftest.py
    └── test_api.py
```

---

## Development Setup

To test locally against your Väinö Pi:

```bash
# Install HA development dependencies
pip install homeassistant aiohttp

# Copy custom_components/vaino into your HA config directory
cp -r custom_components/vaino /path/to/ha/config/custom_components/

# Restart HA and add the integration via UI
```

---

## Contributing

This integration is maintained by [SuppoNexus Technologies](https://supponexus.com).
Issues and pull requests welcome.

[hacs-badge]: https://img.shields.io/badge/HACS-Custom-orange.svg
[hacs-url]: https://github.com/hacs/integration
[release-badge]: https://img.shields.io/github/v/release/supponexustechnologies/homeassistant-vaino
[release-url]: https://github.com/supponexustechnologies/homeassistant-vaino/releases
[hassfest-badge]: https://img.shields.io/github/actions/workflow/status/supponexustechnologies/homeassistant-vaino/hassfest.yaml?label=Hassfest&logo=homeassistant
[hassfest-url]: https://github.com/supponexustechnologies/homeassistant-vaino/actions/workflows/hassfest.yaml
[hacs-validate-badge]: https://img.shields.io/github/actions/workflow/status/supponexustechnologies/homeassistant-vaino/validate.yaml?label=HACS%20Validation&logo=homeassistant
[hacs-validate-url]: https://github.com/supponexustechnologies/homeassistant-vaino/actions/workflows/validate.yaml
