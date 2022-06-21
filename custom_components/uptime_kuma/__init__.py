"""The Uptime Kuma integration."""
from datetime import timedelta
import logging

import async_timeout
from uptime_kuma_monitor import UptimeKumaMonitor

from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import update_coordinator

from .const import DOMAIN

LOGGER = logging.getLogger(__name__)

PLATFORMS = [BINARY_SENSOR_DOMAIN]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Uptime Kuma integration."""

    async def async_get_uptime_kuma_data():
        with async_timeout.timeout(10):
            utkm = await hass.async_add_executor_job(
                UptimeKumaMonitor,
                f"{entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}",
                entry.data[CONF_USERNAME],
                entry.data[CONF_PASSWORD],
                entry.data[CONF_VERIFY_SSL],
            )
            return utkm.data

    coordinator = update_coordinator.DataUpdateCoordinator(
        hass,
        LOGGER,
        name=DOMAIN,
        update_method=async_get_uptime_kuma_data,
        update_interval=timedelta(minutes=1),
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN] = coordinator

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        del hass.data[DOMAIN]

    return unload_ok
