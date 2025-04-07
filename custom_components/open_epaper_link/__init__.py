import logging
import os
from typing import Final

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, EVENT_HOMEASSISTANT_STARTED
from homeassistant.core import HomeAssistant
from .const import DOMAIN
from .hub import Hub
from .services import async_setup_services, async_unload_services
_LOGGER: Final = logging.getLogger(__name__)

PLATFORMS = [
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.CAMERA,
    Platform.SELECT,
    Platform.SWITCH,
    Platform.TEXT,
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up OpenEPaperLink from a config entry."""
    hub = Hub(hass, entry)

    # Do basic setup without WebSocket connection
    if not await hub.async_setup_initial():
        return False

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Set up services
    await async_setup_services(hass)

    # Listen for changes to options
    entry.async_on_unload(entry.add_update_listener(async_update_options))

    # Create an async task to start the WebSocket after HA is fully started
    async def start_websocket(_):
        """Start WebSocket connection after HA is fully started."""
        await hub.async_start_websocket()

    if hass.is_running:
        # If HA is already running, start WebSocket immediately
        await hub.async_start_websocket()
    else:
        # Otherwise wait for the started event
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, start_websocket)

    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update options."""
    hub = hass.data[DOMAIN][entry.entry_id]
    await hub.async_reload_config()

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hub = hass.data[DOMAIN][entry.entry_id]

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        await hub.shutdown()
        await async_unload_services(hass)
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle removal of an entry."""
    # This is called only when the integration is removed, not during restarts
    await async_remove_storage_files(hass)

async def async_remove_storage_files(hass: HomeAssistant) -> None:
    """Remove storage files when removing integration."""

    # Remove tag types file
    tag_types_file = hass.config.path("open_epaper_link_tagtypes.json")
    if await hass.async_add_executor_job(os.path.exists, tag_types_file):
        try:
            await hass.async_add_executor_job(os.remove, tag_types_file)
            _LOGGER.debug("Removed tag types file")
        except OSError as err:
            _LOGGER.error("Error removing tag types file: %s", err)

    # Remove tag storage file
    storage_dir = hass.config.path(".storage")
    tags_file = os.path.join(storage_dir, f"{DOMAIN}_tags")
    if await hass.async_add_executor_job(os.path.exists, tags_file):
        try:
            await hass.async_add_executor_job(os.remove, tags_file)
            _LOGGER.debug("Removed tag storage file")
        except OSError as err:
            _LOGGER.error("Error removing tag storage file: %s", err)

    # Remove image directory
    image_dir = hass.config.path("www/open_epaper_link")
    if await hass.async_add_executor_job(os.path.exists, image_dir):
        try:
            # Get file list in executor
            files = await hass.async_add_executor_job(os.listdir, image_dir)

            # Remove each file in executor
            for file in files:
                file_path = os.path.join(image_dir, file)
                await hass.async_add_executor_job(os.remove, file_path)

            # Remove directory in executor
            await hass.async_add_executor_job(os.rmdir, image_dir)
            _LOGGER.debug("Removed image directory")
        except OSError as err:
            _LOGGER.error("Error removing image directory: %s", err)