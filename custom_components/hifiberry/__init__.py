"""The hifiberry integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from pyhifiberry.audiocontrol2sio import Audiocontrol2SIO

from .const import DATA_HIFIBERRY, DATA_INIT, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["media_player"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up hifiberry from a config entry."""
    try:
        host=entry.data["host"]
        port=entry.data["port"]
        api = await Audiocontrol2SIO.connect(host, port)
    except Exception as error:
        raise ConfigEntryNotReady from error

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_HIFIBERRY: api,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
