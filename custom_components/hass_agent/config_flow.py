"""Config flow for HASS.Agent"""
from __future__ import annotations
import json
import logging
import requests
import voluptuous as vol

from typing import Any
from homeassistant.components.notify import ATTR_TITLE_DEFAULT
from homeassistant.core import callback

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_PORT, CONF_SSL, CONF_URL
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.service_info.mqtt import MqttServiceInfo

from .const import DOMAIN, CONF_DEFAULT_NOTIFICATION_TITLE

_logger = logging.getLogger(__name__)


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            user_input[CONF_DEFAULT_NOTIFICATION_TITLE] = user_input[
                CONF_DEFAULT_NOTIFICATION_TITLE
            ].strip()

            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_DEFAULT_NOTIFICATION_TITLE,
                        default=self.config_entry.options.get(
                            CONF_DEFAULT_NOTIFICATION_TITLE, ATTR_TITLE_DEFAULT
                        ),
                    ): str
                }
            ),
        )


class FlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize flow."""
        self._device_name = ""
        self._data = {}

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)

    async def async_step_mqtt(self, discovery_info: MqttServiceInfo) -> FlowResult:
        """Handle a flow initialized by MQTT discovery."""
        device_name = discovery_info.topic.split("hass.agent/devices/")[1]

        payload = json.loads(discovery_info.payload)

        serial_number = payload["serial_number"]

        _logger.debug(
            "found device. Name: %s, Serial Number: %s", device_name, serial_number
        )

        self._data = {"device": payload["device"], "apis": payload["apis"]}

        for config in self._async_current_entries():
            if config.unique_id == serial_number:
                return self.async_abort(reason="already_configured")

        await self.async_set_unique_id(serial_number)

        # "hass.agent/devices/#" is hardcoded in HASS.Agent's manifest
        assert discovery_info.subscribed_topic == "hass.agent/devices/#"

        self._device_name = device_name

        return await self.async_step_confirm()

    async def async_step_local_api(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:

        errors = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            use_ssl = user_input[CONF_SSL]

            protocol = "https" if use_ssl else "http"

            url = f"{protocol}://{host}:{port}"

            # serial number!
            try:

                def get_device_info():
                    return requests.get(f"{url}/info", timeout=10)

                response = await self.hass.async_add_executor_job(get_device_info)

                response_json = response.json()

                await self.async_set_unique_id(response_json["serial_number"])

                return self.async_create_entry(
                    title=response_json["device"]["name"],
                    data={CONF_URL: url},
                    options={CONF_DEFAULT_NOTIFICATION_TITLE: ATTR_TITLE_DEFAULT},
                )

            except Exception:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="local_api",
            data_schema=vol.Schema(
                # pylint: disable=no-value-for-parameter
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=5115): int,
                    vol.Required(CONF_SSL): bool,
                }
            ),
            errors=errors,
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        return await self.async_step_local_api()

    async def async_step_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm the setup."""

        if user_input is not None:
            return self.async_create_entry(
                title=self._device_name,
                data=self._data,
                options={CONF_DEFAULT_NOTIFICATION_TITLE: ATTR_TITLE_DEFAULT},
            )

        placeholders = {CONF_NAME: self._device_name}

        self.context["title_placeholders"] = placeholders

        self._set_confirm_only()

        return self.async_show_form(
            step_id="confirm",
            description_placeholders=placeholders,
        )
