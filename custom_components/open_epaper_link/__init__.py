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
    """Set up OpenEPaperLink integration from a config entry.

    This is the main entry point for integration initialization, which:

    1. Creates and initializes the Hub instance
    2. Stores the Hub in hass.data for component-wide access
    3. Sets up entity platforms (sensor, button, etc.)
    4. Registers service handlers
    5. Starts the WebSocket connection to the AP

    The WebSocket connection is started after Home Assistant is fully loaded
    to avoid blocking startup with network operations.

    Args:
        hass: Home Assistant instance
        entry: Configuration Entry object with connection details

    Returns:
        bool: True if setup was successful, False otherwise
    """
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

    async def start_websocket(_):
        """Start WebSocket connection after HA is fully started.

        Delayed startup of the WebSocket connection to ensure
        Home Assistant is fully initialized and ready to handle
        entity updates that might result from incoming data.

        Args:
            _: Event object (unused)
        """
        await hub.async_start_websocket()

    if hass.is_running:
        # If HA is already running, start WebSocket immediately
        await hub.async_start_websocket()
    else:
        # Otherwise wait for the started event
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, start_websocket)

    return True

async def async_update_options(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle updates to integration options.

    Called when the user updates integration options through the UI.
    Reloads configuration settings such as:

    - Tag blacklist
    - Button/NFC debounce intervals
    - Font directories

    Args:
        hass: Home Assistant instance
        entry: Updated configuration entry
    """
    hub = hass.data[DOMAIN][entry.entry_id]
    await hub.async_reload_config()

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload the integration when removed or restarted.

    Performs cleanup operations including:

    1. Unloading entity platforms
    2. Shutting down the Hub (closes WebSocket connection)
    3. Unregistering service handlers
    4. Removing the Hub from hass.data

    Args:
        hass: Home Assistant instance
        entry: Configuration entry being unloaded

    Returns:
        bool: True if unload was successful, False otherwise
    """
    hub = hass.data[DOMAIN][entry.entry_id]

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        await hub.shutdown()
        await async_unload_services(hass)
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle complete removal of integration.

    Called when the integration is completely removed from Home Assistant
    (not during restarts). Performs cleanup of persistent storage files.

    Args:
        hass: Home Assistant instance
        entry: Configuration entry being removed
    """
    await async_remove_storage_files(hass)

async def async_remove_storage_files(hass: HomeAssistant) -> None:
    """Remove persistent storage files when removing integration.

    Cleans up files created by the integration:

    1. Tag types file (open_epaper_link_tagtypes.json)
    2. Tag storage file (.storage/open_epaper_link_tags)
    3. Image directory (www/open_epaper_link)

    This prevents orphaned files when the integration is removed
    and ensures a clean reinstallation if needed.

    Args:
        hass: Home Assistant instance
    """

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