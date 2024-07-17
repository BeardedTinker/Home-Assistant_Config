"""The Growcube integration."""
import asyncio
import logging
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_HOST, Platform
from .coordinator import GrowcubeDataCoordinator
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry

_LOGGER = logging.getLogger(__name__)

from .const import *
from .services import async_setup_services

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR, Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: dict):
    """Set up the Growcube entry."""
    hass.data.setdefault(DOMAIN, {})

    host_name = entry.data[CONF_HOST]
    data_coordinator = GrowcubeDataCoordinator(host_name, hass)
    try:
        await data_coordinator.connect()
        hass.data[DOMAIN][entry.entry_id] = data_coordinator

        # Wait for device to report id
        retries = 3
        while not data_coordinator.device_id and retries > 0:
            retries -= 1
            await asyncio.sleep(0.5)

        if retries == 0:
            _LOGGER.error(
                "Unable to read device id of %s, device is probably connected to another app",
                host_name
            )
            return False

    except asyncio.TimeoutError:
        _LOGGER.error(
            "Connection to %s timed out",
            host_name
        )
        return False
    except OSError:
        _LOGGER.error(
            "Unable to connect to host %s",
            host_name
        )
        return False

    registry = device_registry.async_get(hass)
    device_entry = registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, data_coordinator.data.device_id)},
        name=f"GrowCube " + data_coordinator.device_id,
        manufacturer="Elecrow",
        model="GrowCube",
        sw_version=data_coordinator.data.version
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await async_setup_services(hass)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: dict):
    """Unload the Growcube entry."""
    client = hass.data[DOMAIN][entry.entry_id]
    client.disconnect()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok




