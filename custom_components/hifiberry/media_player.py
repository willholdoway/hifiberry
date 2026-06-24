"""HiFiBerry media player platform."""
from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import MediaType
from homeassistant.components.media_player import MediaPlayerEntityFeature
from homeassistant.const import STATE_IDLE, STATE_PAUSED, STATE_PLAYING

from .audiocontrol import AudioControlClient, AudioControlError
from .const import DATA_HIFIBERRY, DOMAIN

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=5)

SUPPORT_VOLUME = (
    MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.VOLUME_STEP
)

CAPABILITY_TO_FEATURE = {
    "play": MediaPlayerEntityFeature.PLAY,
    "pause": MediaPlayerEntityFeature.PAUSE,
    "stop": MediaPlayerEntityFeature.STOP,
    "previous": MediaPlayerEntityFeature.PREVIOUS_TRACK,
    "next": MediaPlayerEntityFeature.NEXT_TRACK,
}

PLAY_PAUSE_FEATURES = (
    MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PAUSE
)

SUPPORT_HIFIBERRY_FALLBACK = (
    MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.PLAY
    | SUPPORT_VOLUME
)

if hasattr(MediaPlayerEntityFeature, "TURN_ON"):
    SUPPORT_HIFIBERRY_FALLBACK |= MediaPlayerEntityFeature.TURN_ON

if hasattr(MediaPlayerEntityFeature, "TURN_OFF"):
    SUPPORT_HIFIBERRY_FALLBACK |= MediaPlayerEntityFeature.TURN_OFF


def _first_value(data: dict[str, Any], *keys: str) -> Any:
    """Return the first non-empty value from a dict."""
    for key in keys:
        value = data.get(key)
        if value not in (None, ""):
            return value
    return None


