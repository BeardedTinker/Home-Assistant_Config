"""Config flow to configure Mikrotik Router."""

import logging

import voluptuous as vol
from homeassistant.config_entries import (
    CONN_CLASS_LOCAL_POLL,
    ConfigFlow,
    OptionsFlow,
)
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_PORT,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SSL,
    CONF_ZONE,
    STATE_HOME,
)
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_TRACK_IFACE_CLIENTS,
    DEFAULT_TRACK_IFACE_CLIENTS,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    CONF_TRACK_HOSTS,
    DEFAULT_TRACK_HOSTS,
    CONF_SENSOR_PORT_TRACKER,
    DEFAULT_SENSOR_PORT_TRACKER,
    CONF_SENSOR_PORT_TRAFFIC,
    DEFAULT_SENSOR_PORT_TRAFFIC,
    CONF_SENSOR_CLIENT_TRAFFIC,
    DEFAULT_SENSOR_CLIENT_TRAFFIC,
    CONF_SENSOR_SIMPLE_QUEUES,
    DEFAULT_SENSOR_SIMPLE_QUEUES,
    CONF_SENSOR_NAT,
    DEFAULT_SENSOR_NAT,
    CONF_SENSOR_MANGLE,
    DEFAULT_SENSOR_MANGLE,
    CONF_SENSOR_FILTER,
    DEFAULT_SENSOR_FILTER,
    CONF_SENSOR_KIDCONTROL,
    DEFAULT_SENSOR_KIDCONTROL,
    CONF_SENSOR_PPP,
    DEFAULT_SENSOR_PPP,
    CONF_SENSOR_SCRIPTS,
    DEFAULT_SENSOR_SCRIPTS,
    CONF_SENSOR_ENVIRONMENT,
    DEFAULT_SENSOR_ENVIRONMENT,
    CONF_TRACK_HOSTS_TIMEOUT,
    DEFAULT_TRACK_HOST_TIMEOUT,
    LIST_UNIT_OF_MEASUREMENT,
    DEFAULT_UNIT_OF_MEASUREMENT,
    DEFAULT_HOST,
    DEFAULT_USERNAME,
    DEFAULT_PASSWORD,
    DEFAULT_PORT,
    DEFAULT_DEVICE_NAME,
    DEFAULT_SSL,
)
from .mikrotikapi import MikrotikAPI

_LOGGER = logging.getLogger(__name__)


# ---------------------------
#   configured_instances
# ---------------------------
@callback
def configured_instances(hass):
    """Return a set of configured instances."""
    return set(
        entry.data[CONF_NAME] for entry in hass.config_entries.async_entries(DOMAIN)
    )


