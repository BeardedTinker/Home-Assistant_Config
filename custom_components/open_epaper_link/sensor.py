"""Sensor implementation for OpenEPaperLink integration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Final

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    SIGNAL_STRENGTH_DECIBELS,
    PERCENTAGE,
    UnitOfTemperature,
    UnitOfElectricPotential, UnitOfInformation, UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

import logging

from .tag_types import get_hw_string, get_hw_dimensions

_LOGGER: Final = logging.getLogger(__name__)

from .const import DOMAIN
from .hub import Hub


@dataclass(kw_only=True, frozen=True)
class OpenEPaperLinkSensorEntityDescription(SensorEntityDescription):
    """Class describing OpenEPaperLink sensor entities.

    Extends the standard Home Assistant sensor description with
    additional fields specific to OpenEPaperLink sensors, particularly
    the value extraction function that pulls data from the raw state.

    This class acts as a blueprint for creating sensor entities with
    consistent behavior and appearance across the integration.

    Attributes:
        key: Unique identifier for the sensor type
        name: Human-readable name for the sensor
        device_class: Device class for standardized behavior
        state_class: State class for statistics and history
        native_unit_of_measurement: Unit for the sensor value
        suggested_unit_of_measurement: Preferred unit for display
        suggested_display_precision: Number of decimal places to display
        entity_category: Category for UI organization
        entity_registry_enabled_default: Whether enabled by default
        value_fn: Function to extract the value from raw state data
        attr_fn: Optional function to extract extra attributes
        icon: Material Design Icons identifier
    """
    key: str
    name: str
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    native_unit_of_measurement: str | None = None
    suggested_unit_of_measurement: UnitOfInformation | None = None
    suggested_display_precision: int | None = None
    entity_category: EntityCategory | None = None
    entity_registry_enabled_default: bool = True
    value_fn: Callable[[dict], Any]
    attr_fn: Callable[[dict], Any] = None
    icon: str


AP_SENSOR_TYPES: tuple[OpenEPaperLinkSensorEntityDescription, ...] = (
    OpenEPaperLinkSensorEntityDescription(
        key="ip",
        name="IP Address",
        value_fn=lambda data: data.get("ip"),
        icon="mdi:ip",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="wifi_ssid",
        name="WiFi SSID",
        value_fn=lambda data: data.get("wifi_ssid"),
        icon="mdi:wifi-settings",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="record_count",
        name="Tag count",
        state_class=SensorStateClass.TOTAL,
        value_fn=lambda data: data.get("record_count"),
        icon="mdi:tag-multiple",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="db_size",
        name="Database Size",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.KIBIBYTES,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: int(data.get("db_size", 0)),
        icon="mdi:database-settings",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="little_fs_free",
        name="LittleFS Free",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.MEBIBYTES,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: int(data.get("little_fs_free", 0)),
        icon="mdi:database-outline",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="ap_state",
        name="State",
        value_fn=lambda data: data.get("ap_state"),
        icon="mdi:access-point",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="run_state",
        name="Run State",
        value_fn=lambda data: data.get("run_state"),
        icon="mdi:cog",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="wifi_rssi",
        name="WiFi RSSI",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("rssi"),
        icon="mdi:wifi-strength-4",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="heap",
        name="Free Heap",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.KIBIBYTES,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: int(data.get("heap", 0)),
        icon="mdi:chip",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="sys_time",
        name="System Time",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda data: datetime.fromtimestamp(data.get("sys_time", 0), tz=timezone.utc),
        icon="mdi:clock-outline",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="uptime",
        name="Uptime",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("uptime"),
        icon="mdi:timer",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="low_battery_tag_count",
        name="Low Battery Tags",
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda data: data.get("low_battery_count"),
        icon="mdi:battery-alert",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="timeout_tag_count",
        name="Timed out Tags",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=None,
        value_fn=lambda data: data.get("timeout_count"),
        icon="mdi:tag-off",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="ps_ram_free",
        name="PSRAM Free",
        device_class=SensorDeviceClass.DATA_SIZE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfInformation.BYTES,
        suggested_unit_of_measurement=UnitOfInformation.MEBIBYTES,
        suggested_display_precision=3,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: int(data.get("ps_ram_free", 0)),
        icon="mdi:memory",
    )
)
"""Definitions for all AP-related sensor entities.

This tuple defines all the sensor entities created for the Access Point.
Each entry is an OpenEPaperLinkSensorEntityDescription that specifies
how to create and populate a sensor entity from AP data.

Sensor types include:

- Network information (IP, WiFi SSID, RSSI)
- System metrics (heap, database size, uptime)
- Tag statistics (count, low battery, timeout)
- Operational state (AP state, run state)

