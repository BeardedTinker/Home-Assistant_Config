"""Config flow for MusicAssistant integration."""
from __future__ import annotations

import asyncio
from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.components import zeroconf
from homeassistant.components.hassio import (
    AddonError,
    AddonInfo,
    AddonManager,
    AddonState,
    is_hassio,
)
from homeassistant.const import CONF_URL
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import AbortFlow, FlowResult
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import aiohttp_client, selector
from music_assistant.client import MusicAssistantClient
from music_assistant.client.exceptions import CannotConnect, InvalidServerVersion
from music_assistant.common.models.api import ServerInfoMessage

from .addon import get_addon_manager, install_repository
from .const import (
    ADDON_HOSTNAME,
    CONF_ASSIST_AUTO_EXPOSE_PLAYERS,
    CONF_INTEGRATION_CREATED_ADDON,
    CONF_OPENAI_AGENT_ID,
    CONF_USE_ADDON,
    DOMAIN,
    LOGGER,
)

ADDON_SETUP_TIMEOUT = 5
ADDON_SETUP_TIMEOUT_ROUNDS = 40
DEFAULT_URL = "http://mass.local:8095"
ADDON_URL = f"http://{ADDON_HOSTNAME}:8095"
DEFAULT_TITLE = "Music Assistant"

ON_SUPERVISOR_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_USE_ADDON, default=True): bool,
        vol.Optional(CONF_OPENAI_AGENT_ID, default=""): selector.ConversationAgentSelector(
            selector.ConversationAgentSelectorConfig(language="en")
        ),
        vol.Optional(CONF_ASSIST_AUTO_EXPOSE_PLAYERS, default=False): bool,
    }
)


def get_manual_schema(user_input: dict[str, Any]) -> vol.Schema:
    """Return a schema for the manual step."""
    default_url = user_input.get(CONF_URL, DEFAULT_URL)
    return vol.Schema(
        {
            vol.Required(CONF_URL, default=default_url): str,
            vol.Optional(CONF_OPENAI_AGENT_ID, default=""): selector.ConversationAgentSelector(
                selector.ConversationAgentSelectorConfig(language="en")
            ),
            vol.Optional(CONF_ASSIST_AUTO_EXPOSE_PLAYERS, default=False): bool,
        }
    )


def get_zeroconf_schema() -> vol.Schema:
    """Return a schema for the zeroconf step."""
    return vol.Schema(
        {
            vol.Optional(CONF_OPENAI_AGENT_ID, default=""): selector.ConversationAgentSelector(
                selector.ConversationAgentSelectorConfig(language="en")
            ),
            vol.Optional(CONF_ASSIST_AUTO_EXPOSE_PLAYERS, default=False): bool,
        }
    )


async def get_server_info(hass: HomeAssistant, url: str) -> ServerInfoMessage:
    """Validate the user input allows us to connect."""
    async with MusicAssistantClient(url, aiohttp_client.async_get_clientsession(hass)) as client:
        return client.server_info


