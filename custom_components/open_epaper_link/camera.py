"""Camera implementation for OpenEPaperLink integration."""
from __future__ import annotations

import logging
import os
from typing import Final

from homeassistant.components.camera import Camera
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
import requests

from .tag_types import TagType
from .const import DOMAIN, SIGNAL_TAG_IMAGE_UPDATE
from .image_decompressor import to_image
from .tag_types import get_hw_string, get_tag_types_manager
from .util import get_image_path

_LOGGER: Final = logging.getLogger(__name__)

async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
) -> bool:
    """Set up EPD cameras from a config entry."""
    hub = hass.data[DOMAIN][entry.entry_id]

    # Track added cameras to prevent duplicates
    added_cameras = set()

    async def async_add_camera(tag_mac: str) -> None:
        """Add camera for a newly discovered tag."""
        # Skip if camera already exists
        if tag_mac in added_cameras:
            return

        # Skip if tag is blacklisted
        if tag_mac in hub.get_blacklisted_tags():
            _LOGGER.debug("Skipping camera creation for blacklisted tag: %s", tag_mac)
            return

        # Skip AP (it's not a tag)
        if tag_mac == "ap":
            return

        camera = EPDCamera(hass, tag_mac, hub)
        added_cameras.add(tag_mac)
        async_add_entities([camera], True)

    # Add cameras for existing tags
    for tag_mac in hub.tags:
        await async_add_camera(tag_mac)

    # Register callback for new tag discovery
    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            f"{DOMAIN}_tag_discovered",
            async_add_camera
        )
    )

    # Register callback for blacklist updates
    async def handle_blacklist_update() -> None:
        """Handle updates to the tag blacklist."""
        for tag_mac in hub.get_blacklisted_tags():
            if tag_mac in added_cameras:
                added_cameras.remove(tag_mac)

    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            f"{DOMAIN}_blacklist_update",
            handle_blacklist_update
        )
    )

    return True

class EPDCamera(Camera):
    """Camera class for OpenEPaperLink tags."""

    def __init__(self, hass: HomeAssistant, tag_mac: str, hub) -> None:
        super().__init__()
        self._tag_mac = tag_mac
        self._hub = hub
        self._attr_has_entity_name = True
        self._attr_translation_key = "content"
        self._attr_unique_id = f"{tag_mac}_content"
        tag_data = hub.get_tag_data(tag_mac)
        self._name = f"{tag_data.get('tag_name', tag_mac)}"
        self.content_type = "image/jpeg"
        self._image_path = get_image_path(hass, f"{DOMAIN}.{tag_mac}")
        self._last_image = None
        self._tag_type = None
        self._last_error = None

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._tag_mac)},
            "name": self._name,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
                self._hub.online and
                self._tag_mac in self._hub.tags and
                self._tag_mac not in self._hub.get_blacklisted_tags()
        )

    async def _fetch_raw_image(self) -> bytes | None:
        """Fetch raw image data from AP."""
        url = f"http://{self._hub.host}/current/{self._tag_mac}.raw"
        try:
            result = await self.hass.async_add_executor_job(lambda: requests.get(url))
            if result.status_code == 200:
                return result.content
            if result.status_code == 404:
                _LOGGER.debug("No image found for %s", self._tag_mac)
                return None

            _LOGGER.error(
                "Failed to fetch image for %s: HTTP %d",
                self._tag_mac,
                result.status_code
            )
            return None
        except Exception as err:
            _LOGGER.error(
                "Error fetching image for %s: %s",
                self._tag_mac,
                str(err)
            )
            return None

    async def _get_tag_def(self) -> TagType | None:
        """Get tag definition for image decoding."""
        if self._tag_type is None:
            try:
                tag_data = self._hub.get_tag_data(self._tag_mac)
                hw_type = tag_data.get("hw_type")
                if hw_type is None:
                    return None

                tag_manager = await get_tag_types_manager(self.hass)
                tag_type = await tag_manager.get_tag_info(hw_type)
                if tag_type is None:
                    return None
                self._tag_type = tag_type

            except Exception as err:
                _LOGGER.error(
                    "Error getting tag definition for %s: %s",
                    self._tag_mac,
                    str(err)
                )
                return None

        return self._tag_type



    async def async_camera_image(
            self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return image response."""
        try:
            # First check if we have an image on disk
            if os.path.exists(self._image_path):
                if not self._last_image:
                    self._last_image = await self.hass.async_add_executor_job(
                        lambda: open(self._image_path, 'rb').read()
                    )
                return self._last_image

            # No image on disk, try to fetch and decode
            raw_data = await self._fetch_raw_image()
            if raw_data:
                tag_def = await self._get_tag_def()
                if tag_def:
                    try:
                        # Create decoder and process image in executor to avoid blocking
                        def process_image():
                            # Log first byte of raw data for debugging
                            return to_image(raw_data, tag_def)

                        jpeg_data = await self.hass.async_add_executor_job(process_image)

                        # Save to disk
                        await self.hass.async_add_executor_job(
                            lambda: os.makedirs(os.path.dirname(self._image_path), exist_ok=True)
                        )
                        await self.hass.async_add_executor_job(
                            lambda: open(self._image_path, 'wb').write(jpeg_data)
                        )

                        self._last_image = jpeg_data
                        return jpeg_data
                    except Exception as err:
                        _LOGGER.error(
                            "Error decoding image for %s: %s",
                            self._tag_mac,
                            str(err)
                        )

        except Exception as err:
            _LOGGER.error(
                "Error getting camera image for %s: %s",
                self._tag_mac,
                str(err)
            )

        return None

    async def async_added_to_hass(self) -> None:
        """Register callbacks when entity is added."""
        # Update state on tag updates
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{SIGNAL_TAG_IMAGE_UPDATE}_{self._tag_mac}",
                self._handle_tag_update
            )
        )

        # Update state on connection status changes
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_connection_status",
                self._handle_connection_status
            )
        )

    @callback
    def _handle_tag_update(self, data) -> None:
        """Handle tag data updates."""
        # Clear cached image to force refresh on next request
        self._last_image = None
        # clear image file if not dry run
        if data:
            if os.path.exists(self._image_path):
                os.remove(self._image_path)
        # Update entity state
        self.async_write_ha_state()

    @callback
    def _handle_connection_status(self, is_online: bool) -> None:
        """Handle connection status updates."""
        self.async_write_ha_state()