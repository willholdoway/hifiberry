"""Hifiberry Platform."""
import logging
from datetime import timedelta

from homeassistant.components.media_player import MediaPlayerEntity
from homeassistant.components.media_player.const import MediaType
from homeassistant.components.media_player import MediaPlayerEntityFeature

from homeassistant.const import (
    STATE_IDLE,
    STATE_PAUSED,
    STATE_PLAYING,
)
from pyhifiberry.audiocontrol2 import Audiocontrol2Exception, LOGGER
from pyhifiberry.audiocontrol2sio import Audiocontrol2SIO
from .const import DATA_HIFIBERRY, DATA_INIT, DOMAIN

from homeassistant.components.media_player import MediaPlayerEntityFeature
SUPPORT_HIFIBERRY = (
    MediaPlayerEntityFeature.PAUSE |
    MediaPlayerEntityFeature.VOLUME_SET |
    MediaPlayerEntityFeature.VOLUME_MUTE |
    MediaPlayerEntityFeature.PREVIOUS_TRACK |
    MediaPlayerEntityFeature.NEXT_TRACK |
    MediaPlayerEntityFeature.STOP |
    MediaPlayerEntityFeature.PLAY |
    MediaPlayerEntityFeature.VOLUME_STEP |
    MediaPlayerEntityFeature.TURN_OFF
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the hifiberry media player platform."""

    data = hass.data[DOMAIN][config_entry.entry_id]
    audiocontrol2 = data[DATA_HIFIBERRY]
    uid = config_entry.entry_id
    name = f"hifiberry {config_entry.data['host']}"
    base_url = f"http://{config_entry.data['host']}:{config_entry.data['port']}"
    entity = HifiberryMediaPlayer(audiocontrol2, uid, name, base_url)
    async_add_entities([entity])


class HifiberryMediaPlayer(MediaPlayerEntity):
    """Hifiberry Media Player Object."""

    should_poll = False

    def __init__(self, audiocontrol2: Audiocontrol2SIO, uid, name, base_url):
        """Initialize the media player."""
        self._audiocontrol2 = audiocontrol2
        self._uid = uid
        self._name = name
        self._base_url = base_url
        self._muted = audiocontrol2.volume.percent == 0
        self._muted_volume = audiocontrol2.volume.percent

    @property
    def available(self) -> bool:
        """Return true if device is responding."""
        return self._audiocontrol2.connected

    @property
    def unique_id(self):
        """Return the unique id for the entity."""
        return self._uid

    @property
    def device_info(self):
        """Return device info for this device."""
        return {
            "identifiers": {(DOMAIN, self.unique_id)},
            "name": self.name,
            "manufacturer": "Hifiberry",
        }

    async def async_added_to_hass(self) -> None:
        """Run when this Entity has been added to HA."""
        await self._audiocontrol2.volume.get()      ### make sure volume percent is set
        self._audiocontrol2.metadata.add_callback(self.schedule_update_ha_state)
        self._audiocontrol2.volume.add_callback(self.schedule_update_ha_state)

    async def async_will_remove_from_hass(self) -> None:
        """Entity being removed from hass."""
        await self._audiocontrol2.disconnect()

    @property
    def media_content_type(self):
        """Content type of current playing media."""
        return MediaType.MUSIC

    @property
    def state(self):
        """Return the state of the device."""
        status = self._audiocontrol2.metadata.playerState
        if status == "paused":
            return STATE_PAUSED
        if status == "playing":
            return STATE_PLAYING
        return STATE_IDLE

    @property
    def media_position_updated_at(self):
        """When was the position of the current playing media valid.

        Returns value from homeassistant.util.dt.utcnow().
        """
        return self._audiocontrol2.metadata.positionupdate
        
    @property
    def media_title(self):
        """Title of current playing media."""
        return self._audiocontrol2.metadata.title

    @property
    def media_artist(self):
        """Artist of current playing media (Music track only)."""
        return self._audiocontrol2.metadata.artist

    @property
    def media_album_name(self):
        """Artist of current playing media (Music track only)."""
        return self._audiocontrol2.metadata.albumTitle

    @property
    def media_album_artist(self):
        """Album artist of current playing media, music track only."""
        return self._audiocontrol2.metadata.albumArtist

    @property
    def media_track(self):
        """Track number of current playing media, music track only."""
        return self._audiocontrol2.metadata.tracknumber

    @property
    def media_image_url(self):
        """Image url of current playing media."""
        art_url = self._audiocontrol2.metadata.artUrl
        external_art_url = self._audiocontrol2.metadata.externalArtUrl
        if art_url is not None:
            if art_url.startswith("static/"):
                return external_art_url
            if art_url.startswith("artwork/"):
                return f"{self._base_url}/{art_url}"
            return art_url
        return external_art_url

    @property
    def volume_level(self):
        """Volume level of the media player (0..1)."""
        return int(self._audiocontrol2.volume.percent) / 100

    @property
    def is_volume_muted(self):
        """Boolean if volume is currently muted."""
        return self._muted

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def source(self):
        """Name of the current input source."""
        return self._audiocontrol2.metadata.playerName

    @property
    def supported_features(self):
        """Flag of media commands that are supported."""
        return SUPPORT_HIFIBERRY

    async def async_media_next_track(self):
        """Send media_next command to media player."""
        await self._audiocontrol2.player.next()

    async def async_media_previous_track(self):
        """Send media_previous command to media player."""
        await self._audiocontrol2.player.previous()

    async def async_media_play(self):
        """Send media_play command to media player."""
        await self._audiocontrol2.player.play()

    async def async_media_pause(self):
        """Send media_pause command to media player."""
        await self._audiocontrol2.player.pause()

    async def async_volume_up(self):
        """Service to send the hifiberry the command for volume up."""
        await self._audiocontrol2.volume.set(min(100, self._audiocontrol2.volume.percent + 5))

    async def async_volume_down(self):
        """Service to send the hifiberry the command for volume down."""
        await self._audiocontrol2.volume.set(max(0, self._audiocontrol2.volume.percent - 5))

    async def async_set_volume_level(self, volume):
        """Send volume_set command to media player."""
        if volume < 0:
            volume = 0
        elif volume > 1:
            volume = 1
        await self._audiocontrol2.volume.set(int(volume * 100))
        self._volume = volume * 100

    async def async_mute_volume(self, mute):
        """Mute. Emulated with set_volume_level."""
        if mute:
            self._muted_volume = self.volume_level * 100
            await self._audiocontrol2.volume.set(0)
        await self._audiocontrol2.volume.set(int(self._muted_volume))
        self._muted = mute

    async def async_turn_off(self):
        return await self._audiocontrol2.poweroff()
