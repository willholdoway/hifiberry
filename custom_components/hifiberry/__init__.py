"""The hifiberry integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .audiocontrol import AudioControlClient
from .const import DATA_HIFIBERRY, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["media_player"]


async def async_migrate_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Migrate legacy HiFiBerry OS config entries to HBOS NG settings."""
    if entry.version >= 2:
        return True

    data = dict(entry.data)
    data.pop("authtoken", None)
    if data.get("port") in (None, 81):
        data["port"] = 80

    hass.config_entries.async_update_entry(entry, data=data, version=2)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up hifiberry from a config entry."""
    host = entry.data["host"]
    port = entry.data["port"]
    api = AudioControlClient(async_get_clientsession(hass), host, port)
    try:
        await api.async_update()
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
