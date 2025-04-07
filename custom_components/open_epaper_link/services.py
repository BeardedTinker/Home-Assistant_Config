from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Final

import async_timeout
import requests

from requests_toolbelt import MultipartEncoder

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from .const import DOMAIN
from .imagegen import ImageGen
from .tag_types import get_tag_types_manager
from .util import send_tag_cmd, reboot_ap

_LOGGER: Final = logging.getLogger(__name__)

DITHER_DISABLED=0
DITHER_FLOYD_STEINBERG=1
DITHER_ORDERED=2

DITHER_DEFAULT=DITHER_ORDERED

def rgb_to_rgb332(rgb):
    """Convert RGB values to RGB332 format."""
    r, g, b = [max(0, min(255, x)) for x in rgb]
    r = (r // 32) & 0b111
    g = (g // 32) & 0b111
    b = (b // 64) & 0b11
    rgb332 = (r << 5) | (g << 2) | b
    return str(hex(rgb332)[2:].zfill(2))

def int_to_hex_string(number: int) -> str:
    """Convert integer to two-digit hex string."""
    hex_string = hex(number)[2:]
    return '0' + hex_string if len(hex_string) == 1 else hex_string

async def get_entity_id_from_device_id(hass: HomeAssistant, device_id: str) -> str:
    """Get the primary entity ID for a device."""
    device_registry = dr.async_get(hass)
    device = device_registry.async_get(device_id)
    if not device:
        raise HomeAssistantError(f"Device {device_id} not found")

    # Get the first entity ID associated with this device
    if not device.identifiers:
        raise HomeAssistantError(f"No identifiers found for device {device_id}")

    # Get the MAC address from the device identifier
    domain_mac = next(iter(device.identifiers))
    if domain_mac[0] != DOMAIN:
        raise HomeAssistantError(f"Device {device_id} is not an OpenEPaperLink device")

    return f"{DOMAIN}.{domain_mac[1].lower()}"

class UploadQueueHandler:
    """Handle queued image uploads to the AP."""

    def __init__(self, max_concurrent: int = 1, cooldown: float = 1.0):
        """Initialize the upload queue handler."""
        self._queue = asyncio.Queue()
        self._processing = False
        self._max_concurrent = max_concurrent
        self._cooldown = cooldown
        self._active_uploads = 0
        self._last_upload = None
        self._lock = asyncio.Lock()

    def __str__(self):
        """Return queue status string."""
        return f"Queue(active={self._active_uploads}, size={self._queue.qsize()})"

    async def add_to_queue(self, upload_func, *args, **kwargs):
        """Add an upload task to the queue."""

        entity_id = next((arg for arg in args if isinstance(arg, str) and "." in arg), "unknown")

        _LOGGER.debug("Adding upload task to queue for %s. %s", entity_id, self)
        # Add task to queue
        await self._queue.put((upload_func, args, kwargs))

        # Start processing queue if not already running
        if not self._processing:
            _LOGGER.debug("Starting upload queue processor for %s", entity_id)
            asyncio.create_task(self._process_queue())

    async def _process_queue(self):
        """Process queued upload tasks."""
        self._processing = True
        _LOGGER.debug("Upload queue processor started. %s", self)

        try:
            while not self._queue.empty():
                async with self._lock:
                    # Check if the upload limit has been reached
                    if self._active_uploads >= self._max_concurrent:
                        _LOGGER.debug("Hit concurrent upload limit (%d). Waiting...", self._max_concurrent)
                        await asyncio.sleep(0.1)
                        continue

                    # Check cooldown period
                    if self._last_upload:
                        elapsed = (datetime.now() - self._last_upload).total_seconds()
                        if elapsed < self._cooldown:
                            _LOGGER.debug("In cooldown period (%.1f seconds remaining)",
                                          self._cooldown - elapsed)
                            await asyncio.sleep(self._cooldown - elapsed)

                    # Get next task from queue
                    upload_func, args, kwargs = await self._queue.get()

                    entity_id = next((arg for arg in args if isinstance(arg, str) and "." in arg), "unknown")

                    try:
                        # Increment active uploads counter
                        self._active_uploads += 1
                        _LOGGER.debug("Starting upload for %s. %s", entity_id, self)

                        # Perform upload
                        _LOGGER.debug("Starting queued upload task")
                        start_time = datetime.now()
                        await upload_func(*args, **kwargs)
                        duration = (datetime.now() - start_time).total_seconds()

                        # Update last upload timestamp
                        self._last_upload = datetime.now()
                        _LOGGER.debug("Upload completed for %s in %.1f seconds", entity_id, duration)

                    except Exception as err:
                        _LOGGER.error("Error processing queued upload for %s: %s", entity_id, str(err))
                    finally:
                        # Decrement active upload counter
                        self._active_uploads -= 1
                        # Mark task as done
                        self._queue.task_done()
                        _LOGGER.debug("Upload task for %s finished. %s", entity_id, self)
        finally:
            self._processing = False



async def async_setup_services(hass: HomeAssistant) -> None:
    """Set up the OpenEPaperLink services."""

    upload_queue = UploadQueueHandler(max_concurrent=1, cooldown=1.0)

    async def get_hub():
        """Get the hub instance."""
        if DOMAIN not in hass.data or not hass.data[DOMAIN]:
            raise HomeAssistantError("Integration not configured")
        return next(iter(hass.data[DOMAIN].values()))

    async def drawcustom_service(service: ServiceCall) -> None:
        """Handle drawcustom service calls."""
        hub = await get_hub()
        if not hub.online:
            raise HomeAssistantError(
                "AP is offline. Please check your network connection and AP status."
            )

        device_ids = service.data.get("device_id")
        if isinstance(device_ids, str):
            device_ids = [device_ids]

        generator = ImageGen(hass)
        errors = []

        # Process each device
        for device_id in device_ids:
            device_errors = []
            try:
                # Get entity ID from device ID
                entity_id = await get_entity_id_from_device_id(hass, device_id)
                _LOGGER.debug("Processing device_id: %s (entity_id: %s)", device_id, entity_id)

                try:
                    # Generate image
                    image_data = await generator.generate_custom_image(
                        entity_id=entity_id,
                        service_data=service.data,
                        error_collector=device_errors
                    )

                    if device_errors:
                        errors.extend([f"Device {entity_id}: {err}" for err in device_errors])
                        _LOGGER.warning(
                            "Completed with warnings for device %s:\n%s",
                            device_id,
                            "\n".join(device_errors)
                        )

                    if service.data.get("dry-run", False):
                        _LOGGER.info("Dry run completed for %s", entity_id)
                        continue

                    # Queue the upload
                    await upload_queue.add_to_queue(
                        upload_image,
                        hub,
                        entity_id,
                        image_data,
                        service.data.get("dither", DITHER_DEFAULT),
                        service.data.get("ttl", 60),
                        service.data.get("preload_type", 0),
                        service.data.get("preload_lut", 0)
                    )

                except Exception as err:
                    error_msg = f"Error processing device {entity_id}: {str(err)}"
                    errors.append(error_msg)
                    _LOGGER.error(error_msg)
                    continue

            except Exception as err:
                error_msg = f"Failed to process device {device_id}: {str(err)}"
                errors.append(error_msg)
                _LOGGER.error(error_msg)
                continue

        if errors:
            raise HomeAssistantError("\n".join(errors))

    async def upload_image(hub, entity_id: str, img: bytes, dither: int, ttl: int,
                           preload_type: int = 0, preload_lut: int = 0) -> None:
        """Upload image to tag through AP."""
        url = f"http://{hub.host}/imgupload"
        mac = entity_id.split(".")[1].upper()

        _LOGGER.debug("Preparing upload for %s (MAC: %s)", entity_id, mac)
        _LOGGER.debug("Upload parameters: dither=%d, ttl=%d, preload_type=%d, preload_lut=%d",
                      dither, ttl, preload_type, preload_lut)

        # Convert TTL fom seconds to minutes for the AP
        ttl_minutes = max(1, ttl // 60)

        # Prepare multipart form data
        fields = {
            'mac': mac,
            'contentmode': "25",
            'dither': str(dither),
            'ttl': str(ttl_minutes),
            'image': ('image.jpg', img, 'image/jpeg'),
        }

        _LOGGER.debug("Image size for %s: %.1f KB", entity_id, len(img)/1024)

        # Add preload parameters if needed
        if preload_type > 0:
            fields.update({
                'preloadtype': str(preload_type),
                'preloadlut': str(preload_lut),
            })

        mp_encoder = MultipartEncoder(fields=fields)

        try:
            async with async_timeout.timeout(30):  # 30 second timeout for upload
                response = await hass.async_add_executor_job(
                    lambda: requests.post(
                        url,
                        headers={'Content-Type': mp_encoder.content_type},
                        data=mp_encoder
                    )
                )

            if response.status_code != 200:
                raise HomeAssistantError(
                    f"Image upload failed for {entity_id} with status code: {response.status_code}"
                )

        except asyncio.TimeoutError:
            raise HomeAssistantError(f"Image upload timed out for {entity_id}")
        except Exception as err:
            raise HomeAssistantError(f"Failed to upload image for {entity_id}: {str(err)}")

    async def setled_service(service: ServiceCall) -> None:
        """Handle LED pattern service calls."""
        hub = await get_hub()
        if not hub.online:
            raise HomeAssistantError("AP is offline")

        device_ids = service.data.get("device_id")
        if isinstance(device_ids, str):
            device_ids = [device_ids]

        for device_id in device_ids:
            entity_id = await get_entity_id_from_device_id(hass, device_id)
            _LOGGER.info("Processing device_id: %s (entity_id: %s)", device_id, entity_id)
            mac = entity_id.split(".")[1].upper()

            mode = service.data.get("mode", "")
            modebyte = "1" if mode == "flash" else "0"
            brightness = service.data.get("brightness", 2)
            modebyte = hex(((brightness - 1) << 4) + int(modebyte))[2:]

            pattern = (
                    modebyte +
                    rgb_to_rgb332(service.data.get("color1", "")) +
                    hex(int(service.data.get("flashSpeed1", 0.2) * 10))[2:] +
                    hex(service.data.get("flashCount1", 2))[2:] +
                    int_to_hex_string(int(service.data.get("delay1", 0.1) * 10)) +
                    rgb_to_rgb332(service.data.get("color2", "")) +
                    hex(int(service.data.get("flashSpeed2", 0.2) * 10))[2:] +
                    hex(service.data.get("flashCount2", 2))[2:] +
                    int_to_hex_string(int(service.data.get("delay2", 0.1) * 10)) +
                    rgb_to_rgb332(service.data.get("color3", "")) +
                    hex(int(service.data.get("flashSpeed3", 0.2) * 10))[2:] +
                    hex(service.data.get("flashCount3", 2))[2:] +
                    int_to_hex_string(int(service.data.get("delay3", 0.0) * 10)) +
                    int_to_hex_string(service.data.get("repeats", 2) - 1) +
                    "00"
            )

            url = f"http://{hub.host}/led_flash?mac={mac}&pattern={pattern}"
            result = await hass.async_add_executor_job(requests.get, url)
            if result.status_code != 200:
                _LOGGER.warning("LED pattern update failed with status code: %s", result.status_code)

    async def clear_pending_service(service: ServiceCall) -> None:
        """Handle clear pending service calls."""
        device_ids = service.data.get("device_id")
        if isinstance(device_ids, str):
            device_ids = [device_ids]

        for device_id in device_ids:
            entity_id = await get_entity_id_from_device_id(hass, device_id)
            await send_tag_cmd(hass, entity_id, "clear")

    async def force_refresh_service(service: ServiceCall) -> None:
        """Handle force refresh service calls."""
        device_ids = service.data.get("device_id")
        if isinstance(device_ids, str):
            device_ids = [device_ids]

        for device_id in device_ids:
            entity_id = await get_entity_id_from_device_id(hass, device_id)
            await send_tag_cmd(hass, entity_id, "refresh")

    async def reboot_tag_service(service: ServiceCall) -> None:
        """Handle tag reboot service calls."""
        device_ids = service.data.get("device_id")
        if isinstance(device_ids, str):
            device_ids = [device_ids]

        for device_id in device_ids:
            entity_id = await get_entity_id_from_device_id(hass, device_id)
            await send_tag_cmd(hass, entity_id, "reboot")

    async def scan_channels_service(service: ServiceCall) -> None:
        """Handle channel scan service calls."""
        device_ids = service.data.get("device_id")
        if isinstance(device_ids, str):
            device_ids = [device_ids]

        for device_id in device_ids:
            entity_id = await get_entity_id_from_device_id(hass, device_id)
            await send_tag_cmd(hass, entity_id, "scan")

    async def reboot_ap_service(service: ServiceCall) -> None:
        """Handle AP reboot service calls."""
        await reboot_ap(hass)

    async def refresh_tag_types_service(service: ServiceCall) -> None:
        """Handle tag type refresh service calls."""
        manager = await get_tag_types_manager(hass)
        manager._last_update = None  # Force refresh
        await manager.ensure_types_loaded()

        tag_types_len = len(manager.get_all_types())
        message = f"Successfully refreshed {tag_types_len} tag types from GitHub"

        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "Tag Types Refreshed",
                "message": message,
                "notification_id": "tag_types_refresh_notification",
            },
        )

    # Register current services
    hass.services.async_register(DOMAIN, "drawcustom", drawcustom_service)
    hass.services.async_register(DOMAIN, "setled", setled_service)
    hass.services.async_register(DOMAIN, "clear_pending", clear_pending_service)
    hass.services.async_register(DOMAIN, "force_refresh", force_refresh_service)
    hass.services.async_register(DOMAIN, "reboot_tag", reboot_tag_service)
    hass.services.async_register(DOMAIN, "scan_channels", scan_channels_service)
    hass.services.async_register(DOMAIN, "reboot_ap", reboot_ap_service)
    hass.services.async_register(DOMAIN, "refresh_tag_types", refresh_tag_types_service)

    # Register handlers for deprecated services that just show error
    async def deprecated_service_handler(service: ServiceCall, old_service: str) -> None:
        """Handler for deprecated services that raises an error."""
        raise HomeAssistantError(
            f"The service {DOMAIN}.{old_service} has been removed. "
            f"Please use {DOMAIN}.drawcustom instead. "
            "See the documentation for more details."
        )

    # Register deprecated services with error message
    for old_service in ["dlimg", "lines5", "lines4"]:
        hass.services.async_register(
            DOMAIN,
            old_service,
            lambda call, name=old_service: deprecated_service_handler(call, name)
        )

async def async_unload_services(hass: HomeAssistant) -> None:
    """Unload OpenEPaperLink services."""
    services = [
        "dlimg", "lines5", "lines4", "drawcustom", "setled", "clear_pending",
        "force_refresh", "reboot_tag", "scan_channels", "reboot_ap", "refresh_tag_types"
    ]
    for service in services:
        hass.services.async_remove(DOMAIN, service)