# ---------------------------
#   MikrotikControllerConfigFlow
# ---------------------------
class MikrotikControllerConfigFlow(ConfigFlow, domain=DOMAIN):
    """MikrotikControllerConfigFlow class"""

    VERSION = 1
    CONNECTION_CLASS = CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize MikrotikControllerConfigFlow."""

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return MikrotikControllerOptionsFlowHandler(config_entry)

    async def async_step_import(self, user_input=None):
        """Occurs when a previously entry setup fails and is re-initiated."""
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            # Check if instance with this name already exists
            if user_input[CONF_NAME] in configured_instances(self.hass):
                errors["base"] = "name_exists"

            # Test connection
            api = MikrotikAPI(
                host=user_input[CONF_HOST],
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                port=user_input[CONF_PORT],
                use_ssl=user_input[CONF_SSL],
            )
            if not api.connect():
                errors[CONF_HOST] = api.error

            # Save instance
            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_NAME], data=user_input
                )

            return self._show_config_form(user_input=user_input, errors=errors)

        return self._show_config_form(
            user_input={
                CONF_NAME: DEFAULT_DEVICE_NAME,
                CONF_HOST: DEFAULT_HOST,
                CONF_USERNAME: DEFAULT_USERNAME,
                CONF_PASSWORD: DEFAULT_PASSWORD,
                CONF_PORT: DEFAULT_PORT,
                CONF_SSL: DEFAULT_SSL,
            },
            errors=errors,
        )

    # ---------------------------
    #   _show_config_form
    # ---------------------------
    def _show_config_form(self, user_input, errors=None):
        """Show the configuration form to edit data."""
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=user_input[CONF_NAME]): str,
                    vol.Required(CONF_HOST, default=user_input[CONF_HOST]): str,
                    vol.Required(CONF_USERNAME, default=user_input[CONF_USERNAME]): str,
                    vol.Required(CONF_PASSWORD, default=user_input[CONF_PASSWORD]): str,
                    vol.Optional(CONF_PORT, default=user_input[CONF_PORT]): int,
                    vol.Optional(CONF_SSL, default=user_input[CONF_SSL]): bool,
                }
            ),
            errors=errors,
        )


# ---------------------------
#   MikrotikControllerOptionsFlowHandler
# ---------------------------
class MikrotikControllerOptionsFlowHandler(OptionsFlow):
    """Handle options."""

    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry
        self.options = dict(config_entry.options)

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_basic_options(user_input)

    async def async_step_basic_options(self, user_input=None):
        """Manage the basic options options."""
        if user_input is not None:
            self.options.update(user_input)
            return await self.async_step_sensor_select()

        return self.async_show_form(
            step_id="basic_options",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        default=self.config_entry.options.get(
                            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
                        ),
                    ): int,
                    vol.Optional(
                        CONF_UNIT_OF_MEASUREMENT,
                        default=self.config_entry.options.get(
                            CONF_UNIT_OF_MEASUREMENT, DEFAULT_UNIT_OF_MEASUREMENT
                        ),
                    ): vol.In(LIST_UNIT_OF_MEASUREMENT),
                    vol.Optional(
                        CONF_TRACK_IFACE_CLIENTS,
                        default=self.config_entry.options.get(
                            CONF_TRACK_IFACE_CLIENTS, DEFAULT_TRACK_IFACE_CLIENTS
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_TRACK_HOSTS_TIMEOUT,
                        default=self.config_entry.options.get(
                            CONF_TRACK_HOSTS_TIMEOUT, DEFAULT_TRACK_HOST_TIMEOUT
                        ),
                    ): int,
                    vol.Optional(
                        CONF_ZONE,
                        default=self.config_entry.options.get(CONF_ZONE, STATE_HOME),
                    ): str,
                }
            ),
        )

    async def async_step_sensor_select(self, user_input=None):
        """Manage the sensor select options."""
        if user_input is not None:
            self.options.update(user_input)
            return self.async_create_entry(title="", data=self.options)

        return self.async_show_form(
            step_id="sensor_select",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SENSOR_PORT_TRACKER,
                        default=self.config_entry.options.get(
                            CONF_SENSOR_PORT_TRACKER, DEFAULT_SENSOR_PORT_TRACKER
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_SENSOR_PORT_TRAFFIC,
                        default=self.config_entry.options.get(
                            CONF_SENSOR_PORT_TRAFFIC, DEFAULT_SENSOR_PORT_TRAFFIC
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_TRACK_HOSTS,
                        default=self.config_entry.options.get(
                            CONF_TRACK_HOSTS, DEFAULT_TRACK_HOSTS
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_SENSOR_CLIENT_TRAFFIC,
                        default=self.config_entry.options.get(
                            CONF_SENSOR_CLIENT_TRAFFIC, DEFAULT_SENSOR_CLIENT_TRAFFIC
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_SENSOR_SIMPLE_QUEUES,
                        default=self.config_entry.options.get(
                            CONF_SENSOR_SIMPLE_QUEUES, DEFAULT_SENSOR_SIMPLE_QUEUES
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_SENSOR_NAT,
                        default=self.config_entry.options.get(
                            CONF_SENSOR_NAT, DEFAULT_SENSOR_NAT
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_SENSOR_MANGLE,
                        default=self.config_entry.options.get(
                            CONF_SENSOR_MANGLE, DEFAULT_SENSOR_MANGLE
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_SENSOR_FILTER,
                        default=self.config_entry.options.get(
                            CONF_SENSOR_FILTER, DEFAULT_SENSOR_FILTER
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_SENSOR_KIDCONTROL,
                        default=self.config_entry.options.get(
                            CONF_SENSOR_KIDCONTROL, DEFAULT_SENSOR_KIDCONTROL
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_SENSOR_PPP,
                        default=self.config_entry.options.get(
                            CONF_SENSOR_PPP, DEFAULT_SENSOR_PPP
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_SENSOR_SCRIPTS,
                        default=self.config_entry.options.get(
                            CONF_SENSOR_SCRIPTS, DEFAULT_SENSOR_SCRIPTS
                        ),
                    ): bool,
                    vol.Optional(
                        CONF_SENSOR_ENVIRONMENT,
                        default=self.config_entry.options.get(
                            CONF_SENSOR_ENVIRONMENT, DEFAULT_SENSOR_ENVIRONMENT
                        ),
                    ): bool,
                },
            ),
        )