# ruff: noqa: ARG002


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for MusicAssistant."""

    VERSION = 1

    def __init__(self) -> None:
        """Set up flow instance."""
        self.server_info: ServerInfoMessage | None = None
        self.openai_agent_id: str | None = None
        self.expose_players_assist: bool | None = None
        # If we install the add-on we should uninstall it on entry remove.
        self.integration_created_addon = False
        self.install_task: asyncio.Task | None = None
        self.start_task: asyncio.Task | None = None
        self.use_addon = False

    async def async_step_install_addon(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Install MusicAssistant Server add-on."""
        if not self.install_task:
            self.install_task = self.hass.async_create_task(self._async_install_addon())
            return self.async_show_progress(
                step_id="install_addon", progress_action="install_addon"
            )
        try:
            await self.install_task
        except AddonError as err:
            self.install_task = None
            LOGGER.error(err)
            return self.async_show_progress_done(next_step_id="install_failed")

        self.integration_created_addon = True
        self.install_task = None

        return self.async_show_progress_done(next_step_id="start_addon")

    async def async_step_install_failed(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Add-on installation failed."""
        return self.async_abort(reason="addon_install_failed")

    async def _async_install_addon(self) -> None:
        """Install the MusicAssistant Server add-on."""
        addon_manager: AddonManager = get_addon_manager(self.hass)
        try:
            await addon_manager.async_schedule_install_addon()
        finally:
            # Continue the flow after show progress when the task is done.
            self.hass.async_create_task(
                self.hass.config_entries.flow.async_configure(flow_id=self.flow_id)
            )

    async def async_step_start_addon(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Start MusicAssistant Server add-on."""
        if not self.start_task:
            self.start_task = self.hass.async_create_task(self._async_start_addon())
            return self.async_show_progress(step_id="start_addon", progress_action="start_addon")
        try:
            await self.start_task
        except (FailedConnect, AddonError, AbortFlow) as err:
            self.start_task = None
            LOGGER.error(err)
            return self.async_show_progress_done(next_step_id="start_failed")

        self.start_task = None
        return self.async_show_progress_done(next_step_id="finish_addon_setup")

    async def async_step_start_failed(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Add-on start failed."""
        return self.async_abort(reason="addon_start_failed")

    async def _async_start_addon(self) -> None:
        """Start the MusicAssistant Server add-on."""
        addon_manager: AddonManager = get_addon_manager(self.hass)

        try:
            await addon_manager.async_schedule_start_addon()

            # Sleep some seconds to let the add-on start properly before connecting.
            for _ in range(ADDON_SETUP_TIMEOUT_ROUNDS):
                await asyncio.sleep(ADDON_SETUP_TIMEOUT)
                try:
                    self.server_info = await get_server_info(self.hass, ADDON_URL)
                    await self.async_set_unique_id(self.server_info.server_id)
                except (AbortFlow, CannotConnect) as err:
                    LOGGER.debug(
                        "Add-on not ready yet, waiting %s seconds: %s",
                        ADDON_SETUP_TIMEOUT,
                        err,
                    )
                else:
                    break
            else:
                raise FailedConnect("Failed to start MusicAssistant Server add-on: timeout")
        finally:
            # Continue the flow after show progress when the task is done.
            self.hass.async_create_task(
                self.hass.config_entries.flow.async_configure(flow_id=self.flow_id)
            )

    async def _async_get_addon_info(self) -> AddonInfo:
        """Return MusicAssistant Server add-on info."""
        addon_manager: AddonManager = get_addon_manager(self.hass)
        try:
            addon_info: AddonInfo = await addon_manager.async_get_addon_info()
        except AddonError as err:
            LOGGER.error(err)
            raise AbortFlow("addon_info_failed") from err

        return addon_info

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        if is_hassio(self.hass):
            return await self.async_step_on_supervisor()

        return await self.async_step_manual()

    async def async_step_manual(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle a manual configuration."""
        if user_input is None:
            return self.async_show_form(step_id="manual", data_schema=get_manual_schema({}))

        errors = {}

        try:
            self.server_info = await get_server_info(self.hass, user_input[CONF_URL])
            self.openai_agent_id = user_input[CONF_OPENAI_AGENT_ID]
            self.expose_players_assist = user_input[CONF_ASSIST_AUTO_EXPOSE_PLAYERS]
            await self.async_set_unique_id(self.server_info.server_id)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidServerVersion:
            errors["base"] = "invalid_server_version"
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return await self._async_create_entry_or_abort()

        return self.async_show_form(
            step_id="manual", data_schema=get_manual_schema(user_input), errors=errors
        )

    async def async_step_zeroconf(self, discovery_info: zeroconf.ZeroconfServiceInfo) -> FlowResult:
        """
        Handle a discovered Mass server.

        This flow is triggered by the Zeroconf component. It will check if the
        host is already configured and delegate to the import step if not.
        """
        # abort if we already have exactly this server_id
        # reload the integration if the host got updated
        server_id = discovery_info.properties["server_id"]
        base_url = discovery_info.properties["base_url"]
        await self.async_set_unique_id(server_id)
        self._abort_if_unique_id_configured(
            updates={CONF_URL: base_url},
            reload_on_update=True,
        )
        self.server_info = ServerInfoMessage.from_dict(discovery_info.properties)
        return await self.async_step_discovery_confirm()

    async def async_step_discovery_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle user-confirmation of discovered server."""
        if user_input is not None:
            # Check that we can connect to the address.
            try:
                self.openai_agent_id = user_input[CONF_OPENAI_AGENT_ID]
                self.expose_players_assist = user_input[CONF_ASSIST_AUTO_EXPOSE_PLAYERS]
                await get_server_info(self.hass, self.server_info.base_url)
            except CannotConnect:
                return self.async_abort(reason="cannot_connect")
            return await self._async_create_entry_or_abort()
        return self.async_show_form(
            step_id="discovery_confirm",
            data_schema=get_zeroconf_schema(),
            description_placeholders={"url": self.server_info.base_url},
        )

    async def async_step_on_supervisor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle logic when on Supervisor host."""
        if user_input is None:
            return self.async_show_form(step_id="on_supervisor", data_schema=ON_SUPERVISOR_SCHEMA)
        if not user_input[CONF_USE_ADDON]:
            return await self.async_step_manual()

        self.use_addon = True
        await install_repository(self.hass)
        addon_info = await self._async_get_addon_info()

        if addon_info.state == AddonState.RUNNING:
            return await self.async_step_finish_addon_setup()

        if addon_info.state == AddonState.NOT_RUNNING:
            return await self.async_step_start_addon()

        return await self.async_step_install_addon()

    async def async_step_finish_addon_setup(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Prepare info needed to complete the config entry."""
        if not self.server_info:
            # Check that we can connect to the address.
            try:
                self.server_info = await get_server_info(self.hass, ADDON_URL)
            except CannotConnect:
                return self.async_abort(reason="cannot_connect")
        if user_input is not None:
            self.openai_agent_id = user_input[CONF_OPENAI_AGENT_ID]
            self.expose_players_assist = user_input[CONF_ASSIST_AUTO_EXPOSE_PLAYERS]
        return await self._async_create_entry_or_abort()

    async def _async_create_entry_or_abort(self) -> FlowResult:
        """Return a config entry for the flow or abort if already configured."""
        assert self.server_info is not None

        for config_entry in self._async_current_entries():
            if config_entry.unique_id != self.server_info.server_id:
                continue
            self.hass.config_entries.async_update_entry(
                config_entry,
                data={
                    **config_entry.data,
                    CONF_URL: self.server_info.base_url,
                    CONF_USE_ADDON: self.use_addon,
                    CONF_INTEGRATION_CREATED_ADDON: self.integration_created_addon,
                    CONF_OPENAI_AGENT_ID: self.openai_agent_id,
                    CONF_ASSIST_AUTO_EXPOSE_PLAYERS: self.expose_players_assist,
                },
                title=DEFAULT_TITLE,
            )
            await self.hass.config_entries.async_reload(config_entry.entry_id)
            raise AbortFlow("reconfiguration_successful")

        # Abort any other flows that may be in progress
        for progress in self._async_in_progress():
            self.hass.config_entries.flow.async_abort(progress["flow_id"])

        return self.async_create_entry(
            title=DEFAULT_TITLE,
            data={
                CONF_URL: self.server_info.base_url,
                CONF_USE_ADDON: self.use_addon,
                CONF_INTEGRATION_CREATED_ADDON: self.integration_created_addon,
                CONF_OPENAI_AGENT_ID: self.openai_agent_id,
                CONF_ASSIST_AUTO_EXPOSE_PLAYERS: self.expose_players_assist,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Class to handle options flow."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None) -> FlowResult:
        """Manage the options."""
        LOGGER.debug(
            "OptionsFlowHandler:async_step_init user_input [%s] data [%s]",
            user_input,
            self.config_entry.data,
        )
        if user_input is not None:
            if CONF_USE_ADDON in self.config_entry.data:
                user_input[CONF_USE_ADDON] = self.config_entry.data[CONF_USE_ADDON]
            if CONF_INTEGRATION_CREATED_ADDON in self.config_entry.data:
                user_input[CONF_INTEGRATION_CREATED_ADDON] = self.config_entry.data[
                    CONF_INTEGRATION_CREATED_ADDON
                ]

            self.hass.config_entries.async_update_entry(
                self.config_entry, data=user_input, options=self.config_entry.options
            )
            await self.hass.config_entries.async_reload(self.config_entry.entry_id)
            return self.async_create_entry(title="", data={})

        schema = self.mass_config_option_schema(self.config_entry)
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(schema),
        )

    def mass_config_option_schema(self, config_entry: config_entries.ConfigEntry) -> vol.Schema:
        """Return a schema for MusicAssistant completion options."""
        return {
            vol.Required(
                CONF_URL,
                default=config_entry.data.get(CONF_URL),
            ): str,
            vol.Optional(
                CONF_OPENAI_AGENT_ID,
                default=config_entry.data.get(CONF_OPENAI_AGENT_ID),
            ): selector.ConversationAgentSelector(
                selector.ConversationAgentSelectorConfig(language="en")
            ),
            vol.Optional(
                CONF_ASSIST_AUTO_EXPOSE_PLAYERS,
                default=config_entry.data.get(CONF_ASSIST_AUTO_EXPOSE_PLAYERS)
                if config_entry.data.get(CONF_ASSIST_AUTO_EXPOSE_PLAYERS) is not None
                else False,
            ): bool,
        }


class FailedConnect(HomeAssistantError):
    """Failed to connect to the MusicAssistant Server."""
