from __future__ import annotations

import requests

from homeassistant.components.text import TextEntity, TextMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .util import set_ap_config_item

import logging

_LOGGER = logging.getLogger(__name__)

# Define text field configurations
AP_TEXT_ENTITIES = [
    {
        "key": "alias",
        "name": "Alias",
        "icon": "mdi:rename-box",
        "description": "AP display name"
    },
    {
        "key": "repo",
        "name": "Repository",
        "icon": "mdi:source-repository",
        "description": "GitHub repository for tag type definitions"
    }
]
TAG_TEXT_ENTITIES = [
    {
        "key": "alias",
        "name": "Alias",
        "icon": "mdi:rename-box",
        "description": "Tag display name"
    }
]

class APConfigText(TextEntity):
    """Text entity for AP configuration."""

    def __init__(self, hub, key: str, name: str, icon: str, description: str) -> None:
        """Initialize the text entity."""
        self._hub = hub
        self._key = key
        # self._attr_name = f"AP {name}"
        self._attr_unique_id = f"{hub.entry.entry_id}_{key}"
        self._attr_icon = icon
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_has_entity_name = True
        self._attr_translation_key = key
        self._attr_native_max = 32  # Reasonable max length for text fields
        self._attr_native_min = 0
        self._attr_mode = "text"
        self._description = description

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, "ap")},
            "name": "OpenEPaperLink AP",
            "model": "esp32",
            "manufacturer": "OpenEPaperLink",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._hub.online and self._key in self._hub.ap_config

    @property
    def native_value(self) -> str | None:
        """Return the current value."""
        if not self.available:
            return None
        return str(self._hub.ap_config.get(self._key, ""))

    async def async_set_value(self, value: str) -> None:
        """Set the text value."""
        if value != self.native_value:
            await set_ap_config_item(self._hub, self._key, value)

    @callback
    def _handle_ap_config_update(self):
        """Handle updated AP configuration."""
        self.async_write_ha_state()

    @callback
    def _handle_connection_status(self, is_online: bool):
        """Handle connection status updates."""
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Register callbacks."""
        # Listen for AP config updates
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_ap_config_update",
                self._handle_ap_config_update,
            )
        )

        # Listen for connection status updates
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_connection_status",
                self._handle_connection_status,
            )
        )
class TagNameText(TextEntity):
    """Text entity for tag name/alias."""

    def __init__(self, hub, tag_mac: str) -> None:
        """Initialize the text entity."""
        self._hub = hub
        self._tag_mac = tag_mac
        self._attr_unique_id = f"{tag_mac}_alias"
        self._attr_has_entity_name = True
        self._attr_translation_key = "tag_alias"
        self._attr_native_min = 0
        self._attr_mode = TextMode.TEXT
        self._attr_icon = "mdi:rename"

    @property
    def device_info(self):
        """Return device info."""
        tag_data = self._hub.get_tag_data(self._tag_mac)
        return {
            "identifiers": {(DOMAIN, self._tag_mac)},
            "name": tag_data.get("tag_name", self._tag_mac),
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
                self._hub.online and
                self._tag_mac in self._hub.tags and
                self._tag_mac not in self._hub.get_blacklisted_tags()
        )

    @property
    def native_value(self) -> str | None:
        """Return the current value."""
        if not self.available:
            return None
        tag_data = self._hub.get_tag_data(self._tag_mac)
        return tag_data.get("tag_name", "")

    async def async_set_value(self, value: str) -> None:
        """Set the text value."""
        if not value:
            value = self._tag_mac

        if value != self.native_value:
            url = f"http://{self._hub.host}/save_cfg"
            data = {
                'mac': self._tag_mac,
                'alias': value
            }
            try:
                result = await self.hass.async_add_executor_job(
                    lambda: requests.post(url, data=data)
                )
                if result.status_code != 200:
                    _LOGGER.error(
                        "Failed to update tag name %s: HTTP %s",
                        self._tag_mac,
                        result.status_code
                    )
            except Exception as err:
                _LOGGER.error(
                    "Error updating tag name for %s: %s",
                    self._tag_mac,
                    str(err)
                )

    @callback
    def _handle_tag_update(self):
        """Handle tag updates."""
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Register callbacks."""
        # Listen for tag updates
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_tag_update_{self._tag_mac}",
                self._handle_tag_update,
            )
        )

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up text entities for AP configuration."""
    hub = hass.data[DOMAIN][entry.entry_id]

    # Wait for initial AP config to be loaded
    if not hub.ap_config:
        await hub.async_update_ap_config()

    entities = []

    # Create AP text entities from configuration
    for config in AP_TEXT_ENTITIES:
        entities.append(
            APConfigText(
                hub,
                config["key"],
                config["name"],
                config["icon"],
                config["description"]
            )
        )

    # Add tag name/alias text entities
    for tag_mac in hub.tags:
        if tag_mac not in hub.get_blacklisted_tags():
            entities.append(TagNameText(hub, tag_mac))

    async_add_entities(entities)

    # Set up callback for new tag discovery
    async def async_add_tag_text(tag_mac: str) -> None:
        """Add text entities for a newly discovered tag."""
        if tag_mac not in hub.get_blacklisted_tags():
            async_add_entities([TagNameText(hub, tag_mac)])

    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            f"{DOMAIN}_tag_discovered",
            async_add_tag_text
        )
    )