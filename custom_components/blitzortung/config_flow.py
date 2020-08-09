"""Config flow for blitzortung integration."""
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME

from .const import (
    CONF_MAX_TRACKED_LIGHTNINGS,
    CONF_RADIUS,
    CONF_TIME_WINDOW,
    DEFAULT_MAX_TRACKED_LIGHTNINGS,
    DEFAULT_RADIUS,
    DEFAULT_TIME_WINDOW,
    DOMAIN,
)

DEFAULT_CONF_NAME = "Blitzortung"


class DomainConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for blitzortung."""

    VERSION = 4
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_NAME])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=user_input[CONF_NAME], data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_NAME, default=DEFAULT_CONF_NAME): str}
            ),
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry):
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_LATITUDE,
                        default=self.config_entry.options.get(
                            CONF_LATITUDE, self.hass.config.latitude
                        ),
                    ): cv.latitude,
                    vol.Required(
                        CONF_LONGITUDE,
                        default=self.config_entry.options.get(
                            CONF_LONGITUDE, self.hass.config.longitude
                        ),
                    ): cv.longitude,
                    vol.Required(
                        CONF_RADIUS,
                        default=self.config_entry.options.get(
                            CONF_RADIUS, DEFAULT_RADIUS
                        ),
                    ): int,
                    vol.Optional(
                        CONF_TIME_WINDOW,
                        default=self.config_entry.options.get(
                            CONF_TIME_WINDOW, DEFAULT_TIME_WINDOW,
                        ),
                    ): int,
                    vol.Optional(
                        CONF_MAX_TRACKED_LIGHTNINGS,
                        default=self.config_entry.options.get(
                            CONF_MAX_TRACKED_LIGHTNINGS, DEFAULT_MAX_TRACKED_LIGHTNINGS,
                        ),
                    ): int,
                }
            ),
        )
