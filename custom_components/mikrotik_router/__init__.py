"""Mikrotik Router integration."""

import logging
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.exceptions import ConfigEntryNotReady
from .const import (
    DOMAIN,
    DATA_CLIENT,
    RUN_SCRIPT_COMMAND,
)
from .mikrotik_controller import MikrotikControllerData

_LOGGER = logging.getLogger(__name__)

SCRIPT_SCHEMA = vol.Schema(
    {vol.Required("router"): cv.string, vol.Required("script"): cv.string}
)


# ---------------------------
#   async_setup
# ---------------------------
async def async_setup(hass, _config):
    """Set up configured Mikrotik Controller."""
    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][DATA_CLIENT] = {}
    return True


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(hass, config_entry):
    """Set up Mikrotik Router as config entry."""
    controller = MikrotikControllerData(hass, config_entry)
    await controller.async_hwinfo_update()

    await controller.async_update()

    if not controller.data:
        raise ConfigEntryNotReady()

    await controller.async_init()
    hass.data[DOMAIN][DATA_CLIENT][config_entry.entry_id] = controller

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "sensor")
    )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "binary_sensor")
    )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "device_tracker")
    )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, "switch")
    )

    hass.services.async_register(
        DOMAIN, RUN_SCRIPT_COMMAND, controller.run_script, schema=SCRIPT_SCHEMA
    )

    device_registry = await hass.helpers.device_registry.async_get_registry()
    device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        manufacturer=controller.data["resource"]["platform"],
        model=controller.data["routerboard"]["model"],
        name=controller.data["routerboard"]["model"],
        sw_version=controller.data["resource"]["version"],
    )

    return True


# ---------------------------
#   async_unload_entry
# ---------------------------
async def async_unload_entry(hass, config_entry):
    """Unload a config entry."""
    controller = hass.data[DOMAIN][DATA_CLIENT][config_entry.entry_id]
    await hass.config_entries.async_forward_entry_unload(config_entry, "sensor")
    await hass.config_entries.async_forward_entry_unload(config_entry, "binary_sensor")
    await hass.config_entries.async_forward_entry_unload(config_entry, "device_tracker")
    await hass.config_entries.async_forward_entry_unload(config_entry, "switch")
    hass.services.async_remove(DOMAIN, RUN_SCRIPT_COMMAND)
    await controller.async_reset()
    hass.data[DOMAIN][DATA_CLIENT].pop(config_entry.entry_id)
    return True
