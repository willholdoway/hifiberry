# Home Assistant Core Submission Notes

This repository is currently structured as a HACS custom integration. The HBOS
NG work is useful preparation for Home Assistant Core, but it should not be
submitted to `home-assistant/core` unchanged.

## What Is Core-Ready Here

- The integration uses config entries and a UI config flow.
- It talks to the local HBOS NG REST API instead of the legacy socket.io API.
- It no longer requires an API token.
- It reports local polling as the integration I/O class.
- It maps controls dynamically from the active HiFiBerry player capabilities.
- It migrates legacy config entries by removing `authtoken` and changing port
  `81` to port `80`.

## Work Needed Before Opening a Core PR

1. Extract `custom_components/hifiberry/audiocontrol.py` into a standalone
   async Python package published on PyPI.
2. Add unit tests for the package, covering:
   - Connection validation.
   - Now-playing and player-list parsing.
   - Cover-art lookup and image selection.
   - Player command URL selection.
   - Volume command URL selection.
   - Error handling when HBOS NG accepts a command but returns an HTTP error.
3. Port this integration into `homeassistant/components/hifiberry/`.
4. Update the Core manifest for Home Assistant conventions:
   - Remove the custom-integration-only `version` field.
   - Set `documentation` to
     `https://www.home-assistant.io/integrations/hifiberry`.
   - Add the PyPI package to `requirements`.
5. Add Home Assistant Core tests for:
   - Config flow success and connection failure.
   - Config entry migration from the legacy socket.io setup.
   - Entity state, metadata, volume, artwork, and supported-feature mapping.
   - Play, pause, play/pause, stop, next, and previous command handling.
6. Open a matching documentation PR in `home-assistant/home-assistant.io`.

## Breaking Change Notes For Core

Compared with the older HiFiBerry OS integration approach:

- The legacy `pyhifiberry` socket.io client is replaced by the HBOS NG REST API.
- Port `81` is no longer used by default; HBOS NG should use port `80`.
- The old API token is ignored and removed during config entry migration.
- The integration is local polling rather than local push.
- Controls are source-specific. For example, AirPlay/Shairport may not expose
  next or previous even when Spotify or MPD does.

