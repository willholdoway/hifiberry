"""Config flow for hifiberry integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import DiscoveryInfoType

from .audiocontrol import AudioControlClient, AudioControlError
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> dict[str, Any]:
    """Validate the user input allows us to connect."""

    client = AudioControlClient(
        async_get_clientsession(hass),
        data["host"],
        data["port"],
    )
    await client.async_validate()
    return {"title": data["host"]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for hifiberry."""

    VERSION = 2

    def __init__(self) -> None:
        """Initialize with default hostname."""
        self.host = "hifiberry.local"

    @property
    def schema(self):
        """Return current schema."""
        return vol.Schema(
            {
                vol.Required("host", default=self.host): str,
                vol.Optional("port", default=80): int,
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

        await self.async_set_unique_id(user_input["host"])
        self._abort_if_unique_id_configured()

        try:
            info = await validate_input(self.hass, user_input)
        except AudioControlError:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=self.schema, errors=errors
        )
