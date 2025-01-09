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
    }
]

class APConfigSwitch(SwitchEntity):
    """Switch entity for AP configuration."""

    def __init__(self, hub, key: str, name: str, icon: str, description: str) -> None:
        """Initialize the switch entity."""
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
    def is_on(self) -> bool | None:
        """Return True if entity is on."""
        if not self.available:
            return None
        return bool(int(self._hub.ap_config.get(self._key, 0)))

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the entity on."""
        await set_ap_config_item(self._hub, self._key, 1)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the entity off."""
        await set_ap_config_item(self._hub, self._key, 0)

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

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up switch entities for AP configuration."""
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