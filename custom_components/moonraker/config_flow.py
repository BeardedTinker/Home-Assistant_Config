"""Adds config flow for Moonraker."""

import logging

from typing import Any

import async_timeout
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.util import network, slugify

from .api import MoonrakerApiClient
from .const import (
    CONF_API_KEY,
    CONF_PORT,
    CONF_PRINTER_NAME,
    CONF_TLS,
    CONF_URL,
    CONF_OPTION_POLLING_RATE,
    CONF_OPTION_CAMERA_STREAM,
    CONF_OPTION_CAMERA_SNAPSHOT,
    CONF_OPTION_CAMERA_PORT,
    CONF_OPTION_THUMBNAIL_PORT,
    DOMAIN,
    TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class MoonrakerFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Moonraker."""

    VERSION = 1

    def __init__(self):
        """Initialize."""
        _LOGGER.debug("loading moonraker confFlowHandler")
        self._errors = {}

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        self._errors = {}

        if user_input is not None:
            if not await self._test_host(user_input[CONF_URL]):
                self._errors[CONF_URL] = "host_error"
                return await self._show_config_form(user_input)

            if not await self._test_port(user_input[CONF_PORT]):
                self._errors[CONF_PORT] = "port_error"
                return await self._show_config_form(user_input)

            if not await self._test_api_key(user_input[CONF_API_KEY]):
                self._errors[CONF_API_KEY] = "api_key_error"
                return await self._show_config_form(user_input)

            if not await self._test_printer_name(user_input[CONF_PRINTER_NAME]):
                self._errors[CONF_PRINTER_NAME] = "printer_name_error"
                return await self._show_config_form(user_input)

            if not await self._test_connection(
                user_input[CONF_URL],
                user_input[CONF_PORT],
                user_input[CONF_API_KEY],
                user_input[CONF_TLS],
            ):
                self._errors[CONF_URL] = "printer_connection_error"
                return await self._show_config_form(user_input)

            # changer DOMAIN pour name
            return self.async_create_entry(title=DOMAIN, data=user_input)

        user_input = {}
        # Provide defaults for form
        user_input[CONF_URL] = "192.168.1.123"
        user_input[CONF_PORT] = "7125"
        user_input[CONF_TLS] = False
        user_input[CONF_API_KEY] = ""
        user_input[CONF_PRINTER_NAME] = ""

        return await self._show_config_form(user_input)

    async def _show_config_form(self, user_input):  # pylint: disable=unused-argument
        """Show the configuration form to edit location data."""

        _LOGGER.debug("Showing moonraker conf")
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_URL, default=user_input[CONF_URL]): str,
                    vol.Optional(CONF_PORT, default=user_input[CONF_PORT]): str,
                    vol.Optional(CONF_TLS, default=user_input[CONF_TLS]): bool,
                    vol.Optional(CONF_API_KEY, default=user_input[CONF_API_KEY]): str,
                    vol.Optional(
                        CONF_PRINTER_NAME, default=user_input[CONF_PRINTER_NAME]
                    ): str,
                }
            ),
            errors=self._errors,
        )

    async def _test_host(self, host: str):
        return network.is_host_valid(host)

    async def _test_port(self, port):
        if port != "":
            if not port.isdigit() or int(port) > 65535 or int(port) <= 1:
                return False
        return True

    async def _test_api_key(self, api_key):
        if api_key != "":
            if not api_key.isalnum() or len(api_key) != 32:
                return False
        return True

    async def _test_printer_name(self, printer_name):
        slugified_name = slugify(printer_name)

        if slugified_name == "unknown":
            return False

        return True

    async def _test_connection(self, host, port, api_key, tls):
        api = MoonrakerApiClient(
            host,
            async_get_clientsession(self.hass, verify_ssl=False),
            port=port,
            api_key=api_key,
            tls=tls,
        )

        try:
            await api.start()
            async with async_timeout.timeout(TIMEOUT):
                await api.client.call_method("printer.info")
                return True
        except Exception:
            return False

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_OPTION_POLLING_RATE,
                        default=self.config_entry.options.get(
                            CONF_OPTION_POLLING_RATE, 30
                        ),
                    ): int,
                    vol.Optional(
                        CONF_OPTION_CAMERA_STREAM,
                        default=self.config_entry.options.get(
                            CONF_OPTION_CAMERA_STREAM, ""
                        ),
                    ): str,
                    vol.Optional(
                        CONF_OPTION_CAMERA_SNAPSHOT,
                        default=self.config_entry.options.get(
                            CONF_OPTION_CAMERA_SNAPSHOT, ""
                        ),
                    ): str,
                    vol.Optional(
                        CONF_OPTION_CAMERA_PORT,
                        default=self.config_entry.options.get(
                            CONF_OPTION_CAMERA_PORT, ""
                        ),
                    ): str,
                    vol.Optional(
                        CONF_OPTION_THUMBNAIL_PORT,
                        default=self.config_entry.options.get(
                            CONF_OPTION_THUMBNAIL_PORT, ""
                        ),
                    ): str,
                }
            ),
        )
