"""Client for the HiFiBerry AudioControl REST API."""
from __future__ import annotations

import asyncio
import base64
from typing import Any
from urllib.parse import quote

from aiohttp import ClientError, ClientResponseError, ClientSession


class AudioControlError(Exception):
    """Raised when the AudioControl API cannot be reached."""


class AudioControlClient:
    """Small wrapper around the AudioControl REST API."""

    def __init__(self, session: ClientSession, host: str, port: int) -> None:
        """Initialize the client."""
        self._session = session
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}"
        self.public_base_url = f"http://{host}"
        self.connected = False
        self.now_playing: dict[str, Any] = {}
        self.players: list[dict[str, Any]] = []
        self.volume: dict[str, Any] = {}
        self.cover_art_url: str | None = None
        self._cover_art_song_key: tuple[Any, Any, Any] | None = None
        self._last_active_player_name: str | None = None

    async def _request(
        self,
        method: str,
        path: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Send a request to AudioControl."""
        urls = [f"{self.base_url}{path}"]
        if (
            self.port != 80
            and path.startswith(("/api/audiocontrol/", "/api/pipewire/"))
        ):
            urls.append(f"{self.public_base_url}{path}")
        last_error: Exception | None = None
        try:
            for url in urls:
                try:
                    async with asyncio.timeout(10):
                        response = await self._session.request(method, url, **kwargs)
                        response.raise_for_status()
                        if response.content_type == "application/json":
                            return await response.json()
                        return {}
                except (TimeoutError, ClientError, ClientResponseError) as err:
                    last_error = err
            raise AudioControlError(f"Unable to call {urls[-1]}") from last_error
        except (TimeoutError, ClientError, ClientResponseError) as err:
            self.connected = False
            raise AudioControlError(f"Unable to call {urls[-1]}") from err

    async def _request_first(
        self,
        method: str,
        paths: tuple[str, ...],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Try multiple API paths for compatibility across HiFiBerry OS builds."""
        last_error: AudioControlError | None = None
        for path in paths:
            try:
                return await self._request(method, path, **kwargs)
            except AudioControlError as err:
                last_error = err
        if last_error is not None:
            raise last_error
        raise AudioControlError("No AudioControl API paths configured")

    async def async_validate(self) -> None:
        """Check that AudioControl is reachable."""
        await self._request_first(
            "GET",
            (
                "/api/version",
                "/api/audiocontrol/version",
                "/api/now-playing",
                "/api/audiocontrol/now-playing",
            ),
        )
        self.connected = True

    async def async_update(self) -> None:
        """Refresh cached player and volume data."""
        self.now_playing = await self._request_first(
            "GET",
            (
                "/api/now-playing",
                "/api/audiocontrol/now-playing",
            ),
        )
        try:
            players_response = await self._request_first(
                "GET",
                (
                    "/api/players",
                    "/api/audiocontrol/players",
                ),
            )
            players = players_response.get("players")
            self.players = players if isinstance(players, list) else []
        except AudioControlError:
            self.players = []
        try:
            self.volume = await self._request_first(
                "GET",
                (
                    "/api/volume/state",
                    "/api/pipewire/v1/volume",
                ),
            )
        except AudioControlError:
            self.volume = {}
        await self.async_update_cover_art()
        active_player_name = self._active_player_name()
        now_playing_state = str(self.now_playing.get("state") or "").lower()
        if active_player_name and now_playing_state in ("playing", "paused", "pause"):
            self._last_active_player_name = active_player_name
        self.connected = True

    def _song(self) -> dict[str, Any]:
        """Return the current song payload."""
        song = self.now_playing.get("song")
        return song if isinstance(song, dict) else self.now_playing

    @staticmethod
    def _clean_artist(artist: Any) -> str | None:
        """Clean AirPlay suffixes that break cover-art provider searches."""
        if not isinstance(artist, str):
            return None
        artist = artist.split(" \u2022 ")[0].strip()
        return artist or None

    @staticmethod
    def _base64_urlsafe(value: str) -> str:
        """Encode strings the way the HiFiBerry Web UI cover-art loader does."""
        encoded = base64.b64encode(value.encode()).decode()
        return encoded.replace("+", "-").replace("/", "_").rstrip("=")

    @staticmethod
    def _best_cover_art_url(response: dict[str, Any]) -> str | None:
        """Return the highest-grade cover-art URL from an API response."""
        best_image: dict[str, Any] | None = None
        for result in response.get("results") or []:
            for image in result.get("images") or []:
                if not isinstance(image, dict) or not image.get("url"):
                    continue
                if best_image is None:
                    best_image = image
                    continue
                image_grade = image.get("grade") or 0
                best_grade = best_image.get("grade") or 0
                image_pixels = (image.get("width") or 0) * (image.get("height") or 0)
                best_pixels = (best_image.get("width") or 0) * (best_image.get("height") or 0)
                if (image_grade, image_pixels) > (best_grade, best_pixels):
                    best_image = image
        return best_image.get("url") if best_image else None

    async def async_update_cover_art(self) -> None:
        """Refresh cached cover art using the same API as the HiFiBerry Web UI."""
        song = self._song()
        title = song.get("title")
        album = song.get("album")
        artist = self._clean_artist(song.get("artist"))
        song_key = (title, album, artist)

        if song_key == self._cover_art_song_key:
            return

        self.cover_art_url = None
        self._cover_art_song_key = song_key
        if not artist:
            return

        lookups: list[tuple[str, ...]] = []
        if isinstance(title, str) and title:
            lookups.append(("song", title, artist))
        if isinstance(album, str) and album:
            lookups.append(("album", album, artist))
        lookups.append(("artist", artist))

        for lookup in lookups:
            path = "/".join(self._base64_urlsafe(part) for part in lookup[1:])
            try:
                response = await self._request_first(
                    "GET",
                    (f"/api/audiocontrol/coverart/{lookup[0]}/{path}",),
                )
            except AudioControlError:
                continue
            cover_art_url = self._best_cover_art_url(response)
            if cover_art_url:
                self.cover_art_url = cover_art_url
                return

    def _active_player_name(self, command: str | None = None) -> str | None:
        """Return the best active player name for a command."""
        player = self.now_playing.get("player")
        if isinstance(player, dict):
            player_name = player.get("name")
            capabilities = player.get("capabilities") or []
            player_state = str(player.get("state") or self.now_playing.get("state") or "").lower()
            if (
                player_name
                and player_state not in ("stopped", "unknown", "disconnected")
                and (command is None or command in capabilities)
            ):
                return str(player_name)

        active_players = [
            player
            for player in self.players
            if player.get("is_active")
            and str(player.get("state") or "").lower() not in ("unknown", "disconnected")
        ]
        if command is not None:
            for player in active_players:
                if command in (player.get("capabilities") or []) and player.get("name"):
                    return str(player["name"])

        for player in active_players:
            if player.get("name"):
                return str(player["name"])

        return None

    @property
    def active_player_name(self) -> str | None:
        """Return the current active player name."""
        return self._active_player_name()

    @property
    def last_active_player_name(self) -> str | None:
        """Return the last active player name used for resume."""
        return self._last_active_player_name

    @property
    def active_player_capabilities(self) -> set[str]:
        """Return capabilities reported by the active player."""
        player = self.now_playing.get("player")
        if isinstance(player, dict):
            capabilities = player.get("capabilities")
            if isinstance(capabilities, list):
                return {str(capability) for capability in capabilities}

        player_name = self.active_player_name
        for player in self.players:
            if player.get("name") != player_name:
                continue
            capabilities = player.get("capabilities")
            if isinstance(capabilities, list):
                return {str(capability) for capability in capabilities}

        return set()

    async def async_command(self, command: str) -> None:
        """Send a playback command to the active player."""
        if not self.now_playing:
            await self.async_update()

        if command == "play" and self._last_active_player_name:
            player_name = self._last_active_player_name
        else:
            player_name = self._active_player_name(command)
        paths = []
        if command == "pause":
            paths.append("/api/audiocontrol/players/pause-all")
        elif command == "stop":
            paths.append("/api/audiocontrol/players/stop-all")
        if player_name:
            quoted_player_name = quote(player_name, safe="")
            paths.append(f"/api/audiocontrol/player/{quoted_player_name}/command/{command}")
        elif command not in ("pause", "stop"):
            raise AudioControlError(f"Active player does not support {command}")
        try:
            await self._request_first("POST", tuple(paths))
        except AudioControlError:
            if not await self._async_command_took_effect(command):
                raise
        self.connected = True

    def _command_state_matches(self, command: str) -> bool:
        """Return true if the current state already reflects a command."""
        state = str(self.now_playing.get("state") or "").lower()
        if command == "play":
            return state == "playing"
        if command == "pause":
            return state in ("paused", "pause", "stopped", "stop")
        if command == "stop":
            return state in ("stopped", "stop")
        return False

    async def _async_command_took_effect(self, command: str) -> bool:
        """Refresh state a few times to detect commands that worked despite errors."""
        for _ in range(3):
            await asyncio.sleep(0.5)
            try:
                await self.async_update()
            except AudioControlError:
                continue
            if self._command_state_matches(command):
                return True
        return False

    async def async_set_volume(self, percentage: float) -> None:
        """Set the hardware volume percentage."""
        response = await self._request_first(
            "POST",
            (
                "/api/volume/set",
                "/api/pipewire/v1/volume",
            ),
            json={"percentage": max(0.0, min(100.0, percentage))},
        )
        self.volume = response.get("new_state") or self.volume
        self.connected = True

    async def async_volume_up(self) -> None:
        """Increase volume by the API default amount."""
        response = await self._request("POST", "/api/volume/increase")
        self.volume = response.get("new_state") or self.volume
        self.connected = True

    async def async_volume_down(self) -> None:
        """Decrease volume by the API default amount."""
        response = await self._request("POST", "/api/volume/decrease")
        self.volume = response.get("new_state") or self.volume
        self.connected = True
