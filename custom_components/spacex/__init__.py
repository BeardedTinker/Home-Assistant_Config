"""The SpaceX integration."""
import asyncio
from datetime import timedelta
import logging

from spacexpypi import SpaceX
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import COORDINATOR, DOMAIN, SPACEX_API

CONFIG_SCHEMA = vol.Schema({DOMAIN: vol.Schema({})}, extra=vol.ALLOW_EXTRA)
_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["binary_sensor", "sensor"]


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the SpaceX component."""
    hass.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up SpaceX from a config entry."""
    polling_interval = 25
    api = SpaceX()

    try:
        await api.get_next_launch()
    except ConnectionError as error:
        _LOGGER.debug("SpaceX API Error: %s", error)
        return False
        raise ConfigEntryNotReady from error
    except ValueError as error:
        _LOGGER.debug("SpaceX API Error: %s", error)
        return False
        raise ConfigEntryNotReady from error

    coordinator = SpaceXUpdateCoordinator(
        hass,
        api=api,
        name="SpaceX",
        polling_interval=polling_interval,
    )

    await coordinator.async_refresh()

    if not coordinator.last_update_success:
        raise ConfigEntryNotReady

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

class SpaceXUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching update data from the SpaceX endpoint."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: str,
        name: str,
        polling_interval: int,
    ):
        """Initialize the global SpaceX data updater."""
        self.api = api

        super().__init__(
            hass = hass,
            logger = _LOGGER,
            name = name,
            update_interval = timedelta(seconds=polling_interval),
        )

    async def _async_update_data(self):
        """Fetch data from SpaceX."""
        try:
            _LOGGER.debug("Updating the coordinator data.")
            spacex_starman = await self.api.get_roadster_status()
            spacex_next_launch = await self.api.get_next_launch()
            spacex_latest_launch = await self.api.get_latest_launch()

            return {
                "starman": spacex_starman,
                "next_launch": spacex_next_launch,
                "latest_launch": spacex_latest_launch,
            }
        except ConnectionError as error:
            _LOGGER.info("SpaceX API: %s", error)
            raise UpdateFailed from error
        except ValueError as error:
            _LOGGER.info("SpaceX API: %s", error)
            raise UpdateFailed from error

        

