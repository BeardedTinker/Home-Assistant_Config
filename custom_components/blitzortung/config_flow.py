"""Config flow for blitzortung integration."""

import voluptuous as vol
from typing import Any
import homeassistant.helpers.config_validation as cv
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithConfigEntry,
)
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

RECONFIGURE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_LATITUDE): cv.latitude,
        vol.Required(CONF_LONGITUDE): cv.longitude,
    }
)


class BlitortungConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for blitzortung."""

    VERSION = 5

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            await self.async_set_unique_id(
                f"{user_input[CONF_LATITUDE]}-{user_input[CONF_LONGITUDE]}"
            )
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_NAME],
                data=user_input,
                options={
                    CONF_RADIUS: DEFAULT_RADIUS,
                    CONF_MAX_TRACKED_LIGHTNINGS: DEFAULT_MAX_TRACKED_LIGHTNINGS,
                    CONF_TIME_WINDOW: DEFAULT_TIME_WINDOW,
                },
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME, default=self.hass.config.location_name
                    ): str,
                    vol.Required(
                        CONF_LATITUDE,
                        default=self.hass.config.latitude,
                    ): cv.latitude,
                    vol.Required(
                        CONF_LONGITUDE,
                        default=self.hass.config.longitude,
                    ): cv.longitude,
                }
            ),
        )

    async def async_step_reconfigure(
        self, _: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""
        self.entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])

        return await self.async_step_reconfigure_confirm()

    async def async_step_reconfigure_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a reconfiguration flow initialized by the user."""
        errors = {}

        if user_input is not None:
            self.hass.config_entries.async_update_entry(
                self.entry, data=self.entry.data | user_input
            )
            await self.hass.config_entries.async_reload(self.entry.entry_id)
            return self.async_abort(reason="reconfigure_successful")

        return self.async_show_form(
            step_id="reconfigure_confirm",
            data_schema=self.add_suggested_values_to_schema(
                data_schema=RECONFIGURE_SCHEMA,
                suggested_values=self.entry.data | (user_input or {}),
            ),
            description_placeholders={"name": self.entry.title},
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry):
        return BlitzortungOptionsFlowHandler(config_entry)


class BlitzortungOptionsFlowHandler(OptionsFlowWithConfigEntry):
    """Handle an options flow for Blitzortung."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        options_schema = vol.Schema(
            {
                vol.Required(
                    CONF_RADIUS,
                    default=self.config_entry.options.get(CONF_RADIUS, DEFAULT_RADIUS),
                ): int,
                vol.Optional(
                    CONF_TIME_WINDOW,
                    default=self.config_entry.options.get(
                        CONF_TIME_WINDOW,
                        DEFAULT_TIME_WINDOW,
                    ),
                ): int,
                vol.Optional(
                    CONF_MAX_TRACKED_LIGHTNINGS,
                    default=self.config_entry.options.get(
                        CONF_MAX_TRACKED_LIGHTNINGS,
                        DEFAULT_MAX_TRACKED_LIGHTNINGS,
                    ),
                ): int,
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                options_schema, self.config_entry.options
            ),
        )