Each sensor uses a value_fn to extract the relevant data from
the hub's AP status dictionary.
"""
TAG_SENSOR_TYPES: tuple[OpenEPaperLinkSensorEntityDescription, ...] = (
    OpenEPaperLinkSensorEntityDescription(
        key="temperature",
        name="Temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda data: data.get("temperature"),
        icon="mdi:thermometer",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="battery_voltage",
        name="Battery Voltage",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("battery_mv"),
        icon="mdi:battery",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="battery_percentage",
        name="Battery Percentage",
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=PERCENTAGE,
        value_fn=lambda data: _calculate_battery_percentage(data.get("battery_mv", 0)),
        icon="mdi:battery",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="last_seen",
        name="Last Seen",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: datetime.fromtimestamp(data.get("last_seen", 0), tz=timezone.utc),
        icon="mdi:history",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="next_update",
        name="Next Update",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: datetime.fromtimestamp(data.get("next_update", 0), tz=timezone.utc),
        icon="mdi:update",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="next_checkin",
        name="Next Checkin",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: datetime.fromtimestamp(data.get("next_checkin", 0), tz=timezone.utc),
        icon="mdi:clock-check",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="lqi",
        name="Link Quality Index",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("lqi"),
        icon="mdi:signal-cellular-outline",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="rssi",
        name="RSSI",
        device_class=SensorDeviceClass.SIGNAL_STRENGTH,
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("rssi"),
        icon="mdi:signal-distance-variant",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="pending_updates",
        name="Pending Updates",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("pending"),
        icon="mdi:sync-circle",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="content_mode",
        name="Content Mode",
        value_fn=lambda data: data.get("content_mode"),
        icon="mdi:view-grid-outline",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="wakeup_reason",
        name="Wakeup Reason",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("wakeup_reason"),
        icon="mdi:power",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="capabilities",
        name="Capabilities",
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("capabilities"),
        attr_fn=lambda data: {
            "raw_value": data.get("capabilities", 0),
            "binary_value": format(data.get("capabilities", 0), '08b'),
            "capabilities": get_capabilities(data.get("capabilities", 0))
        },
        icon="mdi:list-box-outline",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="update_count",
        name="Update Count",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("update_count"),
        icon="mdi:counter",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="width",
        name="Width",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("width"),
        icon="mdi:arrow-expand-horizontal",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="height",
        name="Height",
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("height"),
        icon="mdi:arrow-expand-vertical",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="runtime",
        name="Runtime",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.TOTAL,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("runtime", 0),
        icon="mdi:timer-outline",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="boot_count",
        name="Boot Count",
        state_class=SensorStateClass.TOTAL,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("boot_count", 0),
        icon="mdi:restart",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="checkin_count",
        name="Checkin Count",
        state_class=SensorStateClass.TOTAL,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("checkin_count", 0),
        icon="mdi:clock-check",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="block_requests",
        name="Block Requests",
        state_class=SensorStateClass.TOTAL,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda data: data.get("block_requests", 0),
        icon="mdi:transfer",
    ),

)
"""Definitions for all tag-related sensor entities.

This tuple defines all the sensor entities created for each ESL.
Each entry is an OpenEPaperLinkSensorEntityDescription that specifies
how to create and populate a sensor entity from tag data.

Sensor types include:

- Telemetry data (temperature, battery, signal strength)
- Status information (last seen, next update, pending)
- Hardware capabilities (runtime, boot count, display size)
- Technical details (wakeup reason, capabilities flags)