def _nested_first_value(data: dict[str, Any], *keys: str) -> Any:
    """Return the first non-empty value from now-playing or nested song data."""
    song = data.get("song")
    if isinstance(song, dict):
        value = _first_value(song, *keys)
        if value is not None:
            return value
    return _first_value(data, *keys)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the HiFiBerry media player platform."""

    data = hass.data[DOMAIN][config_entry.entry_id]
    audiocontrol = data[DATA_HIFIBERRY]
    uid = config_entry.entry_id
    name = f"HiFiBerry {config_entry.data['host']}"
    entity = HifiberryMediaPlayer(audiocontrol, uid, name)
    async_add_entities([entity], update_before_add=True)


class HifiberryMediaPlayer(MediaPlayerEntity):
    """HiFiBerry media player object."""

    should_poll = True

    def __init__(self, audiocontrol: AudioControlClient, uid: str, name: str) -> None:
        """Initialize the media player."""
        self._audiocontrol = audiocontrol
        self._attr_unique_id = uid
        self._attr_name = name
        self._muted = False
        self._muted_volume = 50

    @property
    def available(self) -> bool:
        """Return true if device is responding."""
        return self._audiocontrol.connected

    @property
    def device_info(self):
        """Return device info for this device."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "HiFiBerry",
        }

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return MediaType.MUSIC

    @property
    def supported_features(self):
        """Return features supported by the active player."""
        capabilities = self._audiocontrol.active_player_capabilities
        if not capabilities:
            return SUPPORT_HIFIBERRY_FALLBACK

        features = SUPPORT_VOLUME
        for capability, feature in CAPABILITY_TO_FEATURE.items():
            if capability in capabilities:
                features |= feature
        if "play_pause" in capabilities:
            features |= PLAY_PAUSE_FEATURES
        if "play" in capabilities:
            if hasattr(MediaPlayerEntityFeature, "TURN_ON"):
                features |= MediaPlayerEntityFeature.TURN_ON
        if "stop" in capabilities or "pause" in capabilities:
            if hasattr(MediaPlayerEntityFeature, "TURN_OFF"):
                features |= MediaPlayerEntityFeature.TURN_OFF
        return features

    @property
    def state(self):
        """Return the state of the device."""
        status = str(
            _first_value(
                self._audiocontrol.now_playing,
                "state",
                "playerState",
                "player_state",
                "status",
            )
            or ""
        ).lower()
        if status in ("paused", "pause"):
            return STATE_PAUSED
        if status in ("playing", "play"):
            return STATE_PLAYING
        return STATE_IDLE

    @property
    def media_title(self):
        """Title of current playing media."""
        return _nested_first_value(
            self._audiocontrol.now_playing,
            "title",
            "name",
            "song_title",
        )

    @property
    def media_artist(self):
        """Artist of current playing media."""
        return _nested_first_value(
            self._audiocontrol.now_playing,
            "artist",
            "song_artist",
        )

    @property
    def media_album_name(self):
        """Album of current playing media."""
        return _nested_first_value(
            self._audiocontrol.now_playing,
            "album",
            "albumTitle",
            "album_title",
        )

    @property
    def media_album_artist(self):
        """Album artist of current playing media."""
        return _nested_first_value(
            self._audiocontrol.now_playing,
            "albumArtist",
            "album_artist",
        )

    @property
    def media_track(self):
        """Track number of current playing media."""
        return _nested_first_value(
            self._audiocontrol.now_playing,
            "track",
            "tracknumber",
            "track_number",
        )

    @property
    def media_image_url(self):
        """Image URL of current playing media."""
        art_url = _nested_first_value(
            self._audiocontrol.now_playing,
            "artUrl",
            "art_url",
            "artwork",
            "image",
            "image_url",
            "coverart",
            "coverart_url",
            "album_art",
            "album_art_url",
            "cover",
            "cover_url",
        )
        if art_url is None:
            art_url = self._audiocontrol.cover_art_url
        if isinstance(art_url, str) and art_url.startswith("/"):
            base_url = (
                self._audiocontrol.public_base_url
                if art_url.startswith("/api/")
                else self._audiocontrol.base_url
            )
            return f"{base_url}{art_url}"
        if isinstance(art_url, str) and not art_url.startswith(("http://", "https://")):
            if art_url.startswith("artwork/"):
                return f"{self._audiocontrol.base_url}/api/{art_url}"
            return f"{self._audiocontrol.base_url}/{art_url}"
        return art_url

    @property
    def extra_state_attributes(self):
        """Expose raw AudioControl data for troubleshooting metadata/artwork."""
        return {
            "hifiberry_now_playing": self._audiocontrol.now_playing,
            "hifiberry_active_player_name": self._audiocontrol.active_player_name,
            "hifiberry_last_active_player_name": (
                self._audiocontrol.last_active_player_name
            ),
            "hifiberry_active_player_capabilities": sorted(
                self._audiocontrol.active_player_capabilities
            ),
            "hifiberry_cover_art_url": self._audiocontrol.cover_art_url,
            "hifiberry_media_image_url": self.media_image_url,
        }

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        percent = _first_value(
            self._audiocontrol.volume,
            "percentage",
            "percent",
            "volume",
        )
        if percent is None:
            return None
        return float(percent) / 100

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._muted

    @property
    def source(self):
        """Name of the current input source."""
        player = self._audiocontrol.now_playing.get("player")
        if isinstance(player, dict):
            return _first_value(player, "name", "id")
        return _first_value(
            self._audiocontrol.now_playing,
            "player",
            "playerName",
            "player_name",
            "source",
        )

    async def async_update(self):
        """Refresh state from AudioControl."""
        try:
            await self._audiocontrol.async_update()
        except AudioControlError:
            _LOGGER.debug("Unable to update HiFiBerry state", exc_info=True)

    async def async_media_next_track(self):
        """Send media_next command to media player."""
        await self._audiocontrol.async_command("next")

    async def async_media_previous_track(self):
        """Send media_previous command to media player."""
        await self._audiocontrol.async_command("previous")

    async def async_media_play(self):
        """Send media_play command to media player."""
        await self._audiocontrol.async_command("play")

    async def async_media_pause(self):
        """Send media_pause command to media player."""
        await self._audiocontrol.async_command("pause")

    async def async_media_play_pause(self):
        """Toggle play/pause state."""
        try:
            await self._audiocontrol.async_update()
        except AudioControlError:
            _LOGGER.debug("Unable to refresh HiFiBerry state before toggle", exc_info=True)
        if self.state == STATE_PLAYING:
            await self._audiocontrol.async_command("pause")
        else:
            await self._audiocontrol.async_command("play")

    async def async_turn_on(self):
        """Turn the media player on by starting playback."""
        await self._audiocontrol.async_command("play")

    async def async_turn_off(self):
        """Turn the media player off by stopping playback."""
        await self._audiocontrol.async_command("stop")

    async def async_toggle(self):
        """Toggle playback for Home Assistant's media_player.toggle action."""
        await self.async_media_play_pause()

    async def async_media_stop(self):
        """Send media_stop command to media player."""
        await self._audiocontrol.async_command("stop")

    async def async_volume_up(self):
        """Service to send the HiFiBerry the command for volume up."""
        await self._audiocontrol.async_volume_up()

    async def async_volume_down(self):
        """Service to send the HiFiBerry the command for volume down."""
        await self._audiocontrol.async_volume_down()

    async def async_set_volume_level(self, volume):
        """Send volume_set command to media player."""
        await self._audiocontrol.async_set_volume(volume * 100)

    async def async_mute_volume(self, mute):
        """Mute, emulated by setting volume to 0."""
        if mute:
            current_volume = self.volume_level
            if current_volume is not None:
                self._muted_volume = current_volume * 100
            await self._audiocontrol.async_set_volume(0)
        else:
            await self._audiocontrol.async_set_volume(self._muted_volume)
        self._muted = mute
