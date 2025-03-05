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

@dataclass( kw_only=True, frozen=True)
class OpenEPaperLinkSensorEntityDescription(SensorEntityDescription):
    """Class describing OpenEPaperLink sensor entities."""
    key: str
    name: str
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None
    native_unit_of_measurement : str | None = None
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
        value_fn=lambda data: datetime.fromtimestamp(data.get("sys_time", 0),tz=timezone.utc),
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
        value_fn=lambda data: datetime.fromtimestamp(data.get("last_seen", 0),tz=timezone.utc),
        icon="mdi:history",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="next_update",
        name="Next Update",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: datetime.fromtimestamp(data.get("next_update", 0),tz=timezone.utc),
        icon="mdi:update",
    ),
    OpenEPaperLinkSensorEntityDescription(
        key="next_checkin",
        name="Next Checkin",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda data: datetime.fromtimestamp(data.get("next_checkin", 0),tz=timezone.utc),
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

def _calculate_battery_percentage(voltage: int) -> int:
    """Calculate battery percentage from voltage."""
    if not voltage:
        return 0
    percentage = ((voltage / 1000) - 2.20) * 250
    return max(0, min(100, int(percentage)))


class OpenEPaperLinkBaseSensor(SensorEntity):
    """Base class for all OpenEPaperLink sensors."""

    entity_description: OpenEPaperLinkSensorEntityDescription

    def __init__(self, hub, description: OpenEPaperLinkSensorEntityDescription) -> None:
        """Initialize the sensor."""
        self._hub = hub
        self.entity_description = description

class OpenEPaperLinkTagSensor(OpenEPaperLinkBaseSensor):
    def __init__(self, hub, tag_mac: str, description: OpenEPaperLinkSensorEntityDescription) -> None:
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
        """Return if entity is available."""
        return self._tag_mac in self._hub.tags

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.available or self.entity_description.value_fn is None:
            return None
        return self.entity_description.value_fn(self._hub.get_tag_data(self._tag_mac))

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        if self.entity_description.attr_fn is None:
            return None

        return self.entity_description.attr_fn(self._hub.get_tag_data(self._tag_mac))

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to register update signal handler."""
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_tag_update_{self._tag_mac}",
                self._handle_update,
            )
        )

    @callback
    def _handle_update(self) -> None:
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

class OpenEPaperLinkAPSensor(OpenEPaperLinkBaseSensor):
    """Sensor class for OpenEPaperLink AP."""

    def __init__(self, hub, description: OpenEPaperLinkSensorEntityDescription) -> None:
        """Initialize the AP sensor."""
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
            model="esp32",
            manufacturer="OpenEPaperLink",
        )

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self._hub.online

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if not self.available or self.entity_description.value_fn is None:
            return None
        return self.entity_description.value_fn(self._hub.ap_status)

    async def async_added_to_hass(self) -> None:
        """Run when entity is added to register update signal handler."""
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
        """Handle updated data from the coordinator."""
        self.async_write_ha_state()

    @callback
    def _handle_connection_status(self, is_online: bool) -> None:
        """Handle connection status updates."""
        self.async_write_ha_state()

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the OpenEPaperLink sensors."""
    hub = hass.data[DOMAIN][entry.entry_id]

    # Set up AP sensors
    ap_sensors = [OpenEPaperLinkAPSensor(hub, description) for description in AP_SENSOR_TYPES]
    async_add_entities(ap_sensors)

    @callback
    def async_add_tag_sensor(tag_mac: str) -> None:
        """Add sensors for a new tag."""
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
    """Convert a capabilities number into a list of capabilities."""
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