Each sensor uses a value_fn to extract the relevant data from
the hub's tag data dictionary.
"""


def _calculate_battery_percentage(voltage: int) -> int:
    """Calculate battery percentage from raw voltage.

    Converts a battery voltage reading in millivolts to an estimated
    percentage based on the known discharge curve of a typical
    lithium battery used in ESL tags.

    The formula approximates:

    - 100% at around 3.0V
    - 0% at around 2.2V

    Args:
        voltage: Battery voltage in millivolts

    Returns:
        int: Battery percentage (0-100), clamped to valid range
    """
    if not voltage:
        return 0
    percentage = ((voltage / 1000) - 2.20) * 250
    return max(0, min(100, int(percentage)))


class OpenEPaperLinkBaseSensor(SensorEntity):
    """Base class for all OpenEPaperLink sensors.

    Provides common functionality and attributes for all sensor entities
    in the integration, whether they're associated with the AP or with
    individual tags.

    This base class handles the interaction with the entity description
    system to ensure consistent behavior across all sensor types.
    """

    entity_description: OpenEPaperLinkSensorEntityDescription

    def __init__(self, hub, description: OpenEPaperLinkSensorEntityDescription) -> None:
        """Initialize the sensor.

        Sets up the sensor with the hub connection and entity description.
        The description contains all the information needed to extract
        values and format the sensor's display.

        Args:
            hub: Hub instance for data access
            description: Sensor entity description
        """
        self._hub = hub
        self.entity_description = description


class OpenEPaperLinkTagSensor(OpenEPaperLinkBaseSensor):
    """Sensor class for OpenEPaperLink tag data.

    Provides sensor entities that display data from individual ESL tags,
    such as battery level, temperature, signal strength, and status
    information.

    Each tag has multiple sensor entities created from the TAG_SENSOR_TYPES
    definitions, with values extracted from the tag's data in the hub.
    """
    def __init__(self, hub, tag_mac: str, description: OpenEPaperLinkSensorEntityDescription) -> None:
        """Initialize the tag sensor.

    Sets up the sensor with the tag MAC, hub connection, and description.
    Configures the device info to associate the sensor with the correct
    tag device in the Home Assistant UI.

    Args:
        hub: Hub instance for data access
        tag_mac: MAC address of the tag
        description: Sensor entity description
    """
        super().__init__(hub, description)
        self._tag_mac = tag_mac

        name_base = self._hub.get_tag_data(tag_mac).get("tag_name", tag_mac)
        # self._attr_name = f"{name_base} {description.name}"
        self._attr_has_entity_name = True
        self._attr_translation_key = description.key

        # Set unique ID without domain
        self._attr_unique_id = f"{tag_mac}_{description.key}"

        # Set entity_id with the sensor type included
        self.entity_id = f"{DOMAIN}.{tag_mac.lower()}_{description.key}"

        firmware_version = str(self._hub.get_tag_data(tag_mac).get("version", ""))

        tag_data = self._hub.get_tag_data(self._tag_mac)
        hw_type = tag_data.get("hw_type", 0)
        hw_string = get_hw_string(hw_type)
        width, height = get_hw_dimensions(hw_type)

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._tag_mac)},
            name=name_base,
            manufacturer="OpenEPaperLink",
            model=hw_string,
            via_device=(DOMAIN, "ap"),
            sw_version=f"0x{int(firmware_version, 16):X}" if firmware_version else "Unknown",
            serial_number=self._tag_mac,
            hw_version=f"{width}x{height}",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available.

        A tag sensor is available if the tag is known to the hub.

        Returns:
            bool: True if the sensor is available, False otherwise
        """
        return self._tag_mac in self._hub.tags

    @property
    def native_value(self):
        """Return the state of the sensor.

        Uses the value_fn from the entity description to extract the
        appropriate value from the tag's data dictionary. This allows
        each sensor type to extract different data using the same method.

        Returns:
            Any: The sensor state value
            None: If the sensor is not available
        """
        if not self.available or self.entity_description.value_fn is None:
            return None
        return self.entity_description.value_fn(self._hub.get_tag_data(self._tag_mac))

    @property
    def extra_state_attributes(self):
        """Return the state attributes.

        If the entity description includes an attr_fn, uses it to extract
        additional attributes for the sensor from the tag's data dictionary.

        Returns:
            dict: Additional attributes for the sensor
            None: If no attr_fn is defined
        """
        if self.entity_description.attr_fn is None:
            return None

        return self.entity_description.attr_fn(self._hub.get_tag_data(self._tag_mac))

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to register update signal handler.

        Sets up a dispatcher listener for tag updates to refresh the
        sensor's value when the tag data changes.

        This ensures the sensor stays in sync with the actual tag data
        without requiring polling.
        """
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_tag_update_{self._tag_mac}",
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self) -> None:
        """Handle updated data from the coordinator.

        Called when the tag's data is updated. Triggers a state update
        to refresh the sensor's value and attributes in the UI.
        """
        self.async_write_ha_state()


class OpenEPaperLinkAPSensor(OpenEPaperLinkBaseSensor):
    """Sensor class for OpenEPaperLink AP data.

    Provides sensor entities that display data from the Access Point,
    such as connection status, memory usage, tag counts, and system state.

    Each AP has multiple sensor entities created from the AP_SENSOR_TYPES
    definitions, with values extracted from the AP's status data in the hub.
    """

    def __init__(self, hub, description: OpenEPaperLinkSensorEntityDescription) -> None:
        """Initialize the AP sensor.

        Sets up the sensor with the hub connection and description.
        Configures the device info to associate the sensor with the
        AP device in the Home Assistant UI.

        Args:
            hub: Hub instance for data access
            description: Sensor entity description
        """
        super().__init__(hub, description)

        # Set name and unique_id
        # self._attr_name = f"AP {description.name}"
        self._attr_has_entity_name = True
        self._attr_translation_key = description.key
        self._attr_unique_id = f"{self._hub.entry.entry_id}_{description.key}"

        # Set device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, "ap")},
            name="OpenEPaperLink AP",
            model=self._hub.ap_model,
            manufacturer="OpenEPaperLink",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available.

        An AP sensor is available if the AP is online.

        Returns:
            bool: True if the sensor is available, False otherwise
        """
        return self._hub.online

    @property
    def native_value(self):
        """Return the state of the sensor.

        Uses the value_fn from the entity description to extract the
        appropriate value from the AP's status dictionary. This allows
        each sensor type to extract different data using the same method.

        Returns:
            Any: The sensor state value
            None: If the sensor is not available
        """
        if not self.available or self.entity_description.value_fn is None:
            return None
        return self.entity_description.value_fn(self._hub.ap_status)

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to register update signal handlers.

        Sets up two dispatcher listeners:

        1. AP updates - to refresh the sensor when AP status changes
        2. Connection status updates - to update availability when AP connects/disconnects

        This ensures the sensor stays in sync with the actual AP status
        without requiring polling.
        """
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_ap_update",
                self._handle_update,
            )
        )
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_connection_status",
                self._handle_connection_status,
            )
        )

    @callback
    def _handle_update(self) -> None:
        """Handle updated data from the coordinator.

        Called when the AP's status is updated. Triggers a state update
        to refresh the sensor's value in the UI.
        """
        self.async_write_ha_state()

    @callback
    def _handle_connection_status(self, is_online: bool) -> None:
        """Handle connection status updates.

        Updates the sensor's availability state when the AP connection
        status changes.

        Args:
            is_online: Boolean indicating if the AP is online
        """
        self.async_write_ha_state()


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the OpenEPaperLink sensors.

    Creates sensor entities for both the AP and all known tags:

    1. AP sensors based on AP_SENSOR_TYPES definitions
    2. Tag sensors for each known tag based on TAG_SENSOR_TYPES definitions

    Also sets up a callback to add sensors for newly discovered tags.

    Args:
        hass: Home Assistant instance
        entry: Configuration entry
        async_add_entities: Callback to register new entities
    """
    hub = hass.data[DOMAIN][entry.entry_id]

    # Set up AP sensors
    ap_sensors = [OpenEPaperLinkAPSensor(hub, description) for description in AP_SENSOR_TYPES]
    async_add_entities(ap_sensors)

    @callback
    def async_add_tag_sensor(tag_mac: str) -> None:
        """Add sensors for a new tag.

        Creates sensor entities for a newly discovered tag based on the
        TAG_SENSOR_TYPES definitions. Called when a new tag is discovered
        by the integration.

        Args:
            tag_mac: MAC address of the newly discovered tag
        """
        entities = []

        for description in TAG_SENSOR_TYPES:
            sensor = OpenEPaperLinkTagSensor(hub, tag_mac, description)
            entities.append(sensor)

        async_add_entities(entities)

    # Set up sensors for existing tags
    for tag_mac in hub.tags:
        async_add_tag_sensor(tag_mac)

    # Register callback for new tag discovery
    entry.async_on_unload(
        async_dispatcher_connect(
            hass,
            f"{DOMAIN}_tag_discovered",
            async_add_tag_sensor
        )
    )


