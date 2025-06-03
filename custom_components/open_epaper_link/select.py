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
    """Base mapping class for handling value-to-option mapping.

    Provides bidirectional mapping between internal values used by the AP
    and human-readable options shown in the UI. This enables:

    - Converting raw numeric values to readable strings for display
    - Converting user-selected strings back to the correct values for the AP
    - Generating lists of valid options for dropdown menus

    For example, it can map brightness level 255 to "100%" and vice versa.

    Attributes:
        value_to_option: Dictionary mapping internal values to display options
        option_to_value: Dictionary mapping display options to internal values
        options: List of all available display options for selection
    """

    def __init__(self, mapping: dict[int | str, str]):
        """Initialize bidirectional mapping between values and display options.

        Creates three data structures for efficient value-option conversion:

        1. value_to_option: Maps internal values to display options
        2. option_to_value: Maps display options back to internal values
        3. options: List of all available display options for dropdowns

        Examples:
            OptionMapping({0: "off", 255: "100%"})

            - Maps internal value 0 to display option "off"
            - Maps internal value 255 to display option "100%"
            - Creates reverse mappings to convert back after user selection

        The mapping is used to:

        - Display human-readable options in the Home Assistant UI
        - Convert user selections back to the values expected by the AP API
        - Provide consistent options for all instances of a select entity

        Args:
            mapping: Dictionary with keys as internal values (int or str) and
                    values as human-readable display options (str)
        """
        self.value_to_option = mapping
        self.option_to_value = {v: k for k, v in mapping.items()}
        self.options = list(mapping.values())

    def get_option(self, value: int | str) -> str | None:
        """Get the display option for a given value.

        Converts internal values from the AP to human-readable options
        for display in the UI.

        Args:
            value: Internal value to convert

        Returns:
            str: Corresponding display option if found
            None: If no mapping exists for the value
        """
        return self.value_to_option.get(value)

    def get_value(self, option: str) -> int | str | None:
        """Get the internal value for a given display option.

        Converts a user-selected option back to the internal value
        needed by the AP.

        Args:
            option: Display option selected by the user

        Returns:
            int|str: Corresponding internal value if found
            None: If no mapping exists for the option
        """
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
"""Maps IEEE 802.15.4 channel numbers to display options.

Channel 0 is special and means "automatic channel selection",
while others represent specific frequency channels.
"""

BRIGHTNESS_MAPPING = OptionMapping({
    0: "off",
    15: "10%",
    31: "25%",
    127: "50%",
    191: "75%",
    255: "100%"
})
"""Maps LED brightness levels to percentage display options.

Values range from 0 (off) to 255 (maximum brightness),
with intermediate values for different brightness levels.
"""

TFT_BRIGHTNESS_MAPPING = OptionMapping({
    0: "off",
    20: "10%",
    64: "25%",
    128: "50%",
    192: "75%",
    255: "100%"
})
"""Maps TFT display brightness levels to percentage display options.

Similar to LED brightness but with different value ranges optimized
for TFT display hardware. Values range from 0 (off) to 255 (maximum).
"""

MAX_SLEEP_MAPPING = OptionMapping({
    0: "shortest (40 sec)",
    5: "5 min",
    10: "10 min",
    30: "30 min",
    60: "1 hour"
})
"""Maps maximum sleep duration settings for tags.

Determines how long tags will sleep between check-ins,
affecting battery life and update responsiveness.
"""

LOCK_INVENTORY_MAPPING = OptionMapping({
    0: "no",
    1: "locked: don't add new tags",
    2: "learning: only add booting tags"
})
"""Maps tag inventory lock modes for AP discovery behavior.

Controls how the AP handles new tags that attempt to connect:

- 0: All new tags are accepted
- 1: No new tags are accepted
- 2: Only booting tags are accepted
"""

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
"""Maps WiFi transmit power levels in dBm.

Controls the AP's WiFi transmission power.
"""

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
"""Maps language codes to human-readable language names.

Determines the language used in some tag content types that support localization.
"""

