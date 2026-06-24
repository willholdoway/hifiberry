## HiFiBerry for Home Assistant

![beta_badge](https://img.shields.io/badge/maturity-Beta-yellow.png)
[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs)
[![License: CC0-1.0](https://img.shields.io/badge/License-CC0%201.0-lightgrey.svg)](http://creativecommons.org/publicdomain/zero/1.0/)

The HiFiBerry integration exposes a HiFiBerry OS player as a Home Assistant
`media_player` entity.

This version targets current HiFiBerry OS / HBOS NG builds that expose the
AudioControl REST API through the web UI reverse proxy:

```text
http://<device>/api/audiocontrol/
```

It no longer depends on the older `pyhifiberry` socket.io client.

## Supported Features

- Playback state, source, title, artist, album, and volume polling.
- Play, pause, stop, and play/pause actions.
- Dynamic control capabilities based on the active HiFiBerry player.
- Spotify Connect, AirPlay/Shairport, MPD, Bluetooth, LMS, RAAT, and other
  players as reported by HiFiBerry OS.
- Album artwork lookup through the same cover-art API used by the HBOS NG web
  UI.

Capabilities are source-specific. For example, AirPlay/Shairport usually reports
play, pause, and stop, but not next/previous. Spotify and MPD may expose a wider
set of controls.

## Installation

Install using [Home Assistant Community Store (HACS)](https://hacs.xyz/) where
available.

For manual installation, copy this folder:

```text
custom_components/hifiberry/
```

to:

```text
<config directory>/custom_components/hifiberry/
```

Then fully restart Home Assistant.

## Configuration

1. Open Home Assistant.
2. Go to **Settings** > **Devices & services**.
3. Click **Add Integration**.
4. Search for **HiFiBerry**.
5. Enter the HiFiBerry host or IP address.
6. Use port `80` for HBOS NG unless you have a custom reverse proxy.

The old socket.io API token is no longer required.

## Migration Notes

This release moves the integration from the legacy HiFiBerry OS
`audiocontrol2` socket.io API to the HBOS NG REST API.

### Breaking Changes

- The `pyhifiberry` dependency has been removed.
- The old socket.io API on port `81` is no longer used.
- The `authtoken` setup field has been removed for new config entries.
- The integration is now local polling rather than local push.
- Existing config entries may need their port changed to `80`.
- Player controls are now source-specific. Buttons such as next/previous are
  only exposed when the currently active HiFiBerry player reports support for
  them.

Existing entries are migrated automatically where possible. Legacy entries have
their old `authtoken` value removed, and entries using the old socket.io port
`81` are moved to port `80`.

### HBOS NG API Details

The integration uses:

```text
GET  /api/audiocontrol/now-playing
GET  /api/audiocontrol/players
POST /api/audiocontrol/player/<player_name>/command/<command>
POST /api/audiocontrol/players/pause-all
POST /api/audiocontrol/players/stop-all
GET  /api/audiocontrol/coverart/...
```

Some HiFiBerry builds expose the backend on port `1080`, but the public and
documented web UI route is usually port `80` with the `/api/audiocontrol/`
prefix. The integration prefers the public route and keeps compatibility probes
for older path shapes where practical.

## Album Artwork

HBOS NG does not always include artwork URLs in `now-playing`. The web UI performs
a separate cover-art lookup using the current title, artist, and album. This
integration mirrors that behavior and cleans common AirPlay metadata suffixes
such as ` • Video Available` before querying cover-art providers.

## Troubleshooting

If the integration loads but controls are missing, inspect the entity attributes:

```text
hifiberry_active_player_name
hifiberry_active_player_capabilities
hifiberry_last_active_player_name
hifiberry_cover_art_url
hifiberry_now_playing
```

These show the active source, what commands HiFiBerry reports as supported, and
the raw metadata returned by HBOS NG.

If Home Assistant still appears to run an older version after updating, remove:

```text
<config directory>/custom_components/hifiberry/__pycache__/
```

and fully restart Home Assistant.

## Support

This is community-supported and is not an official HiFiBerry or Home Assistant
integration.

Discussion and support:

- [Home Assistant HiFiBerry discussion thread](https://community.home-assistant.io/t/hifiberry-os-media-player-integration/163567)

Related projects:

- [HiFiBerry OS](https://www.hifiberry.com/hifiberryos/)
- [HBOS NG backend API docs](https://github.com/hifiberry/hifiberry-os/blob/hbosng/docs/backend-apis.md)

## Home Assistant Core

This repository is packaged as a HACS custom integration. Before submitting the
integration to Home Assistant Core, the AudioControl API client should be
extracted into a tested PyPI package and the integration should be ported into
`homeassistant/components/hifiberry/`.

See [CORE_SUBMISSION.md](CORE_SUBMISSION.md) for the current Core-readiness
checklist.
