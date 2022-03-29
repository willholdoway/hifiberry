"""Config flow for hifiberry integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.typing import DiscoveryInfoType
from pyhifiberry.audiocontrol2sio import Audiocontrol2SIO
from socketio.exceptions import ConnectionError

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""
    
    await Audiocontrol2SIO.connect(host=data["host"], port=data["port"])


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for hifiberry."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize with default hostname."""
        self.host = "hifiberry.local"

    @property
    def schema(self):
        """Return current schema."""
        return vol.Schema(
            {
                vol.Required("host", default=self.host): str,
                vol.Optional("port", default=81): int,
                vol.Optional("authtoken", default=""): str,
            }
        )

    async def async_step_zeroconf(self, discovery_info: DiscoveryInfoType) -> data_entry_flow.FlowResult:
        """Zeroconf detects hifiberry, but we don't have enough informatio to create entry."""
        await self.async_set_unique_id(discovery_info.host)
        self._abort_if_unique_id_configured()

        self.host = discovery_info.host
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=self.schema
            )

        errors = {}

        await self.async_set_unique_id(user_input['host'])  # This should be future "rpi serial" from https://github.com/hifiberry/audiocontrol2/pull/17
        self._abort_if_unique_id_configured()

        try:
            await validate_input(self.hass, user_input)
        except ConnectionError:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=user_input["host"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=self.schema, errors=errors
        )
