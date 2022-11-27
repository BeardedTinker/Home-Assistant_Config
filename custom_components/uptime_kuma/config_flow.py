"""Config flow for Uptime Kuma integration."""
from __future__ import annotations

from typing import Any

from pyuptimekuma import UptimeKuma, UptimeKumaException
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, LOGGER

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=443): vol.Coerce(int),
        vol.Optional(CONF_USERNAME, default=""): str,
        vol.Optional(CONF_PASSWORD, default=""): str,
        vol.Optional(CONF_VERIFY_SSL, default=True): bool,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Uptime Kuma."""

    VERSION = 1

    async def _validate_input(
        self, data: dict[str, Any]
    ) -> tuple[dict[str, str], None]:
        """Validate the user input allows us to connect."""
        errors: dict[str, str] = {}
        host: str = data[CONF_HOST]
        port: int = data[CONF_PORT]
        username: str = data[CONF_USERNAME]
        password: str = data[CONF_PASSWORD]
        verify_ssl: bool = data[CONF_VERIFY_SSL]

        uptime_robot_api = UptimeKuma(
            async_get_clientsession(self.hass),
            f"{host}:{port}",
            username,
            password,
            verify_ssl,
        )

        try:
            await uptime_robot_api.async_get_monitors()
        except UptimeKumaException as exception:
            LOGGER.error(exception)
            errors["base"] = "cannot_connect"
        except Exception as exception:  # pylint: disable=broad-except
            LOGGER.exception(exception)
            errors["base"] = "unknown"
            # return await self._show_setup_form(errors)

        return errors

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = await self._validate_input(user_input)
        if not errors:
            unique_id = f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=unique_id, data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )
