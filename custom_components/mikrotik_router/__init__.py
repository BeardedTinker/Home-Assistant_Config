"""Mikrotik Router integration."""

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    PLATFORMS,
    DOMAIN,
    RUN_SCRIPT_COMMAND,
)
from .mikrotik_controller import MikrotikControllerData

SCRIPT_SCHEMA = vol.Schema(
    {vol.Required("router"): cv.string, vol.Required("script"): cv.string}
)


# ---------------------------
#   async_setup
# ---------------------------
async def async_setup(hass, _config):
    """Set up configured Mikrotik Controller."""
    hass.data[DOMAIN] = {}
    return True


# ---------------------------
#   update_listener
# ---------------------------
async def update_listener(hass, config_entry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(config_entry.entry_id)


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(hass, config_entry) -> bool:
    """Set up Mikrotik Router as config entry."""
    controller = MikrotikControllerData(hass, config_entry)
    await controller.async_hwinfo_update()
    if not controller.connected():
        raise ConfigEntryNotReady(f"Cannot connect to host")

    await controller.async_update()

    if not controller.data:
        raise ConfigEntryNotReady()

    await controller.async_init()
    hass.data[DOMAIN][config_entry.entry_id] = controller

    hass.config_entries.async_setup_platforms(config_entry, PLATFORMS)
    config_entry.async_on_unload(config_entry.add_update_listener(update_listener))

    hass.services.async_register(
        DOMAIN, RUN_SCRIPT_COMMAND, controller.run_script, schema=SCRIPT_SCHEMA
    )

    return True


# ---------------------------
#   async_unload_entry
# ---------------------------
async def async_unload_entry(hass, config_entry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    if unload_ok:
        controller = hass.data[DOMAIN][config_entry.entry_id]
        await controller.async_reset()
        hass.services.async_remove(DOMAIN, RUN_SCRIPT_COMMAND)
        hass.data[DOMAIN].pop(config_entry.entry_id)

    return unload_ok