def get_capabilities(capabilities_value: int) -> list[str]:
    """Convert a capabilities number into a list of capabilities.

    Translates the binary capabilities flags from the tag into a
    human-readable list of capability names. Each bit in the value
    represents a different capability.

    Capabilities include:

    - SUPPORTS_COMPRESSION: Tag supports compressed image data
    - SUPPORTS_CUSTOM_LUTS: Tag supports custom display LUTs
    - HAS_EXT_POWER: Tag has external power connection
    - HAS_WAKE_BUTTON: Tag has physical wake button
    - HAS_NFC: Tag has NFC capability
    - NFC_WAKE: Tag can wake from NFC scan

    Args:
        capabilities_value: Integer with capability flags

    Returns:
        list[str]: List of capability string names
    """
    capability_map = {
        0x02: "SUPPORTS_COMPRESSION",
        0x04: "SUPPORTS_CUSTOM_LUTS",
        0x08: "ALT_LUT_SIZE",
        0x10: "HAS_EXT_POWER",
        0x20: "HAS_WAKE_BUTTON",
        0x40: "HAS_NFC",
        0x80: "NFC_WAKE"
    }

    capabilities = []
    for flag, name in capability_map.items():
        if capabilities_value & flag:
            capabilities.append(name)

    return capabilities