DISCOVERY_MAPPING = OptionMapping({
    0: "Multicast",
    1: "Broadcast",
})
"""Maps network discovery methods for AP-to-tag communication.

Controls how the AP discovers tags on the network:

- 0: Uses multicast for discovery (more efficient but less compatible)
- 1: Uses broadcast for discovery (more compatible but less efficient)
"""

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
"""Maps Sub-GHz radio channel settings.

Controls the frequency used by the optional Sub-GHz radio
for long-range communication with compatible tags.
Different regions have different legal frequency allocations,
with separate bands for Europe and North America.
"""

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
"""Configuration for all select entities to create for the AP.

This list defines all the select entities that will be created during
integration setup. Each dictionary contains:

- key: Configuration parameter key in the AP's configuration system.
    This matches the key used in HTTP API calls to the AP.
- name: Human-readable name for display in the UI. This will be combined
    with "AP" to form the full entity name.
- icon: Material Design Icons identifier for the entity.
    Format is "mdi:icon-name" matching the icon library.
- mapping: OptionMapping instance to handle conversion between internal
    values and user-friendly display options.

The order of entities in this list determines their order in the UI.
Each entity corresponds to a specific configuration option on the AP
and allows users to change that setting through Home Assistant.

Some common settings include:

- channel: IEEE 802.15.4 wireless channel for tag communication
- led: RGB LED brightness on the AP
- maxsleep: Maximum time tags can sleep between check-ins
- lock: Tag inventory management mode
- language: Content mode language for some tag types
- discovery: Network discovery method for finding tags
- subghzchannel: Sub-GHz radio frequency channel (if equipped)
"""


class APConfigSelect(SelectEntity):
    """Base select entity for AP configuration.

    Provides a dropdown selection entity that controls a specific
    configuration setting on the OpenEPaperLink Access Point.

    When the user selects an option, the corresponding value is sent
    to the AP via HTTP and the local state is updated. The entity
    also responds to configuration changes from other sources.
    """

    def __init__(self, hub, key: str, name: str, icon: str, mapping: OptionMapping) -> None:
        """Initialize the select entity.

        Sets up the select entity with appropriate name, icon, and options.

        Args:
            hub: Hub instance for AP communication
            key: Configuration key on the AP
            name: Human-readable name for the UI
            icon: Material Design Icons identifier
            mapping: OptionMapping for value/option conversion
        """
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
        """Return device info for the AP.

        Associates this select entity with the AP device in Home Assistant
        using the domain and "ap" as the identifier.

        Returns:
            dict: Device information dictionary
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

        A select entity is available if:

        - The AP is online
        - The configuration key exists in the AP's config

        Returns:
            bool: True if the entity is available, False otherwise
        """
        """Return if entity is available."""
        return self._hub.online and self._key in self._hub.ap_config

    @property
    def current_option(self) -> str | None:
        """Return the current selected option.

        Converts the current value from the AP configuration to
        the corresponding display option using the mapping.

        Returns:
            str: Currently selected option
            None: If entity is unavailable or value has no mapping
        """
        if not self.available:
            return None
        value = self._hub.ap_config.get(self._key)
        return self._mapping.get_option(value)

    async def async_select_option(self, option: str) -> None:
        """Change the selected option.

        Converts the selected option to its internal value and
        sends it to the AP via the hub.

        Args:
            option: The option selected by the user
        """
        value = self._mapping.get_value(option)
        if value is not None:
            await set_ap_config_item(self._hub, self._key, value)

    @callback
    def _handle_ap_config_update(self):
        """Handle updated AP configuration.

        Called when the AP configuration changes. Updates the entity state
        to reflect the new value from the AP.
        """
        self.async_write_ha_state()

    @callback
    def _handle_connection_status(self, is_online: bool):
        """Handle connection status updates.

        Updates the entity's availability state when the AP connection
        status changes.

        Args:
            is_online: Boolean indicating if the AP is online
        """
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
    """Special handling for time selection.

    Extends the base select entity with specialized handling for
    hour-based time selection. Instead of using a predefined mapping,
    it dynamically generates a mapping with 24 hours in HH:00 format.

    This is used for sleep time configuration on the AP, which defines
    periods when tag updates are disabled.
    """

    def __init__(self, hub, key: str, name: str, icon: str) -> None:
        """Initialize time select entity.

        Creates a specialized select entity for time selection with
        24 options representing hours of the day (00:00 to 23:00).

        Args:
            hub: Hub instance for AP communication
            key: Configuration key on the AP
            name: Human-readable name for the UI
            icon: Material Design Icons identifier
        """
        # Create 24-hour time mapping
        time_mapping = OptionMapping({
            i: f"{i:02d}:00" for i in range(24)
        })
        super().__init__(hub, key, name, icon, time_mapping)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up select entities for AP configuration.

    Creates select entities for all defined AP configuration options
    based on the SELECT_ENTITIES definition list.

    Additionally, creates time-specific select entities for sleep time
    configuration (start and end hours when updates are disabled).

    Args:
        hass: Home Assistant instance
        entry: Configuration entry
        async_add_entities: Callback to register new entities
    """
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
