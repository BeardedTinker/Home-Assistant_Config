"""The SpaceX integration."""
import asyncio
from datetime import timedelta
import logging

from spacexpypi import SpaceX
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady, PlatformNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import COORDINATOR, DOMAIN, SPACEX_API

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)
_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["binary_sensor", "sensor"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the SpaceX component."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up SpaceX from a config entry."""
    polling_interval = 5
    api = SpaceX()

    async def async_update_data():
        """Fetch data from API endpoint."""
        _LOGGER.debug("Updating the coordinator data.")

        try:
            spacex_starman = await api.get_roadster_status()
        except ConnectionError as e:
            _LOGGER.info("SpaceX API: %s", e)
            raise PlatformNotReady

        try:
            spacex_next_launch = await api.get_next_launch()
        except ConnectionError as e:
            _LOGGER.info("SpaceX API: %s", e)
            raise PlatformNotReady

        try:
            spacex_latest_launch = await api.get_latest_launch()
        except ConnectionError as e:
            _LOGGER.info("SpaceX API: %s", e)
            raise PlatformNotReady

        return [
            spacex_starman,
            spacex_next_launch,
            spacex_latest_launch,
        ]

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="SpaceX",
        update_method=async_update_data,
        update_interval=timedelta(seconds=polling_interval),
    )

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {COORDINATOR: coordinator, SPACEX_API: api}

    for component in PLATFORMS:
        _LOGGER.info("Setting up platform: %s", component)
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
