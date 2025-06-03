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
"""Configuration for text entities to create for the AP.

This list defines the text input entities created during setup that 
control Access Point text-based settings. Each dictionary contains:

- key: Configuration parameter key in the AP's configuration system
- name: Human-readable name for display in the UI
- icon: Material Design Icons identifier for the entity
- description: Detailed explanation of the setting's purpose
"""
TAG_TEXT_ENTITIES = [
    {
        "key": "alias",
        "name": "Alias",
        "icon": "mdi:rename-box",
        "description": "Tag display name"
    }
]
"""Configuration for text entities to create for each tag.

This list defines the text input entities that will be created for
each discovered tag. Currently, this includes only the tag's alias,
which allows customizing the display name shown in Home Assistant and which also updates the tags alias on the AP.
"""

class APConfigText(TextEntity):
    """Text entity for AP configuration.

    Provides a text input entity that allows setting text-based
    configuration values on the OpenEPaperLink Access Point.

    The entity:

    - Displays the current value from the AP configuration
    - Allows editing the value and sending updates to the AP
    - Updates when the value is changed from other sources
    - Provides appropriate input constraints (max length, etc.)

    Common uses include setting the AP's display name (alias) and
    configuring the GitHub repository for tag type definitions.
    """

    def __init__(self, hub, key: str, name: str, icon: str, description: str) -> None:
        """Initialize the text entity.

        Sets up the text input with appropriate name, unique ID, icon,
        category, and constraints based on the provided configuration.

        Args:
            hub: Hub instance for AP communication
            key: Configuration key on the AP
            name: Human-readable name for the UI
            icon: Material Design Icons identifier
            description: Detailed description of the setting's purpose
        """
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
        """Return device info for the AP.

        Associates this text entity with the AP device in Home Assistant
        using the domain and "ap" as the identifier.

        Returns:
            dict: Device information dictionary with identifiers, name,
                  model, and manufacturer
        """
        return {
            "identifiers": {(DOMAIN, "ap")},
            "name": "OpenEPaperLink AP",
            "model": self._hub.ap_model,
            "manufacturer": "OpenEPaperLink",
        }

    @property
    def available(self) -> bool:
        """Return if entity is available.

        A text entity is available if:

        - The AP is online
        - The configuration key exists in the AP's config

        Returns:
            bool: True if the entity is available, False otherwise
        """
        return self._hub.online and self._key in self._hub.ap_config

    @property
    def native_value(self) -> str | None:
        """Return the current value.

        Retrieves the current text value from the AP configuration.

        Returns:
            str: Current value of the setting
            None: If the entity is not available
        """
        if not self.available:
            return None
        return str(self._hub.ap_config.get(self._key, ""))

    async def async_set_value(self, value: str) -> None:
        """Set the text value.

        Sends the new text value to the AP if it differs from the current value.
        This updates the AP's configuration and triggers a configuration update
        event to refresh other entities.

        Args:
            value: New text value to set
        """
        if value != self.native_value:
            await set_ap_config_item(self._hub, self._key, value)

    @callback
    def _handle_ap_config_update(self):
        """Handle updated AP configuration.

        Called when the AP configuration changes. Updates the text entity's
        value to reflect the new value from the AP, ensuring the UI stays
        in sync with the actual AP settings.
        """
        self.async_write_ha_state()

    @callback
    def _handle_connection_status(self, is_online: bool):
        """Handle connection status updates.

        Updates the text entity's availability state when the AP connection
        status changes. This ensures the entity appears as unavailable
        when the AP is offline.

        Args:
            is_online: Boolean indicating if the AP is online
        """
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Register callbacks when entity is added to Home Assistant.

        Sets up two dispatcher listeners:

        1. AP configuration updates - to refresh the value when settings change
        2. Connection status updates - to update availability when AP connects/disconnects

        This ensures the text input stays in sync with the actual AP configuration
        and properly reflects connection status changes.
        """
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
    """Text entity for tag name/alias.

    Provides a text input entity that allows setting a custom display name
    (alias) for an ESL tag. This makes it easier to identify tags in the UI
    by using meaningful names instead of MAC addresses.

    When the name is changed, it's sent to the AP via HTTP and stored
    in the AP's configuration, making the name persistent across restarts.
    """

    def __init__(self, hub, tag_mac: str) -> None:
        """Initialize the text entity.

        Sets up the text input with appropriate name, unique ID, and icon
        based on the tag's MAC address.

        Args:
            hub: Hub instance for AP communication
            tag_mac: MAC address of the tag
        """
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
        """Return device info for the tag.

        Associates this text entity with the tag device in Home Assistant
        using the tag MAC address as the identifier.

        Returns:
            dict: Device information dictionary with identifiers and name
        """
        tag_data = self._hub.get_tag_data(self._tag_mac)
        return {
            "identifiers": {(DOMAIN, self._tag_mac)},
            "name": tag_data.get("tag_name", self._tag_mac),
        }

    @property
    def available(self) -> bool:
        """Return if entity is available.

        A tag name text entity is available if:

        - The AP is online
        - The tag is known to the AP
        - The tag is not blacklisted

        Returns:
            bool: True if the entity is available, False otherwise
        """
        return (
                self._hub.online and
                self._tag_mac in self._hub.tags and
                self._tag_mac not in self._hub.get_blacklisted_tags()
        )

    @property
    def native_value(self) -> str | None:
        """Return the current value.

        Retrieves the current tag name from the hub's tag data.

        Returns:
            str: Current tag name or alias
            None: If the entity is not available
        """
        if not self.available:
            return None
        tag_data = self._hub.get_tag_data(self._tag_mac)
        return tag_data.get("tag_name", "")

    async def async_set_value(self, value: str) -> None:
        """Set the text value.

        Sends a request to the AP to update the tag's alias.
        If no value is provided, defaults to using the MAC address
        as the display name.

        Args:
            value: New tag name to set

        Raises:
            Exception: If the HTTP request fails
        """
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
        """Handle tag updates.

        Called when the tag's data is updated. Refreshes the text entity's
        value to reflect any changes to the tag name, ensuring the UI
        stays in sync with the actual tag configuration.
        """
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Register callbacks when entity is added to Home Assistant.

        Sets up a dispatcher listener for tag updates to refresh the
        entity's value when the tag data changes.

        This ensures the text input stays in sync with the actual tag name
        in the AP's configuration.
        """
        # Listen for tag updates
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_tag_update_{self._tag_mac}",
                self._handle_tag_update,
            )
        )

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up text entities for AP configuration and tag names.

    Creates text input entities for:

    1. AP configuration settings defined in AP_TEXT_ENTITIES
    2. Tag name/alias for each discovered tag

    For the AP entities, first ensures the AP configuration is loaded.
    For tags, creates an entity for each existing tag and sets up a
    listener to add entities for newly discovered tags.

    Args:
        hass: Home Assistant instance
        entry: Configuration entry
        async_add_entities: Callback to register new entities
    """
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
        """Add text entities for a newly discovered tag.

        Creates a TagNameText entity for a newly discovered tag,
        allowing the user to set a custom display name for the tag.

        Only adds the entity if the tag is not blacklisted.

        Args:
            tag_mac: MAC address of the newly discovered tag
        """
        if tag_mac not in hub.get_blacklisted_tags():
            async_add_entities([TagNameText(hub, tag_mac)])

    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            f"{DOMAIN}_tag_discovered",
            async_add_tag_text
        )
    )