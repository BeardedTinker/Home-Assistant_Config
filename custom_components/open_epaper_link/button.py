from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
import requests
import json
import logging

from .tag_types import get_hw_dimensions, get_tag_types_manager
from .util import send_tag_cmd, reboot_ap
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    hub = hass.data[DOMAIN][entry.entry_id]

    # Track added tags to prevent duplicates
    added_tags = set()

    async def async_add_tag_buttons(tag_mac: str) -> None:
        """Add buttons for a newly discovered tag."""

        # Skip if tag is blacklisted
        if tag_mac in hub.get_blacklisted_tags():
            _LOGGER.debug("Skipping button creation for blacklisted tag: %s", tag_mac)
            return

        if tag_mac in added_tags:
            return

        added_tags.add(tag_mac)
        new_buttons = [
            ClearPendingTagButton(hass, tag_mac, hub),
            ForceRefreshButton(hass, tag_mac, hub),
            RebootTagButton(hass, tag_mac, hub),
            ScanChannelsButton(hass, tag_mac, hub),
            DeepSleepButton(hass, tag_mac, hub),
        ]
        async_add_entities(new_buttons)

    # Add buttons for existing tags
    for tag_mac in hub.tags:
        await async_add_tag_buttons(tag_mac)

    # Add AP-level buttons
    async_add_entities([
        RebootAPButton(hass, hub),
        RefreshTagTypesButton(hass),
    ])

    # Listen for new tag discoveries
    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            f"{DOMAIN}_tag_discovered",
            async_add_tag_buttons
        )
    )

    # Listen for blacklist updates
    async def handle_blacklist_update() -> None:
        """Handle blacklist updates by removing buttons for blacklisted tags."""
        # Get all buttons registered for this entry
        device_registry = dr.async_get(hass)
        entity_registry = er.async_get(hass)

        # Track which devices need to be removed
        devices_to_remove = set()

        # Find and remove entities for blacklisted tags
        entities_to_remove = []
        for entity in entity_registry.entities.values():
            if entity.config_entry_id == entry.entry_id:
                # Check if this entity belongs to a blacklisted tag
                device = device_registry.async_get(entity.device_id) if entity.device_id else None
                if device:
                    for identifier in device.identifiers:
                        if identifier[0] == DOMAIN and identifier[1] in hub.get_blacklisted_tags():
                            entities_to_remove.append(entity.entity_id)
                            # Add device to removal list
                            devices_to_remove.add(device.id)
                            break

        # Remove the entities
        for entity_id in entities_to_remove:
            entity_registry.async_remove(entity_id)
            _LOGGER.debug("Removed entity %s for blacklisted tag", entity_id)

        # Remove the devices
        for device_id in devices_to_remove:
            device_registry.async_remove_device(device_id)
            _LOGGER.debug("Removed device %s for blacklisted tag", device_id)

    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            f"{DOMAIN}_blacklist_update",
            handle_blacklist_update
        )
    )

class ClearPendingTagButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, tag_mac: str, hub) -> None:
        """Initialize the button."""
        self.hass = hass
        self._tag_mac = tag_mac
        self._entity_id = f"{DOMAIN}.{tag_mac}"
        self._hub = hub
        self._attr_has_entity_name = True
        self._attr_translation_key = "clear_pending"
        # self._attr_name = f"{hub._data[tag_mac]['tag_name']} Clear Pending"
        self._attr_unique_id = f"{tag_mac}_clear_pending"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:broom"

    @property
    def device_info(self):
        """Return device info."""
        tag_name = self._hub._data[self._tag_mac]['tag_name']
        return {
            "identifiers": {(DOMAIN, self._tag_mac)},
            "name": tag_name,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._tag_mac not in self._hub.get_blacklisted_tags()

    async def async_press(self) -> None:
        await send_tag_cmd(self.hass, self._entity_id, "clear")

class ForceRefreshButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, tag_mac: str, hub) -> None:
        """Initialize the button."""
        self.hass = hass
        self._tag_mac = tag_mac
        self._entity_id = f"{DOMAIN}.{tag_mac}"
        self._hub = hub
        self._attr_has_entity_name = True
        self._attr_translation_key = "force_refresh"
        # self._attr_name = f"{hub._data[tag_mac]['tag_name']} Force Refresh"
        self._attr_unique_id = f"{tag_mac}_force_refresh"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:refresh"

    @property
    def device_info(self):
        """Return device info."""
        tag_name = self._hub._data[self._tag_mac]['tag_name']
        return {
            "identifiers": {(DOMAIN, self._tag_mac)},
            "name": tag_name,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._tag_mac not in self._hub.get_blacklisted_tags()

    async def async_press(self) -> None:
        await send_tag_cmd(self.hass, self._entity_id, "refresh")

class RebootTagButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, tag_mac: str, hub) -> None:
        """Initialize the button."""
        self.hass = hass
        self._tag_mac = tag_mac
        self._entity_id = f"{DOMAIN}.{tag_mac}"
        self._hub = hub
        self._attr_has_entity_name = True
        self._attr_translation_key = "reboot_tag"
        # self._attr_name = f"{hub._data[tag_mac]['tag_name']} Reboot"
        self._attr_unique_id = f"{tag_mac}_reboot"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:restart"

    @property
    def device_info(self):
        """Return device info."""
        tag_name = self._hub._data[self._tag_mac]['tag_name']
        return {
            "identifiers": {(DOMAIN, self._tag_mac)},
            "name": tag_name,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._tag_mac not in self._hub.get_blacklisted_tags()

    async def async_press(self) -> None:
        await send_tag_cmd(self.hass, self._entity_id, "reboot")

class ScanChannelsButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, tag_mac: str, hub) -> None:
        """Initialize the button."""
        self.hass = hass
        self._tag_mac = tag_mac
        self._entity_id = f"{DOMAIN}.{tag_mac}"
        self._hub = hub
        self._attr_has_entity_name = True
        self._attr_translation_key = "scan_channels"
        # self._attr_name = f"{hub._data[tag_mac]['tag_name']} Scan Channels"
        self._attr_unique_id = f"{tag_mac}_scan_channels"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:wifi"

    @property
    def device_info(self):
        """Return device info."""
        tag_name = self._hub._data[self._tag_mac]['tag_name']
        return {
            "identifiers": {(DOMAIN, self._tag_mac)},
            "name": tag_name,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._tag_mac not in self._hub.get_blacklisted_tags()

    async def async_press(self) -> None:
        await send_tag_cmd(self.hass, self._entity_id, "scan")

class DeepSleepButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, tag_mac: str, hub) -> None:
        """Initialize the button."""
        self.hass = hass
        self._tag_mac = tag_mac
        self._entity_id = f"{DOMAIN}.{tag_mac}"
        self._hub = hub
        self._attr_has_entity_name = True
        self._attr_translation_key = "deep_sleep"
        # self._attr_name = f"{hub._data[tag_mac]['tag_name']} Scan Channels"
        self._attr_unique_id = f"{tag_mac}_deep_sleep"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:sleep"

    @property
    def device_info(self):
        """Return device info."""
        tag_name = self._hub._data[self._tag_mac]['tag_name']
        return {
            "identifiers": {(DOMAIN, self._tag_mac)},
            "name": tag_name,
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._tag_mac not in self._hub.get_blacklisted_tags()

    async def async_press(self) -> None:
        await send_tag_cmd(self.hass, self._entity_id, "deepsleep")

class RebootAPButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, hub) -> None:
        """Initialize the button."""
        self.hass = hass
        self._hub = hub
        # self._attr_name = "Reboot AP"
        self._attr_has_entity_name = True
        self._attr_translation_key = "reboot_ap"
        self._attr_unique_id = "reboot_ap"
        self._attr_icon = "mdi:restart"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, "ap")},
        }

    async def async_press(self) -> None:
        await reboot_ap(self.hass)

class RefreshTagTypesButton(ButtonEntity):
    """Button to manually refresh tag types from GitHub."""

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._attr_unique_id = "refresh_tag_types"
        # self._attr_name = "Refresh Tag Types"
        self._attr_has_entity_name = True
        self._attr_translation_key = "refresh_tag_types"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:refresh"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, "ap")},
            "name": "OpenEPaperLink AP",
            "model": "esp32",
            "manufacturer": "OpenEPaperLink",
        }

    async def async_press(self) -> None:
        """Trigger a manual refresh of tag types."""
        manager = await get_tag_types_manager(self._hass)
        # Force a refresh by clearing the last update timestamp
        manager._last_update = None
        await manager.ensure_types_loaded()
        tag_types_len = len(manager.get_all_types())
        message = f"Successfully refreshed {tag_types_len} tag types from GitHub"
        await self.hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "Tag Types Refreshed",
                "message": message,
                "notification_id": "tag_types_refresh_notification",
            },
        )