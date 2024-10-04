from __future__ import annotations
from typing import Any
from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN  # pylint:disable=unused-import
from .hub import Hub
import voluptuous as vol
import logging

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema({("host"): str})


async def validate_input(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    if len(data["host"]) < 3:
        raise InvalidHost
    # remove http or https from the host
    data["host"] = data["host"].replace("http://", "").replace("https://", "").replace("/", "")
    hub = Hub(hass, data["host"], "")
    result = await hub.test_connection()
    if not result:
        raise CannotConnect
    return {"title": data["host"]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 2
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                errors["host"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
