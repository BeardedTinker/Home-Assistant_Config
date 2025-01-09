from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .util import set_ap_config_item

import logging

_LOGGER = logging.getLogger(__name__)

# Base mapping class for handling value-to-option mapping
class OptionMapping:
    def __init__(self, mapping: dict[int | str, str]):
        self.value_to_option = mapping
        self.option_to_value = {v: k for k, v in mapping.items()}
        self.options = list(mapping.values())

    def get_option(self, value: int | str) -> str | None:
        return self.value_to_option.get(value)

    def get_value(self, option: str) -> int | str | None:
        return self.option_to_value.get(option)

# Define mappings for different select types
CHANNEL_MAPPING = OptionMapping({
    0: "auto",
    11: "11",
    15: "15",
    20: "20",
    25: "25",
    26: "26"
})

BRIGHTNESS_MAPPING = OptionMapping({
    0: "off",
    15: "10%",
    31: "25%",
    127: "50%",
    191: "75%",
    255: "100%"
})

TFT_BRIGHTNESS_MAPPING = OptionMapping({
    0: "off",
    20: "10%",
    64: "25%",
    128: "50%",
    192: "75%",
    255: "100%"
})

MAX_SLEEP_MAPPING = OptionMapping({
    0: "shortest (40 sec)",
    5: "5 min",
    10: "10 min",
    30: "30 min",
    60: "1 hour"
})

LOCK_INVENTORY_MAPPING = OptionMapping({
    0: "no",
    1: "locked: don't add new tags",
    2: "learning: only add booting tags"
})

WIFI_POWER_MAPPING = OptionMapping({
    78: "19.5 dBm",
    76: "19.0 dBm",
    74: "18.5 dBm",
    68: "17.0 dBm",
    60: "15.0 dBm",
    52: "13.0 dBm",
    44: "11.0 dBm",
    34: "8.5 dBm",
    28: "7.0 dBm",
    20: "5.0 dBm",
    8: "2.0 dBm",
})

LANGUAGE_MAPPING = OptionMapping({
    0: "EN English",
    1: "NL Nederlands",
    2: "DE Deutsch",
    4: "FR Français",
    3: "NO Norsk",
    5: "CZ Čeština",
    6: "SK Slovenčina",
    7: "PL Polski",
    8: "ES Español",
    9: "SV Svenska",
    10: "DK Dansk",
    11: "ET Eesti"
})

DISCOVERY_MAPPING = OptionMapping({
    0: "Multicast",
    1: "Broadcast",
})

SUB_GHZ_MAPPING = OptionMapping({
    0: "disabled",
    100: "100 - 864.000 Mhz (Europe, etc)",
    101: "101 - 865.006 Mhz (Europe, etc)",
    102: "102 - 866.014 Mhz (Europe, etc)",
    103: "103 - 867.020 Mhz (Europe, etc)",
    104: "104 - 868.027 Mhz (Europe, etc)",
    105: "105 - 869.034 Mhz (Europe, etc)",
    200: "200 - 903.000 Mhz (US, etc)",
    201: "201 - 907.027 Mhz (US, etc)",
    202: "202 - 911.054 Mhz (US, etc)",
    203: "203 - 915.083 Mhz (US, etc)",
    204: "204 - 919.110 Mhz (US, etc)",
    205: "205 - 923.138 Mhz (US, etc)"
})

# Mapping of select entities to their configurations
SELECT_ENTITIES = [
    {
        "key": "channel",
        "name": "IEEE 802.15.4 channel",
        "icon": "mdi:wifi",
        "mapping": CHANNEL_MAPPING,
    },
    {
        "key": "led",
        "name": "RGB LED brightness",
        "icon": "mdi:brightness-5",
        "mapping": BRIGHTNESS_MAPPING,
    },
    {
        "key": "tft",
        "name": "TFT brightness",
        "icon": "mdi:brightness-5",
        "mapping": TFT_BRIGHTNESS_MAPPING,
    },
    {
        "key": "maxsleep",
        "name": "Maximum Sleep",
        "icon": "mdi:sleep",
        "mapping": MAX_SLEEP_MAPPING,
    },
    {
        "key": "lock",
        "name": "Lock tag inventory",
        "icon": "mdi:lock",
        "mapping": LOCK_INVENTORY_MAPPING,
    },
    {
        "key": "wifipower",
        "name": "Wifi power",
        "icon": "mdi:wifi-strength-4",
        "mapping": WIFI_POWER_MAPPING,
    },
    {
        "key": "language",
        "name": "Language",
        "icon": "mdi:translate",
        "mapping": LANGUAGE_MAPPING,
    },
    {
        "key": "discovery",
        "name": "Discovery Method",
        "icon": "mdi:access-point-network",
        "mapping": DISCOVERY_MAPPING
    },
    {
        "key": "subghzchannel",
        "name": "Sub-GHz channel",
        "icon": "mdi:antenna",
        "mapping": SUB_GHZ_MAPPING
    }
]

class APConfigSelect(SelectEntity):
    """Base select entity for AP configuration."""

    def __init__(self, hub, key: str, name: str, icon: str, mapping: OptionMapping) -> None:
        """Initialize the select entity."""
        self._hub = hub
        self._key = key
        # self._attr_name = f"AP {name}"
        self._attr_has_entity_name = True
        self._attr_translation_key = key
        self._attr_unique_id = f"{hub.entry.entry_id}_{key}"
        self._attr_icon = icon
        self._attr_entity_category = EntityCategory.CONFIG
        self._mapping = mapping
        self._attr_options = mapping.options
        self._available = False

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
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if not self.available:
            return None
        value = self._hub.ap_config.get(self._key)
        return self._mapping.get_option(value)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        value = self._mapping.get_value(option)
        if value is not None:
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

class APTimeHourSelect(APConfigSelect):
    """Special handling for time selection."""

    def __init__(self, hub, key: str, name: str, icon: str) -> None:
        """Initialize time select entity."""
        # Create 24-hour time mapping
        time_mapping = OptionMapping({
            i: f"{i:02d}:00" for i in range(24)
        })
        super().__init__(hub, key, name, icon, time_mapping)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up select entities for AP configuration."""
    hub = hass.data[DOMAIN][entry.entry_id]

    # Wait for initial AP config to be loaded
    if not hub.ap_config:
        await hub.async_update_ap_config()

    entities: list[SelectEntity] = []

    # Add standard select entities
    for config in SELECT_ENTITIES:
        entities.append(APConfigSelect(
            hub,
            config["key"],
            config["name"],
            config["icon"],
            config["mapping"]
        ))

    # Add time select entities
    entities.extend([
        APTimeHourSelect(hub, "sleeptime1", "No updates between 1 (from)", "mdi:sleep"),
        APTimeHourSelect(hub, "sleeptime2", "No updates between 2 (to)", "mdi:sleep"),
    ])

    async_add_entities(entities)