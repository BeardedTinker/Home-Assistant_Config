"""Config flow for OpenEPaperLink integration."""
from __future__ import annotations

import asyncio
from typing import Any, Mapping, Final

import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry, OptionsFlow
from homeassistant.const import CONF_HOST
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import Selector, TextSelectorType

from .const import DOMAIN
import logging

_LOGGER: Final = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for OpenEPaperLink.

    Implements the flow for initial integration setup and reauthorization.
    The flow validates that the provided AP host is reachable and responds
    correctly before creating a configuration entry.

    The class stores connection state throughout the flow steps to maintain
    context between user interactions.
    """

    VERSION = 2

    def __init__(self) -> None:
        """Initialize flow."""
        self._host: str | None = None

    async def _validate_input(self, host: str) -> tuple[dict[str, str], str | None]:
        """Validate the user input allows us to connect to the OpenEPaperLink AP.

        Tests the connection to the specified host address by:

        1. Sanitizing the input (removing protocol prefixes, trailing slashes)
        2. Attempting an HTTP request to the root endpoint
        3. Verifying the response indicates a valid OpenEPaperLink AP

        Args:
            host: The hostname or IP address of the AP

        Returns:
            tuple: A tuple containing:
                - A dictionary with validated info (empty if validation failed)
                - An error code string if validation failed, None otherwise
        """
        errors = {}
        info = None

        # Remove any http:// or https:// prefix
        host = host.replace("http://", "").replace("https://", "")
        # Remove any trailing slashes
        host = host.rstrip("/")

        try:
            session = async_get_clientsession(self.hass)
            async with asyncio.timeout(10):
                async with session.get(f"http://{host}") as response:
                    if response.status != 200:
                        errors["base"] = "cannot_connect"
                    else:
                        # Store version info for later display
                        self._host = host
                        return {"title": f"OpenEPaperLink AP ({host})"}, None

        except asyncio.TimeoutError:
            errors["base"] = "timeout"
        except aiohttp.ClientError:
            errors["base"] = "cannot_connect"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"

        return {}, errors.get("base", "unknown")

    async def async_step_user(
            self, user_input: dict[str, Any] | None = None
    ):
        """Handle the initial step of the config flow.

        Presents a form for the user to enter the AP host address,
        validates the connection, and creates a config entry if successful.

        Args:
            user_input: User-provided configuration data, or None if the
                       form is being shown for the first time

        Returns:
            FlowResult: Result of the flow step, either showing the form
                       again (with errors if applicable) or creating an entry
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            info, error = await self._validate_input(user_input[CONF_HOST])
            if not error:
                await self.async_set_unique_id(self._host)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=info["title"],
                    data={CONF_HOST: self._host}
                )

            errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reauth(self, entry_data: Mapping[str, Any]):
        """Handle reauthorization flow initiated by connection failure.

        Prepares for reauthorization by extracting the current host from
        the existing config entry data and storing it for validation.

        Args:
            entry_data: Data from the existing config entry

        Returns:
            FlowResult: Flow result directing to the reauth confirmation step
        """
        self._host = entry_data[CONF_HOST]
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
            self, user_input: dict[str, Any] | None = None
    ):
        """Handle reauthorization confirmation.

        Validates the connection to the previously configured AP.

        If successful, updates the existing config entry;
        if not, shows an error.

        Args:
            user_input: User input from form, or None on first display

        Returns:
            FlowResult: Flow result object for the next step or completion
        """
        errors: dict[str, str] = {}

        if user_input is not None:
            info, error = await self._validate_input(self._host)
            if not error:
                entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
                if entry:
                    self.hass.config_entries.async_update_entry(
                        entry,
                        data={**entry.data, CONF_HOST: self._host},
                    )
                    await self.hass.config_entries.async_reload(entry.entry_id)
                    return self.async_abort(reason="reauth_successful")

            errors["base"] = error

        return self.async_show_form(
            step_id="reauth_confirm",
            description_placeholders={"host": self._host},
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Create the options flow handler.

        Returns an instance of the OptionsFlowHandler to manage the
        integration's configuration options.

        Args:
            config_entry: The current configuration entry

        Returns:
            OptionsFlow: The options flow handler
        """
        return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle OpenEPaperLink integration options.

    Provides a UI for configuring integration options including:

    - Tag blacklisting to hide unwanted devices
    - Button and NFC debounce intervals to prevent duplicate triggers
    - Custom font directories for the image generation system

    The options flow fetches current tag data from the hub to
    populate the selection fields with accurate information.
    """

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow with the current configuration.

        Stores references to the current config entry and extracts
        existing option values to use as defaults in the flow.

        Args:
            config_entry: Current configuration entry
        """
        self.config_entry = config_entry
        self._blacklisted_tags = self.config_entry.options.get("blacklisted_tags", [])
        self._button_debounce = self.config_entry.options.get("button_debounce", 0.5)
        self._nfc_debounce = self.config_entry.options.get("nfc_debounce", 1.0)
        self._custom_font_dirs = self.config_entry.options.get("custom_font_dirs", "")

    async def async_step_init(self, user_input=None):
        """Manage OpenEPaperLink options.

        Presents a form with configuration options for the integration.
        When submitted, updates the config entry with the new options.

        This step retrieves a list of available tags from the hub to
        allow selection of tags to blacklist.

        Args:
            user_input: User-provided input data, or None on first display

        Returns:
            FlowResult: Flow result showing the form or saving options
        """
        if user_input is not None:
            # Update blacklisted tags
            return self.async_create_entry(
                title="",
                data={
                    "blacklisted_tags": user_input.get("blacklisted_tags", []),
                    "button_debounce": user_input.get("button_debounce", 0.5),
                    "nfc_debounce": user_input.get("nfc_debounce", 1.0),
                    "custom_font_dirs": user_input.get("custom_font_dirs", ""),
                }
            )

        # Get list of all known tags from the hub
        hub = self.hass.data[DOMAIN][self.config_entry.entry_id]
        tags = []
        for tag_mac in hub.tags:
            tag_data = hub.get_tag_data(tag_mac)
            tag_name = tag_data.get("tag_name", tag_mac)
            tags.append(
                selector.SelectOptionDict(
                    value=tag_mac,
                    label=f"{tag_name} ({tag_mac})"
                )
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "blacklisted_tags",
                    default=self._blacklisted_tags,
                ): selector.SelectSelector(
                    selector.SelectSelectorConfig(
                        options=tags,
                        multiple=True,
                        mode=selector.SelectSelectorMode.DROPDOWN
                    )
                ),
                vol.Optional(
                    "button_debounce",
                    default=self._button_debounce,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=5.0,
                        step=0.1,
                        unit_of_measurement="s",
                        mode=selector.NumberSelectorMode.SLIDER
                    )
                ),
                vol.Optional(
                    "nfc_debounce",
                    default=self._nfc_debounce,
                ): selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=0.0,
                        max=5.0,
                        step=0.1,
                        unit_of_measurement="s",
                        mode=selector.NumberSelectorMode.SLIDER
                    )
                ),
                vol.Optional(
                    "custom_font_dirs",
                    default=self._custom_font_dirs,
                    description={
                        "suggested_value": None
                    }
                ): selector.TextSelector(
                    selector.TextSelectorConfig(
                        type=TextSelectorType.TEXT,
                        autocomplete="path"
                    )
                ),
            }),
        )