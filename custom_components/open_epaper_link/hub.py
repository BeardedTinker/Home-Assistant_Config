import asyncio
from datetime import datetime, timedelta
from typing import Final, Dict

import json
import requests
import aiohttp
import async_timeout
import websockets
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.core import HomeAssistant, CALLBACK_TYPE, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.storage import Store
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
import logging

_LOGGER: Final = logging.getLogger(__name__)

from .const import DOMAIN, SIGNAL_AP_UPDATE, SIGNAL_TAG_UPDATE, SIGNAL_TAG_IMAGE_UPDATE
from .tag_types import get_tag_types_manager, get_hw_string

STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}_tags"
RECONNECT_INTERVAL = 30
SAVE_DELAY = 10
WEBSOCKET_TIMEOUT = 60
CONNECTION_TIMEOUT = 10




class Hub:
    """Central communication manager for OpenEPaperLink integration.

    This class manages all interaction with the OpenEPaperLink Access Point (AP),
    including:

    - WebSocket connection for real-time updates
    - Tag data management and state tracking
    - AP configuration and status monitoring
    - Event handling for tag interactions (buttons, NFC)
    - Persistent storage of tag data

    The Hub maintains the primary state for all tags and the AP itself,
    serving as the data source for all entities in the integration.

    Attributes:
        hass: Home Assistant instance
        entry: Config entry containing connection details
        host: Hostname or IP of the OpenEPaperLink AP
        online: Boolean indicating if the AP is currently connected
        tags: List of known tag MAC addresses
        ap_config: Dictionary of current AP configuration settings
        ap_status: Dictionary of current AP status information
    """
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Handle WebSocket connection and process incoming messages.

        Manages the lifecycle of the WebSocket connection, including:

        - Establishing initial connection to the AP
        - Processing incoming messages (tag updates, AP status, etc.)
        - Handling connection errors and implementing reconnection logic
        - Broadcasting connection state changes to entities

        This is a long-running task that continues until shutdown is triggered.
        When connection errors occur, it implements a reconnection strategy
        with a fixed interval defined by RECONNECT_INTERVAL.

        Raises:
            No exceptions are raised as they are caught and logged internally.
        """
        self.hass = hass
        self.entry = entry
        self.host = entry.data["host"]
        self._ws_task: asyncio.Task | None = None
        self._ws_client: websockets.WebSocketClientProtocol | None = None
        self._cleanup_task: asyncio.Task | None = None
        self._shutdown = asyncio.Event()
        self._session = async_get_clientsession(hass)
        self._shutdown_handler: CALLBACK_TYPE | None = None
        self._shutdown = asyncio.Event()
        self._store = Store[dict[str, any]](
            hass, STORAGE_VERSION, STORAGE_KEY, private=True, atomic_writes=True
        )
        self._data: dict[str, dict] = {}
        self._ap_data: dict[str, any] = {}
        self.ap_config: dict[str, any] = {}
        self._known_tags: set[str] = set()
        self._last_record_count = None
        self.ap_env = None
        self.ap_model = "ESP32"

        self._unsub_callbacks: list[CALLBACK_TYPE] = []
        self.online = False
        self._reconnect_task: asyncio.Task | None = None
        self._tag_manager = None
        self._tag_manager_ready = asyncio.Event()
        self._blacklisted_tags = entry.options.get("blacklisted_tags", [])
        self._last_button_press: Dict[str, datetime] = {}
        self._button_debounce_interval = timedelta(seconds=0.5)
        self._nfc_last_scan: Dict[str, datetime] = {}
        self._nfc_debounce_interval = timedelta(seconds=1)
        self._update_debounce_interval()

    def _update_debounce_interval(self) -> None:
        """Update event debounce intervals from integration options.

        Reads the button_debounce and nfc_debounce values from the
        integration's configuration options and updates the internal
        debounce interval time deltas accordingly.

        This prevents rapid duplicate events from buttons or NFC scans
        by setting minimum time intervals between consecutive events.
        """
        button_debounce_seconds = self.entry.options.get("button_debounce", 0.5)
        nfc_debounce_seconds = self.entry.options.get("nfc_debounce", 1.0)
        self._button_debounce_interval = timedelta(seconds=button_debounce_seconds)
        self._nfc_debounce_interval = timedelta(seconds=nfc_debounce_seconds)

    async def async_reload_config(self) -> None:
        """Reload configuration from config entry.

        Updates hub settings based on changes to the config entry options:

        - Reloads the tag blacklist
        - Updates debounce intervals for buttons and NFC

        This is called when the integration options are updated through
        the configuration flow.
        """
        await self.async_reload_blacklist()
        self._update_debounce_interval()

    async def async_setup_initial(self) -> bool:
        """Set up hub without establishing a WebSocket connection.

        Performs the initial setup tasks:

        - Loads stored tag data from persistent storage
        - Initializes the tag type manager
        - Registers the shutdown handler
        - Attempts to load initial tag data from the AP

        This is called during integration setup before the platforms
        are loaded, allowing entities to be created with initial state.

        Returns:
            bool: True if setup completed successfully, False otherwise
        """
        try:
            # Load stored data
            stored = await self._store.async_load()
            if stored:
                self._data = stored.get("tags", {})
                self._known_tags = set(self._data.keys())
                _LOGGER.debug("Restored %d tags from storage", len(self._known_tags))

            # Initialize tag manager
            self._tag_manager = await get_tag_types_manager(self.hass)
            self._tag_manager_ready.set()

            # Register shutdown handler only once
            if self._shutdown_handler is None:
                self._shutdown_handler = self.hass.bus.async_listen_once(
                    EVENT_HOMEASSISTANT_STOP,
                    self._handle_shutdown
                )

            # Fetch AP env
            try:
                await self.async_update_ap_info()
            except Exception as err:
                _LOGGER.warning("Could not load initial AP info: %s", str(err))

            # Load all tags from AP
            try:
                await self.async_load_all_tags()
            except Exception as err:
                _LOGGER.warning("Could not load initial tags from AP: %s", str(err))
            return True

        except Exception as err:
            _LOGGER.error("Failed to set up hub: %s", err)
            return False

    async def async_start_websocket(self) -> bool:
        """Start WebSocket connection to the AP.

        Establishes the WebSocket connection for real-time updates from the AP.
        If a previous connection exists, it's cancelled before starting a new one.

        The method waits for the connection to be established or for the
        CONNECTION_TIMEOUT to expire before returning.

        Returns:
            bool: True if connection was successfully established, False otherwise
        """
        if self._ws_task and not self._ws_task.done():
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass

        # Clear the shutdown flag when starting
        self._shutdown.clear()

        self._ws_task = self.hass.async_create_task(
            self._websocket_handler(),
            "open_epaper_link_websocket"
        )

        # Wait briefly to ensure connection is established
        try:
            async with async_timeout.timeout(CONNECTION_TIMEOUT):
                while not self.online and not self._shutdown.is_set():
                    await asyncio.sleep(0.1)

                if not self.online:
                    _LOGGER.error("Failed to establish WebSocket connection")
                    return False

                _LOGGER.info("WebSocket connection established successfully")
                return True

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout while establishing WebSocket connection")
            return False


    async def _handle_shutdown(self, _) -> None:
        """Handle Home Assistant shutdown event.

        Called when Home Assistant is shutting down, this method:

        - Triggers a clean shutdown of the Hub
        - Clears the shutdown handler reference

        Args:
            _: Event object (unused)
        """
        _LOGGER.debug("Processing shutdown for OpenEPaperLink hub")
        await self.shutdown()
        self._shutdown_handler = None

    async def shutdown(self) -> None:
        """Shut down the hub and clean up resources.

        Performs a graceful shutdown of the hub:

        - Sets shutdown flag to prevent new connection attempts
        - Cancels any active WebSocket connection task
        - Removes event listeners and callbacks
        - Updates connection status for dependent entities

        This should be called when unloading the integration.
        """
        _LOGGER.debug("Shutting down OpenEPaperLink hub")

        # Set shutdown flag first
        self._shutdown.set()

        # Cancel WebSocket task
        if self._ws_task and not self._ws_task.done():
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass

        # Clean up other callbacks
        while self._unsub_callbacks:
            try:
                unsub = self._unsub_callbacks.pop()
                unsub()
            except Exception as err:
                _LOGGER.debug("Error cleaning up callback: %s", err)

        # Mark as offline
        self.online = False
        async_dispatcher_send(self.hass, f"{DOMAIN}_connection_status", False)

        _LOGGER.debug("OpenEPaperLink hub shutdown complete")

    async def _websocket_handler(self) -> None:
        """Handle WebSocket connection lifecycle and process messages.

         This is a long-running task that manages all aspects of the WebSocket
         connection to the OpenEPaperLink Access Point, including:

         - Establishing and maintaining the connection
         - Processing incoming real-time messages from the AP
         - Detecting connection failures and implementing reconnection logic
         - Broadcasting connection state changes to dependent entities

         The handler implements error resilience through nested try/except blocks:

         - Outer block: Handles connection establishment and reconnection
         - Inner block: Processes individual messages within an active connection

         When connection errors occur, the handler waits for RECONNECT_INTERVAL
         seconds before attempting to reconnect, continuing until the hub
         shutdown is signaled via the self._shutdown Event.

         Note: This method should be run as a background task and not awaited
         directly, as it runs indefinitely until shutdown is triggered.
         """
        while not self._shutdown.is_set():
            try:
                ws_url = f"ws://{self.host}/ws"
                async with self._session.ws_connect(ws_url, heartbeat=30) as ws:
                    self.online = True
                    _LOGGER.debug("Connected to websocket at %s", ws_url)
                    async_dispatcher_send(self.hass, f"{DOMAIN}_connection_status", True)

                    # Run verification on each connection to catch deletions that happened while offline
                    await self._verify_and_cleanup_tags()

                    while not self._shutdown.is_set():
                        try:
                            msg = await ws.receive()

                            if msg.type == aiohttp.WSMsgType.TEXT:
                                await self._handle_message(msg.data)
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                _LOGGER.info("WebSocket error: %s", ws)
                                break
                            elif msg.type == aiohttp.WSMsgType.CLOSING:
                                _LOGGER.debug("WebSocket closing")
                                break
                            elif msg.type == aiohttp.WSMsgType.CLOSED:
                                _LOGGER.debug("WebSocket closed")
                                break
                        except asyncio.CancelledError:
                            _LOGGER.debug("WebSocket task cancelled")
                            raise
                        except Exception as err:
                            _LOGGER.error("Error handling message: %s", err)

            except asyncio.CancelledError:
                _LOGGER.debug("WebSocket connection cancelled")
                raise
            except aiohttp.ClientError as err:
                self.online = False
                _LOGGER.error("WebSocket connection error: %s", err)
                async_dispatcher_send(self.hass, f"{DOMAIN}_connection_status", False)
            except Exception as err:
                self.online = False
                _LOGGER.error("Unexpected WebSocket error: %s", err)
                async_dispatcher_send(self.hass, f"{DOMAIN}_connection_status", False)

            if not self._shutdown.is_set():
                await asyncio.sleep(RECONNECT_INTERVAL)


    def _schedule_reconnect(self) -> None:
        """Schedule a WebSocket reconnection attempt.

        Creates a task to reconnect after RECONNECT_INTERVAL seconds.
        If a reconnection task is already scheduled, it's cancelled first
        to avoid multiple concurrent reconnection attempts.
        """
        async def reconnect():
            await asyncio.sleep(RECONNECT_INTERVAL)
            if not self._shutdown.is_set():
                self._ws_task = self.hass.async_create_task(
                    self._websocket_handler(),
                    f"{DOMAIN}_websocket",
                )

        if self._reconnect_task and not self._reconnect_task.done():
            self._reconnect_task.cancel()

        self._reconnect_task = self.hass.async_create_task(
            reconnect(),
            f"{DOMAIN}_reconnect",
        )

    async def _handle_message(self, message: str) -> None:
        """Process an incoming WebSocket message from the AP.

        Parses the message JSON and routes it to the appropriate handler
        based on the message type:

        - "sys" messages: AP system status updates
        - "tags" messages: Individual tag status updates
        - "logMsg" messages: Log information from the AP
        - "errMsg" messages: Error notifications
        - "apitem" messages: Configuration change notifications

        Args:
            message: Raw WebSocket message string from the AP

        Raises:
            No exceptions are raised as they are caught and logged internally.
        """
        try:
            data = json.loads("{" + message.split("{", 1)[-1])

            if "sys" in data:
                _LOGGER.debug("System message: %s", data["sys"])
                await self._handle_system_message(data["sys"])
            elif "tags" in data:
                _LOGGER.debug("Tag message: %s", data["tags"][0])
                await self._handle_tag_message(data["tags"][0])
            elif "logMsg" in data:
                _LOGGER.debug("OEPL Log message: %s", data["logMsg"])
                await self._handle_log_message(data["logMsg"])
            elif "errMsg" in data and data["errMsg"] == "REBOOTING":
                _LOGGER.debug("AP is rebooting")
                self._ap_data["ap_state"] = "Offline"
                async_dispatcher_send(self.hass, SIGNAL_AP_UPDATE)
                self.online = False
                async_dispatcher_send(self.hass, f"{DOMAIN}_connection_status", False)

                # Close WebSocket connection immediately
                if self._ws_task and not self._ws_task.done():
                    self._ws_task.cancel()

                # Schedule reconnection attempt after brief delay
                async def delayed_reconnect():
                    await asyncio.sleep(5)
                    if not self._shutdown.is_set():
                        self._ws_task = self.hass.async_create_task(
                            self._websocket_handler(),
                            f"{DOMAIN}_websocket"
                        )

                self.hass.async_create_task(delayed_reconnect(), f"{DOMAIN}_reconnect")
                return
            elif "apitem" in data:
                # Check if this is actually a config change message
                if data.get("apitem", {}).get("type") == "change":
                    await self._handle_ap_config_message(data)
                else:
                    _LOGGER.debug("Ignoring non-change AP message")
            else:
                _LOGGER.debug("Unknown message type: %s", data)

        except json.JSONDecodeError:
            _LOGGER.error("Failed to decode message: %s", message)
        except Exception as err:
            _LOGGER.exception("Error handling message: %s", err)

    @callback
    async def _handle_system_message(self, sys_data: dict) -> None:
        """Process a system message from the AP.

        Updates the AP status information based on system data, including:

        - IP address and Wi-Fi settings
        - Memory usage (heap, database size)
        - Tag counts and AP state
        - Runtime information

        This method is called when the AP sends a "sys" WebSocket message,
        which typically happens periodically or after state changes.

        Args:
            sys_data: Dictionary containing AP system status information
        """

        # Preserve existing values for fields that are not in every message
        current_low_batt = self._ap_data.get("low_battery_count", 0)
        current_timeout = self._ap_data.get("timeout_count", 0)

        self._ap_data = {
            "ip": self.host,
            "sys_time": sys_data.get("currtime"),
            "heap": sys_data.get("heap"),
            "record_count": sys_data.get("recordcount"),
            "db_size": sys_data.get("dbsize"),
            "little_fs_free": sys_data.get("littlefsfree"),
            "ps_ram_free": sys_data.get("psfree"),
            "rssi": sys_data.get("rssi"),
            "ap_state": self._get_ap_state_string(sys_data.get("apstate")),
            "run_state": self._get_ap_run_state_string(sys_data.get("runstate")),
            "temp": sys_data.get("temp"),
            "wifi_status": sys_data.get("wifistatus"),
            "wifi_ssid": sys_data.get("wifissid"),
            "uptime": sys_data.get("uptime"),
            "low_battery_count": sys_data.get("lowbattcount", current_low_batt),
            "timeout_count": sys_data.get("timeoutcount", current_timeout),
        }

        if "recordcount" in sys_data:
            self._track_record_count_changes(sys_data.get("recordcount", 0))

        async_dispatcher_send(self.hass, SIGNAL_AP_UPDATE)

    @callback
    async def _handle_tag_message(self, tag_data: dict) -> None:
        """Process a tag update message from the AP.

        Updates the stored information for a specific tag based on the
        data received from the AP. This includes:

        - Tag status (battery, temperature, etc.)
        - Scheduling information (next update, next check-in)
        - Signal quality information (RSSI, LQI)

        Args:
            tag_data: Dictionary containing tag properties from the AP
        """
        tag_mac = tag_data.get("mac")
        if not tag_mac:
            return

        # Process tag data
        is_new_tag = await self._process_tag_data(tag_mac, tag_data)
        # Save to storage if this was a new tag
        if is_new_tag:
            await self._store.async_save({"tags": self._data})
        else:
            # Schedule a save with a delay to avoid constant writes
            # Will be implemented in the future
            await self._store.async_save({"tags": self._data})


    async def _handle_log_message(self, log_msg: str) -> None:
        """Process a log message from the AP.

        Parses log messages for specific events that require action:
        - Block transfer requests: Updates the block_requests counter
        - Transfer completion: Triggers image update notification

        Args:
            log_msg: Raw log message string from the AP
        """
        if "block request" in log_msg:
            # Extract MAC address from block request message
            # Example: "0000000000123456 block request /current/0000000000123456_452783.pending block 0"
            parts = log_msg.split()
            if len(parts) > 0:
                tag_mac = parts[0].upper()
                if tag_mac in self._data:
                    block_requests = self._data[tag_mac].get("block_requests", 0) + 1
                    self._data[tag_mac]["block_requests"] = block_requests
                    # Notify of update
                    async_dispatcher_send(self.hass, f"{SIGNAL_TAG_UPDATE}_{tag_mac}")
        if "reports xfer complete" in log_msg:
            # Extract MAC address from block request message
            parts = log_msg.split()
            if len(parts) > 0:
                tag_mac = parts[0].upper()
                if tag_mac in self._data:
                    # Notify of update
                    async_dispatcher_send(self.hass, f"{SIGNAL_TAG_IMAGE_UPDATE}_{tag_mac}", True)

    async def _process_tag_data(self, tag_mac: str, tag_data: dict, is_initial_load: bool = False) -> bool:
        """Process tag data and update internal state.

        Handles updates for a single tag, including:

        - Updating stored tag information
        - Calculating runtime and update counters
        - Managing tag discovery events
        - Broadcasting update events to entities
        - Triggering device events for buttons/NFC (with debouncing)

        Args:
            tag_mac: MAC address of the tag
            tag_data: Dictionary containing tag properties from the AP
            is_initial_load: True if this is part of initial loading at startup,
                             which affects event triggering behavior

        Returns:
            bool: True if this was a newly discovered tag, False for an update

        Raises:
            No exceptions are raised as they are caught and logged internally.
        """

        # Skip blacklisted tags
        if tag_mac in self._blacklisted_tags:
            _LOGGER.debug("Ignoring blacklisted tag: %s", tag_mac)
            return False

        # Check if this is a new tag
        is_new_tag = tag_mac not in self._known_tags

        # Get existing data to calculate runtime and update counters
        existing_data = self._data.get(tag_mac, {})

        tag_name = tag_data.get("alias") or tag_mac
        last_seen = tag_data.get("lastseen")
        next_update = tag_data.get("nextupdate")
        next_checkin = tag_data.get("nextcheckin")
        lqi = tag_data.get("LQI")
        rssi = tag_data.get("RSSI")
        temperature = tag_data.get("temperature")
        battery_mv = tag_data.get("batteryMv")
        pending = tag_data.get("pending")
        hw_type = tag_data.get("hwType")
        hw_string = get_hw_string(hw_type)
        width, height = self._tag_manager.get_hw_dimensions(hw_type)
        content_mode = tag_data.get("contentMode")
        wakeup_reason = self._get_wakeup_reason_string(tag_data.get("wakeupReason"))
        capabilities = tag_data.get("capabilities")
        hashv = tag_data.get("hash")
        modecfgjson = tag_data.get("modecfgjson")
        is_external = tag_data.get("isexternal")
        rotate = tag_data.get("rotate")
        lut = tag_data.get("lut")
        channel = tag_data.get("ch")
        version = tag_data.get("ver")
        update_count = tag_data.get("updatecount")

        # Check if name has changed
        old_name = existing_data.get("tag_name")
        if old_name and old_name != tag_name:
            _LOGGER.debug("Tag name changed from '%s' to '%s'", old_name, tag_name)
            # Update device name in device registry
            device_registry = dr.async_get(self.hass)
            device = device_registry.async_get_device(
                identifiers={(DOMAIN, tag_mac)}
            )
            if device:
                device_registry.async_update_device(
                    device.id,
                    name=tag_name
                )

        # Calculate runtime delta (only if this is not the initial load)
        runtime_delta = 0
        runtime_total =  existing_data.get("runtime", 0)
        if not is_initial_load and existing_data:
            runtime_delta = self._calculate_runtime_delta(tag_data, existing_data)
            runtime_total += runtime_delta

        # Update boot count if this is a power-on event
        boot_count = existing_data.get("boot_count", 1)
        if not is_initial_load and wakeup_reason in [1, 252, 254]:  # BOOT, FIRSTBOOT, WDT_RESET
            boot_count += 1
            runtime_total = 0  # Reset runtime on boot

        # Update check-in counter
        checkin_count = existing_data.get("checkin_count", 0)
        if not is_initial_load:
            checkin_count += 1

        # Get existing block request count
        block_requests = existing_data.get("block_requests", 0)

        # Update tag data
        self._data[tag_mac] = {
            "tag_mac": tag_mac,
            "tag_name": tag_name,
            "last_seen": last_seen,
            "next_update": next_update,
            "next_checkin": next_checkin,
            "lqi": lqi,
            "rssi": rssi,
            "temperature": temperature,
            "battery_mv": battery_mv,
            "pending": pending,
            "hw_type": hw_type,
            "width": width,
            "height": height,
            "hw_string": hw_string,
            "content_mode": self._get_content_mode_string(content_mode),
            "wakeup_reason": wakeup_reason,
            "capabilities": capabilities,
            "hash": hashv,
            "modecfgjson": modecfgjson,
            "is_external": is_external,
            "rotate": rotate,
            "lut": lut,
            "channel": channel,
            "version": version,
            "update_count": update_count,
            "runtime": runtime_total,
            "boot_count": boot_count,
            "checkin_count": checkin_count,
            "block_requests": block_requests,
        }

        # Handle new tag discovery
        if is_new_tag:
            self._known_tags.add(tag_mac)
            _LOGGER.debug("Discovered new tag: %s", tag_mac)
            # Fire discovery event before saving
            async_dispatcher_send(self.hass, f"{DOMAIN}_tag_discovered", tag_mac)

        # Fire state update event
        async_dispatcher_send(self.hass, f"{SIGNAL_TAG_UPDATE}_{tag_mac}")

        # Handle wakeup event if needed and not initial load
        wakeup_reason = tag_data.get("wakeupReason")
        if not is_initial_load and wakeup_reason is not None:
            reason_string = self._get_wakeup_reason_string(wakeup_reason)

            should_fire = True
            current_time = datetime.now()

            # Apply debouncing based on event type
            if reason_string in ["BUTTON1", "BUTTON2", "BUTTON3", "BUTTON4", "BUTTON5", "BUTTON6", "BUTTON7", "BUTTON8", "BUTTON9", "BUTTON10"]:
                # Button debouncing
                debounce_key = f"{tag_mac}_{reason_string}"
                last_event = self._last_button_press.get(debounce_key)
                if last_event and (current_time - last_event) <= self._button_debounce_interval:
                    should_fire = False
                else:
                    self._last_button_press[debounce_key] = current_time

            elif reason_string == "NFC":
                # NFC debouncing
                debounce_key = f"{tag_mac}_NFC"
                last_event = self._nfc_last_scan.get(debounce_key)
                if last_event and (current_time - last_event) <= self._nfc_debounce_interval:
                    should_fire = False
                else:
                    self._nfc_last_scan[debounce_key] = current_time

            if should_fire:
                device_registry = dr.async_get(self.hass)
                device = device_registry.async_get_device(
                    identifiers={(DOMAIN, tag_mac)}
                )
                if device:
                    self.hass.bus.async_fire(f"{DOMAIN}_event", {
                        "device_id": device.id,
                        "type": reason_string
                    })

        return is_new_tag

    async def _fetch_all_tags_from_ap(self) -> dict:
        """Fetch complete list of tags from the AP database.

        Retrieves all tag data using the AP's HTTP API, handling pagination
        to ensure all tags are retrieved even when there are many tags.

        The API returns tags in batches, with a continuation token
        to fetch the next batch until all tags have been retrieved.

        Returns:
            dict: Dictionary mapping tag MAC addresses to their complete data

        Raises:
            Exception: If HTTP requests fail or return unexpected data
        """
        result = {}
        position = 0
        retries_left = 10

        while True:
            url = f"http://{self.host}/get_db"
            if position > 0:
                url += f"?pos={position}"

            try:
                response = await self.hass.async_add_executor_job(
                    lambda: requests.get(url, timeout=10)
                )

                if response.status_code != 200:
                    _LOGGER.error("Failed to fetch all tags from AP: %s", response.text)
                    retries_left -= 1
                    if retries_left <= 0:
                        raise Exception(f"Failed to fetch tags after multiple retries: {response.text}")
                    await asyncio.sleep(1)
                    continue

                data = response.json()

                # Add tags to set
                for tag in data.get("tags", []):
                    if "mac" in tag:
                        result[tag["mac"]] = tag

                # Check for pagination
                if "continu" in data and data["continu"] > 0:
                    position = data["continu"]
                else:
                    break

            except Exception as err:
                _LOGGER.error("Failed to fetch all tags from AP: %s", str(err))
                retries_left -= 1
                if retries_left <= 0:
                    raise
                await asyncio.sleep(1)
                continue

        return result

    async def async_load_all_tags(self) -> None:
        """Load all tags from the AP at startup.

        Fetches the complete list of tags from the AP's database and:

        - Processes each tag to update internal state
        - Counts new and updated tags for logging purposes
        - Saves updated data to persistent storage

        This provides a complete initial state for the integration
        without waiting for individual tag check-ins.

        Raises:
            Exception: If fetching or processing tags fails
        """
        try:
            _LOGGER.info("Loading existing tags from AP...")

            # Track how many tags we've processed
            new_tags_count = 0
            updated_tags_count = 0

            # Get all tag data from AP
            all_tags = await self._fetch_all_tags_from_ap()

            # Process each tag using our common helper function
            for tag_mac, tag_data in all_tags.items():
                # Process tag with the initial load flag set
                is_new = await self._process_tag_data(tag_mac, tag_data, is_initial_load=True)

                # Update counters
                if is_new:
                    new_tags_count += 1
                else:
                    updated_tags_count += 1

            # Save to persistent storage
            await self._store.async_save({"tags": self._data})

            if new_tags_count > 0 or updated_tags_count > 0:
                _LOGGER.info("Loaded %d new tags and updated %d existing tags from AP",
                             new_tags_count, updated_tags_count)

        except Exception as err:
            _LOGGER.error("Failed to load tags from AP: %s", err)
            raise

    def _track_record_count_changes(self, new_record_count: int) -> None:
        """Track changes in record count to detect tag deletions.

        When the AP's record count decreases, it indicates that one or more
        tags have been deleted from the AP. This method detects such changes
        and schedules a verification task to identify and remove deleted tags.

        Args:
            new_record_count: New record count reported by the AP
        """
        if self._last_record_count is not None and new_record_count < self._last_record_count:
            # Record count has decreased, indicating a possible tag deletion
            _LOGGER.info(f"AP record count decreased from {self._last_record_count} to {new_record_count}. Checking for deleted tags...")

            # Cancel existing cleanup task if any
            if self._cleanup_task and not self._cleanup_task.done():
                self._cleanup_task.cancel()

            # Schedule cleanup task to verify and clean up any deleted tags
            self._cleanup_task = self.hass.async_create_task(
                self._verify_and_cleanup_tags(),
                f"{DOMAIN}_tag_verification"
            )

        # Update the last known record count
        self._last_record_count = new_record_count

    async def _verify_and_cleanup_tags(self) -> None:
        """Verify which tags exist on the AP and clean up deleted ones.

        Checks if any locally known tags have been deleted from the AP
        and removes them from:

        - Internal data structures
        - Home Assistant device and entity registries
        - Persistent storage

        This ensures Home Assistant's state matches the actual AP state
        when tags are removed from the AP directly.

        Raises:
            No exceptions are raised as they are caught and logged internally.
        """
        try:
            # Get current tags from AP
            ap_tags = await self._fetch_all_tags_from_ap()

            # Map tags to mac addresses
            ap_macs = set(ap_tags.keys())

            ap_macs_upper = {mac.upper() for mac in ap_macs}
            known_macs_upper = {mac.upper() for mac in self._known_tags}

            # Find locally known tags that are missing from the AP
            deleted_tags = known_macs_upper - ap_macs_upper

            if deleted_tags:
                _LOGGER.info(f"Detected {len(deleted_tags)} deleted tags from AP: {deleted_tags}")

                # Map back to original case if needed
                for tag_mac in list(self._known_tags):  # Create a copy for safe iteration
                    if tag_mac.upper() in deleted_tags:
                        await self._remove_tag(tag_mac)

        except Exception as err:
            _LOGGER.error(f"Error while verifying AP tags: {err}")

    async def _remove_tag(self, tag_mac: str) -> None:
        """Remove a tag from HA.

        Args:
            tag_mac: The MAC address of the tag to remove.
        """
        _LOGGER.info(f"Removing tag {tag_mac} as it no longer exists on the AP")

        # Remove from known tags and data
        if tag_mac in self._known_tags:
            self._known_tags.remove(tag_mac)
            self._data.pop(tag_mac, None)

            # Notify that this tag has been removed
            async_dispatcher_send(self.hass, f"{SIGNAL_TAG_UPDATE}_{tag_mac}")

            # Remove related devices and entities
            device_registry = dr.async_get(self.hass)
            entity_registry = er.async_get(self.hass)

            # Find and remove entities for this tag
            entities_to_remove = []
            devices_to_remove = set()

            for entity in entity_registry.entities.values():
                if entity.config_entry_id == self.entry.entry_id:
                    device = device_registry.async_get(entity.device_id) if entity.device_id else None
                    if device:
                        for identifier in device.identifiers:
                            if identifier[0] == DOMAIN and identifier[1] == tag_mac:
                                entities_to_remove.append(entity.entity_id)
                                devices_to_remove.add(device.id)
                                break

            # Remove entities
            for entity_id in entities_to_remove:
                entity_registry.async_remove(entity_id)
                _LOGGER.debug(f"Removed entity {entity_id} for deleted tag {tag_mac}")

            # Remove devices
            for device_id in devices_to_remove:
                device_registry.async_remove_device(device_id)
                _LOGGER.debug(f"Removed device {device_id} for deleted tag {tag_mac}")

            # Update storage
            await self._store.async_save({"tags": self._data})

    async def async_reload_blacklist(self) -> None:
        """Reload the tag blacklist from config entry options.

        Updates the blacklist based on current integration options and:

        - Removes blacklisted tags from active tracking
        - Triggers entity and device removal for blacklisted tags
        - Updates persistent storage to reflect changes

        This is called when the integration options are updated.
        """
        entry = self.entry
        old_blacklist = self._blacklisted_tags.copy()
        self._blacklisted_tags = entry.options.get("blacklisted_tags", [])

        # Remove blacklisted tags from known tags and data
        for tag_mac in self._blacklisted_tags:
            if tag_mac in self._known_tags:
                self._known_tags.remove(tag_mac)
                self._data.pop(tag_mac, None)
                # Notify that this tag's state has changed
                async_dispatcher_send(self.hass, f"{SIGNAL_TAG_UPDATE}_{tag_mac}")

        # If the blacklist has changed, trigger cleanup
        if set(old_blacklist) != set(self._blacklisted_tags):
            # Trigger entity and device removal
            async_dispatcher_send(self.hass, f"{DOMAIN}_blacklist_update")

            # Give Home Assistant time to process removals
            await asyncio.sleep(0.1)

            # Force a state refresh for all remaining tags
            for tag_mac in self._known_tags:
                if tag_mac not in self._blacklisted_tags:
                    async_dispatcher_send(self.hass, f"{SIGNAL_TAG_UPDATE}_{tag_mac}")

            # Save updated data to storage
            await self._store.async_save({
                "tags": self._data
            })

    async def _handle_ap_config_message(self,dict) -> None:
        """Handle AP configuration updates.

        Fetches the current AP configuration via HTTP and updates the
        internal configuration state. This triggers when the AP sends
        a configuration change notification.

        The method uses a hash comparison to only trigger entity updates
        when the configuration actually changes.

        Args:
            message: The configuration message from the AP
        """
        try:
            if self._shutdown.is_set():
                return

            async with aiohttp.ClientSession() as session:
                async with async_timeout.timeout(10):
                    async with session.get(f"http://{self.host}/get_ap_config") as response:
                        if response.status != 200:
                            _LOGGER.error("Failed to fetch AP config: HTTP %s", response.status)
                            return

                        new_config = await response.json()

                        # Compare with existing config
                        if not hasattr(self, '_last_config_hash'):
                            self._last_config_hash = None

                        # Create hash of new config for comparison
                        new_hash = hash(frozenset(new_config.items()))

                        if new_hash != self._last_config_hash:
                            self.ap_config = new_config
                            self._last_config_hash = new_hash
                            _LOGGER.debug("AP config updated: %s", self.ap_config)
                            async_dispatcher_send(self.hass, f"{DOMAIN}_ap_config_update")
                        else:
                            _LOGGER.debug("AP config unchanged, skipping update")

        except asyncio.TimeoutError:
            _LOGGER.error("Timeout fetching AP config")
        except Exception as err:
            _LOGGER.error("Failed to fetch AP config: %s", err)

    @staticmethod
    def _get_wakeup_reason_string(reason: int) -> str:
        """Convert numeric wakeup reason code to human-readable string.

        Maps the numeric reasons received from the AP to descriptive strings:

        - 0: "TIMED" (normal timed wakeup)
        - 1: "BOOT" (device boot)
        - 2: "GPIO" (GPIO trigger)
        - 3: "NFC" (NFC scan)
        - 4: "BUTTON1" (button 1 pressed)
        - 5: "BUTTON2" (button 2 pressed)
        - 6: "BUTTON3" (button 3 pressed)
        - 7: "BUTTON4" (button 4 pressed)
        - 8: "BUTTON5" (button 5 pressed)
        - 9: "BUTTON6" (button 6 pressed)
        - 10: "BUTTON7" (button 7 pressed)
        - 11: "BUTTON8" (button 8 pressed)
        - 12: "BUTTON9" (button 9 pressed)
        - 13: "BUTTON10" (button 10 pressed)
        - 252: "FIRSTBOOT" (first boot)
        - 253: "NETWORK_SCAN" (network scan)
        - 254: "WDT_RESET" (watchdog reset)

        Args:
            reason: Numeric wakeup reason code from the tag

        Returns:
            str: Human-readable reason or "UNKNOWN_{code}" if not recognized
        """
        reasons = {
            0: "TIMED",
            1: "BOOT",
            2: "GPIO",
            3: "NFC",
            4: "BUTTON1",
            5: "BUTTON2",
            6: "BUTTON3",
            7: "BUTTON4",
            8: "BUTTON5",
            9: "BUTTON6",
            10: "BUTTON7",
            11: "BUTTON8",
            12: "BUTTON9",
            13: "BUTTON10",
            252: "FIRSTBOOT",
            253: "NETWORK_SCAN",
            254: "WDT_RESET"
        }
        return reasons.get(reason, f"UNKNOWN_{reason}")

    @staticmethod
    def _get_ap_state_string(state: int) -> str:
        """Convert AP state code to human-readable string.

        Maps the numeric state codes received from the AP to descriptive strings:

        - 0: "Offline"
        - 1: "Online"
        - 2: "Flashing"
        - 3: "Waiting for reset"
        - etc.

        Args:
            state: Numeric AP state code

        Returns:
            str: Human-readable state or "Unknown: {code}" if not recognized
        """
        states = {
            0: "Offline",
            1: "Online",
            2: "Flashing",
            3: "Waiting for reset",
            4: "Requires power cycle",
            5: "Failed",
            6: "Coming online",
            7: "No radio"
        }
        return states.get(state, f"Unknown: {state}")

    @staticmethod
    def _get_ap_run_state_string(state: int) -> str:
        """Convert AP run state code to human-readable string.

        Maps the numeric run state codes received from the AP to descriptive strings:

        - 0: "Stopped"
        - 1: "Paused"
        - 2: "Running"
        - 3: "Initializing"

        The run state indicates the operational mode of the AP's tag update system.

        Args:
            state: Numeric AP run state code

        Returns:
            str: Human-readable run state or "Unknown: {state}" if not recognized
        """
        states = {
            0: "Stopped",
            1: "Paused",
            2: "Running",
            3: "Initializing",
        }
        return states.get(state, f"Unknown: {state}")

    @staticmethod
    def _get_content_mode_string(mode: int) -> str:
        """Convert content mode code to human-readable string.

        Maps the numeric content mode codes to descriptive strings indicating
        what type of content the tag is displaying:

        - 0: "Not configured"
        - 1: "Current date"
        - 7: "Image URL"
        - 25: "Home Assistant"
        - etc.

        Args:
            mode: Numeric content mode code

        Returns:
            str: Human-readable content mode or "Unknown: {mode}" if not recognized
        """
        modes = {
            0: "Not configured",
            1: "Current date",
            2: "Count days",
            3: "Count hours",
            4: "Current weather",
            5: "Firmware update",
            7: "Image URL",
            8: "Weather forecast",
            9: "RSS Feed",
            10: "QR Code",
            11: "Google calendar",
            12: "Remote content",
            14: "Set NFC URL",
            15: "Custom LUT",
            16: "Buienradar",
            18: "Tag Config",
            19: "JSON template",
            20: "Display a copy",
            21: "AP Info",
            22: "Static image",
            23: "Image preload",
            24: "External image",
            25: "Home Assistant",
            26: "Timestamp",
            27: "Dayahead prices",


        }
        return modes.get(mode, f"Unknown: {mode}")

    @property
    def tags(self) -> list[str]:
        """Return list of known tag MAC addresses.

        Provides access to the current set of tracked tag MAC addresses,
        excluding those that have been blacklisted.

        Returns:
            list[str]: List of MAC addresses for all known, non-blacklisted tags
        """
        return list(self._known_tags)

    def get_tag_data(self, tag_mac: str) -> dict:
        """Get the current data for a specific tag.

        Retrieves the complete tag data dictionary for the specified
        tag MAC address, containing all properties like battery level,
        temperature, status, etc.

        Args:
            tag_mac: MAC address of the tag

        Returns:
            dict: Complete tag data dictionary or empty dict if tag not found
        """
        return self._data.get(tag_mac, {})

    def get_blacklisted_tags(self) -> list[str]:
        """Return the list of blacklisted tag MAC addresses.

        Blacklisted tags are known to the AP but ignored by Home Assistant.
        This is configured through the integration's options flow.

        Returns:
            list[str]: List of blacklisted tag MAC addresses
        """
        return self._blacklisted_tags

    @property
    def ap_status(self) -> dict:
        """Get current AP status information.

        Returns a copy of the current AP status dictionary containing:

        - Connection information (IP, Wi-Fi settings)
        - System metrics (heap, database size)
        - Operational state (uptime, run state)
        - Tag statistics (record count, low battery count)

        Returns:
            dict: Copy of the current AP status dictionary
        """
        return self._ap_data.copy()

    async def async_update_ap_config(self) -> None:
        """Force an update of AP configuration from the AP.

        Fetches the current AP configuration settings via HTTP and
        updates the internal configuration state. This will trigger
        updates for any entities that display configuration values.

        Raises:
            HomeAssistantError: If the AP is offline or returns an error.
        """
        await self._handle_ap_config_message({"apitem": {"type": "change"}})

    @staticmethod
    def _calculate_runtime_delta(new_data: dict, existing_data: dict) -> int:
        """Calculate a tag's runtime delta between check-ins.

        Determines how much runtime to add based on the difference
        between last_seen timestamps, taking into account:

        - Power cycles (resets runtime counter)
        - Invalid intervals (exceeding max_valid_interval)

        Args:
            new_data: New tag data received from AP
            existing_data: Previously stored tag data

        Returns:
            int: Runtime in seconds to add to the tag's total runtime,
                 or 0 if the interval is invalid or a power cycle occurred
        """
        last_seen_old = existing_data.get("last_seen", 0)
        last_seen_new = new_data.get("lastseen", 0)

        if last_seen_old == 0:
            return 0

        time_diff = last_seen_new - last_seen_old
        max_valid_interval = 600  # 10 minutes - max expected interval between check-ins

        wake_reason = new_data.get("wakeupReason")
        is_power_cycle = wake_reason in [1, 252, 254]  # BOOT, FIRSTBOOT, WDT_RESET

        if is_power_cycle or time_diff > max_valid_interval:
            return 0

        return time_diff

    async def async_update_ap_info(self) -> None:
        """Force update of AP configuration.

        Fetches the current configuration from the AP via HTTP
        and updates the internal state. This will trigger updates
        for any entities that display configuration values.

        This can be called manually to refresh configuration or
        is triggered automatically when the AP sends a configuration
        change notification.
        """
        try:
            async with async_timeout.timeout(10):
                async with self._session.get(f"http://{self.host}/sysinfo") as response:
                    if response.status != 200:
                        _LOGGER.error("Failed to fetch AP sys info: HTTP %s", response.status)
                        return

                    data = await response.json()
                    self.ap_env = data.get("env")
                    self.ap_model = self._format_ap_model(self.ap_env)

        except Exception as err:
            _LOGGER.error(f"Error updating AP info: {err}")

    @staticmethod
    def _format_ap_model(ap_env: str) -> str:
        """Format the build string to a user-friendly display name.

        Converts technical model identifiers received from the AP
        into human-readable device model names for display in the UI.

        For example:

        - "OpenEPaper_Mini_AP_v4" becomes "Mini AP v4"
        - "ESP32_S3_16_8_YELLOW_AP" becomes "Yellow AP"

        Args:
            ap_env: The raw build environment string from the AP

        Returns:
            str: Human-friendly model name if known, or the original
                 string if no mapping exists. Returns "ESP32" if input is empty.
        """
        if not ap_env:
            return "ESP32"

        model_mapping = {
            "ESP32_S3_C6_NANO_AP": "Nano AP",
            "OpenEPaperLink_Mini_AP_v4": "Mini AP v4",
            "OpenEPaperLink_ESP32-PoE-ISO_AP": "PoE ISO AP",
            "ESP32_S3_16_8_LILYGO_AP": "LilyGo T-Panel S3",
            "OpenEPaperLink_AP_and_Flasher": "AP and Flasher",
            "OpenEPaperLink_PoE_AP": "PoE AP",
            "BLE_ONLY_AP": "BLE only AP",
            "OpenEPaperLink_Nano_TLSR": "Nano TLSR AP",
            "ESP32_S3_16_8_YELLOW_AP": "Yellow AP",
        }

        if ap_env in model_mapping:
            return model_mapping[ap_env]

        return ap_env
