from __future__ import annotations

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .util import set_ap_config_item

import logging

_LOGGER = logging.getLogger(__name__)

# Define switch configurations
SWITCH_ENTITIES = [
    {
        "key": "preview",
        "name": "Preview Images",
        "icon": "mdi:eye",
        "description": "Enable/disable preview images on the AP"
    },
    {
        "key": "ble",
        "name": "Bluetooth",
        "icon": "mdi:bluetooth",
        "description": "Enable/disable Bluetooth"
    },
    {
        "key": "nightlyreboot",
        "name": "Nightly Reboot",
        "icon": "mdi:restart",
        "description": "Enable/disable automatic nightly reboot of the AP"
    },
    {
        "key": "showtimestamp",
        "name": "Show Timestamp",
        "icon": "mdi:clock",
        "description": "Enable/disable showing timestamps on ESLs"
    }
]
"""Configuration for all switch entities to create for the AP.

This list defines all the switch entities that will be created during
integration setup. Each dictionary contains:

- key: Configuration parameter key in the AP's configuration system,
    matching the key used in HTTP API calls.
- name: Human-readable name for display in the UI. This will be combined
    with "AP" to form the full entity name.
- icon: Material Design Icons identifier for the entity.
    Format is "mdi:icon-name" matching the icon library.
- description: Detailed explanation of what the switch controls,
    used for tooltips and documentation.

Common AP features controlled through switches include:

- preview: Whether to show tag images on the AP's display
- ble: Bluetooth Low Energy functionality
- nightlyreboot: Automatic nightly AP reboot for stability
- showtimestamp: Whether to show timestamps on tag displays
"""

class APConfigSwitch(SwitchEntity):
    """Switch entity for AP configuration.

    Provides a toggle switch entity that controls a boolean setting
    on the OpenEPaperLink Access Point. The switch:

    - Displays the current state of the setting (on/off)
    - Allows toggling the setting directly from the UI
    - Updates when the setting is changed from other sources
    - Shows appropriate icons based on the feature being controlled

    When toggled, the switch sends an HTTP request to the AP to update
    the configuration value (1 for on, 0 for off).
    """

    def __init__(self, hub, key: str, name: str, icon: str, description: str) -> None:
        """Initialize the switch entity.

        Sets up the switch with appropriate name, unique ID, icon, and
        category based on the provided configuration.

        Args:
            hub: Hub instance for AP communication
            key: Configuration key on the AP
            name: Human-readable name for the UI
            icon: Material Design Icons identifier
            description: Detailed description of the switch's purpose
        """
        self._hub = hub
        self._key = key
        # self._attr_name = f"AP {name}"
        self._attr_unique_id = f"{hub.entry.entry_id}_{key}"
        self._attr_icon = icon
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_has_entity_name = True
        self._attr_translation_key = key
        self._description = description

    @property
    def device_info(self):
        """Return device info for the AP.

        Associates this switch entity with the AP device in Home Assistant
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

        A switch entity is available if:

        - The AP is online
        - The configuration key exists in the AP's config

        Returns:
            bool: True if the switch is available, False otherwise
        """
        return self._hub.online and self._key in self._hub.ap_config

    @property
    def is_on(self) -> bool | None:
        """Return True if entity is on.

        Converts the numeric value from the AP configuration (0 or 1)
        to a boolean for the switch state.

        Returns:
            bool: True if the setting is enabled (1), False if disabled (0)
            None: If the entity is not available
        """
        if not self.available:
            return None
        return bool(int(self._hub.ap_config.get(self._key, 0)))

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on.

        Sends a request to the AP to set the configuration value to 1,
        enabling the feature controlled by this switch.

        Args:
            **kwargs: Additional arguments (not used)
        """
        await set_ap_config_item(self._hub, self._key, 1)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off.

        Sends a request to the AP to set the configuration value to 0,
        disabling the feature controlled by this switch.

        Args:
            **kwargs: Additional arguments (not used)
        """
        await set_ap_config_item(self._hub, self._key, 0)

    @callback
    def _handle_ap_config_update(self):
        """Handle updated AP configuration.

        Called when the AP configuration changes. Updates the switch state
        to reflect the new value from the AP, ensuring the UI stays in sync
        with the actual AP settings.
        """
        self.async_write_ha_state()

    @callback
    def _handle_connection_status(self, is_online: bool):
        """Handle connection status updates.

        Updates the switch's availability state when the AP connection
        status changes. This ensures the switch appears as unavailable
        when the AP is offline.

        Args:
            is_online: Boolean indicating if the AP is online
        """
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Register callbacks when entity is added to Home Assistant.

        Sets up two dispatcher listeners:

        1. AP configuration updates - to refresh the switch when settings change
        2. Connection status updates - to update availability when AP connects/disconnects

        This ensures the switch stays in sync with the actual AP configuration
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

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up switch entities for AP configuration.

    Creates switch entities for all defined AP configuration options
    based on the SWITCH_ENTITIES definition list.

    For each defined switch:

    1. Creates an APConfigSwitch instance with appropriate configuration
    2. Ensures the AP configuration is loaded before creating entities
    3. Adds all created entities to Home Assistant

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

    # Create switch entities from configuration
    for config in SWITCH_ENTITIES:
        entities.append(
            APConfigSwitch(
                hub,
                config["key"],
                config["name"],
                config["icon"],
                config["description"]
            )
        )

    async_add_entities(entities)