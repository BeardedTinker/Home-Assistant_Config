"""Provides random jokes."""

from .const import DOMAIN
import aiohttp
import asyncio
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback, HomeAssistant
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
import logging

_LOGGER = logging.getLogger(__name__)

# def set_joke(hass: HomeAssistant, text: str):
#     """Helper function to set the random joke."""
#     _LOGGER.debug("set_joke")
#     hass.states.async_set("jokes.random_joke", text)

def setup(hass: HomeAssistant, config: dict):
    """This setup does nothing, we use the async setup."""
    _LOGGER.debug("setup")
    return True

async def async_setup(hass: HomeAssistant, config: dict):
    """Setup from configuration.yaml."""
    _LOGGER.debug("async_setup")
    
    #`config` is the full dict from `configuration.yaml`.
    #set_joke(hass, "")

    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Setup from Config Flow Result."""
    _LOGGER.debug("async_setup_entry")
    
    coordinator = JokeUpdateCoordinator(
        hass,
        _LOGGER,
        update_interval=timedelta(seconds=60)
    )
    await coordinator.async_refresh()
    
    hass.data[DOMAIN] = {
        "coordinator": coordinator
    }
    
    hass.async_create_task(async_load_platform(hass, "sensor", DOMAIN, {}, entry))
    return True

class JokeUpdateCoordinator(DataUpdateCoordinator):
    """Update handler."""

    def __init__(self, hass, logger, update_interval=None):
        """Initialize global data updater."""
        logger.debug("__init__")

        super().__init__(
            hass,
            logger,
            name=DOMAIN,
            update_interval=update_interval,
            update_method=self._async_update_data,
        )
        
    async def _async_update_data(self):
        """Fetch a random joke."""
        self.logger.debug("_async_update_data")
        
        #get a random joke (finally)
        try:
            headers = {
                'Accept': 'application/json',
                'User-Agent': 'Jokes custom integration for Home Assistant (https://github.com/LaggAt/ha-jokes)'
            }
            async with aiohttp.ClientSession() as session:
                async with session.get('https://icanhazdadjoke.com/', headers=headers) as resp:
                    if resp.status == 200:
                        json = await resp.json()
                        #set_joke(self._hass, json["joke"])
                        # return the joke object
                        return json
                    else:
                        raise UpdateFailed(f"Response status code: {resp.status}")
        except Exception as ex:
            raise UpdateFailed from ex
