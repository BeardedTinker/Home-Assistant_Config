"""Support for the Mikrotik Router binary sensor service."""

import logging
from typing import Any, Dict, Optional

from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    ATTR_DEVICE_CLASS,
    ATTR_ATTRIBUTION,
)
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC

from .const import (
    DOMAIN,
    DATA_CLIENT,
    ATTRIBUTION,
    CONF_SENSOR_PPP,
    DEFAULT_SENSOR_PPP,
    CONF_SENSOR_PORT_TRACKER,
    DEFAULT_SENSOR_PORT_TRACKER,
)

_LOGGER = logging.getLogger(__name__)

ATTR_LABEL = "label"
ATTR_GROUP = "group"
ATTR_PATH = "data_path"
ATTR_ATTR = "data_attr"
ATTR_CTGR = "entity_category"

SENSOR_TYPES = {
    "system_fwupdate": {
        ATTR_DEVICE_CLASS: BinarySensorDeviceClass.UPDATE,
        ATTR_LABEL: "Firmware update",
        ATTR_GROUP: "System",
        ATTR_PATH: "fw-update",
        ATTR_ATTR: "available",
        ATTR_CTGR: EntityCategory.DIAGNOSTIC,
    },
}

DEVICE_ATTRIBUTES_IFACE = [
    "running",
    "enabled",
    "comment",
    "client-ip-address",
    "client-mac-address",
    "port-mac-address",
    "last-link-down-time",
    "last-link-up-time",
    "link-downs",
    "actual-mtu",
    "type",
    "name",
    "default-name",
    "poe-out",
]

DEVICE_ATTRIBUTES_IFACE_SFP = [
    "status",
    "auto-negotiation",
    "advertising",
    "link-partner-advertising",
    "sfp-temperature",
    "sfp-supply-voltage",
    "sfp-module-present",
    "sfp-tx-bias-current",
    "sfp-tx-power",
    "sfp-rx-power",
    "sfp-rx-loss",
    "sfp-tx-fault",
    "sfp-type",
    "sfp-connector-type",
    "sfp-vendor-name",
    "sfp-vendor-part-number",
    "sfp-vendor-revision",
    "sfp-vendor-serial",
    "sfp-manufacturing-date",
    "eeprom-checksum",
]

DEVICE_ATTRIBUTES_PPP_SECRET = [
    "connected",
    "service",
    "profile",
    "comment",
    "caller-id",
    "encoding",
]


# ---------------------------
#   format_attribute
# ---------------------------
def format_attribute(attr):
    res = attr.replace("-", " ")
    res = res.capitalize()
    res = res.replace(" ip ", " IP ")
    res = res.replace(" mac ", " MAC ")
    res = res.replace(" mtu", " MTU")
    res = res.replace("Sfp", "SFP")
    res = res.replace("Poe", "POE")
    res = res.replace(" tx", " TX")
    res = res.replace(" rx", " RX")
    return res


# ---------------------------
#   format_value
# ---------------------------
def format_value(res):
    res = res.replace("dhcp", "DHCP")
    res = res.replace("dns", "DNS")
    res = res.replace("capsman", "CAPsMAN")
    res = res.replace("wireless", "Wireless")
    res = res.replace("restored", "Restored")
    return res


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up device tracker for Mikrotik Router component."""
    inst = config_entry.data[CONF_NAME]
    mikrotik_controller = hass.data[DOMAIN][DATA_CLIENT][config_entry.entry_id]
    sensors = {}

    @callback
    def update_controller():
        """Update the values of the controller."""
        update_items(
            inst, config_entry, mikrotik_controller, async_add_entities, sensors
        )

    mikrotik_controller.listeners.append(
        async_dispatcher_connect(
            hass, mikrotik_controller.signal_update, update_controller
        )
    )
    update_controller()


# ---------------------------
#   update_items
# ---------------------------
@callback
def update_items(inst, config_entry, mikrotik_controller, async_add_entities, sensors):
    """Update sensor state from the controller."""
    new_sensors = []

    # Add switches
    for sid, sid_uid, sid_name, sid_ref, sid_func in zip(
        # Data point name
        ["ppp_secret", "interface"],
        # Data point unique id
        ["name", "default-name"],
        # Entry Name
        ["name", "name"],
        # Entry Unique id
        ["name", "port-mac-address"],
        # Tracker function
        [
            MikrotikControllerPPPSecretBinarySensor,
            MikrotikControllerPortBinarySensor,
        ],
    ):
        if (
            sid_func == MikrotikControllerPortBinarySensor
            and not config_entry.options.get(
                CONF_SENSOR_PORT_TRACKER, DEFAULT_SENSOR_PORT_TRACKER
            )
        ):
            continue
        for uid in mikrotik_controller.data[sid]:
            if (
                # Skip if interface is wlan
                sid == "interface"
                and mikrotik_controller.data[sid][uid]["type"] == "wlan"
            ):
                continue
            # Update entity
            item_id = f"{inst}-{sid}-{mikrotik_controller.data[sid][uid][sid_uid]}"
            _LOGGER.debug("Updating binary_sensor %s", item_id)
            if item_id in sensors:
                if sensors[item_id].enabled:
                    sensors[item_id].async_schedule_update_ha_state()
                continue

            # Create new entity
            sid_data = {
                "sid": sid,
                "sid_uid": sid_uid,
                "sid_name": sid_name,
                "sid_ref": sid_ref,
            }
            sensors[item_id] = sid_func(
                inst, uid, mikrotik_controller, config_entry, sid_data
            )
            new_sensors.append(sensors[item_id])

    for sensor in SENSOR_TYPES:
        item_id = f"{inst}-{sensor}"
        _LOGGER.debug("Updating binary_sensor %s", item_id)
        if item_id in sensors:
            if sensors[item_id].enabled:
                sensors[item_id].async_schedule_update_ha_state()
            continue

        sensors[item_id] = MikrotikControllerBinarySensor(
            mikrotik_controller=mikrotik_controller, inst=inst, sensor=sensor
        )
        new_sensors.append(sensors[item_id])

    if new_sensors:
        async_add_entities(new_sensors, True)


class MikrotikControllerBinarySensor(BinarySensorEntity):
    """Define an Mikrotik Controller Binary Sensor."""

    def __init__(self, mikrotik_controller, inst, sensor):
        """Initialize."""
        self._inst = inst
        self._sensor = sensor
        self._ctrl = mikrotik_controller
        if sensor in SENSOR_TYPES:
            self._data = mikrotik_controller.data[SENSOR_TYPES[sensor][ATTR_PATH]]
            self._type = SENSOR_TYPES[sensor]
            self._attr = SENSOR_TYPES[sensor][ATTR_ATTR]
        else:
            self._type = {}
            self._attr = None

        if ATTR_CTGR in self._type:
            self._entity_category = self._type[ATTR_CTGR]
        else:
            self._entity_category = None

        self._device_class = None
        self._state = None
        self._icon = None
        self._unit_of_measurement = None
        self._attrs = {ATTR_ATTRIBUTION: ATTRIBUTION}

    @property
    def name(self) -> str:
        """Return the name."""
        return f"{self._inst} {self._type[ATTR_LABEL]}"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        return self._attrs

    @property
    def unique_id(self) -> str:
        """Return a unique id for this entity."""
        return f"{self._inst.lower()}-{self._sensor.lower()}"

    @property
    def available(self) -> bool:
        """Return if controller is available."""
        return self._ctrl.connected()

    @property
    def entity_category(self) -> str:
        """Return entity category"""
        if self._entity_category:
            return self._entity_category

        return None

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return a description for device registry."""
        if self._type[ATTR_GROUP] == "System":
            self._type[ATTR_GROUP] = self._ctrl.data["resource"]["board-name"]

        info = {
            "connections": {(DOMAIN, self._ctrl.data["routerboard"]["serial-number"])},
            "manufacturer": self._ctrl.data["resource"]["platform"],
            "model": self._ctrl.data["resource"]["board-name"],
            "name": f"{self._inst} {self._type[ATTR_GROUP]}",
            "sw_version": self._ctrl.data["resource"]["version"],
            "configuration_url": f"http://{self._ctrl.config_entry.data[CONF_HOST]}",
        }
        if ATTR_GROUP in self._type:
            info["identifiers"] = {
                (
                    DOMAIN,
                    "serial-number",
                    self._ctrl.data["routerboard"]["serial-number"],
                    "sensor",
                    f"{self._inst} {self._type[ATTR_GROUP]}",
                )
            }

        return info

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        val = False
        if self._attr in self._data:
            val = self._data[self._attr]

        return val

    async def async_update(self):
        """Synchronize state with controller."""

    async def async_added_to_hass(self):
        """Run when entity about to be added to hass."""
        _LOGGER.debug("New sensor %s (%s)", self._inst, self._sensor)


# ---------------------------
#   MikrotikControllerPPPSecretBinarySensor
# ---------------------------
class MikrotikControllerPPPSecretBinarySensor(MikrotikControllerBinarySensor):
    """Representation of a network device."""

    def __init__(self, inst, uid, mikrotik_controller, config_entry, sid_data):
        """Initialize."""
        super().__init__(mikrotik_controller, inst, uid)
        self._sid_data = sid_data
        self._data = mikrotik_controller.data[self._sid_data["sid"]][uid]
        self._config_entry = config_entry

    @property
    def option_sensor_ppp(self) -> bool:
        """Config entry option."""
        return self._config_entry.options.get(CONF_SENSOR_PPP, DEFAULT_SENSOR_PPP)

    @property
    def name(self) -> str:
        """Return the name."""
        return f"{self._inst} PPP {self._data['name']}"

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        if not self.option_sensor_ppp:
            return False

        return self._data["connected"]

    @property
    def device_class(self) -> Optional[str]:
        """Return the device class."""
        return BinarySensorDeviceClass.CONNECTIVITY

    @property
    def available(self) -> bool:
        """Return if controller is available."""
        if not self.option_sensor_ppp:
            return False

        return self._ctrl.connected()

    @property
    def unique_id(self) -> str:
        """Return a unique id for this entity."""
        return f"{self._inst.lower()}-{self._sid_data['sid']}_tracker-{self._data[self._sid_data['sid_ref']]}"

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self._data["connected"]:
            return "mdi:account-network-outline"
        else:
            return "mdi:account-off-outline"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        attributes = self._attrs
        for variable in DEVICE_ATTRIBUTES_PPP_SECRET:
            if variable in self._data:
                attributes[format_attribute(variable)] = self._data[variable]

        return attributes

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return a description for device registry."""
        info = {
            "identifiers": {
                (
                    DOMAIN,
                    "serial-number",
                    self._ctrl.data["routerboard"]["serial-number"],
                    "switch",
                    "PPP",
                )
            },
            "manufacturer": self._ctrl.data["resource"]["platform"],
            "model": self._ctrl.data["resource"]["board-name"],
            "name": f"{self._inst} PPP",
        }
        return info


# ---------------------------
#   MikrotikControllerPortBinarySensor
# ---------------------------
class MikrotikControllerPortBinarySensor(MikrotikControllerBinarySensor):
    """Representation of a network port."""

    def __init__(self, inst, uid, mikrotik_controller, config_entry, sid_data):
        """Initialize."""
        super().__init__(mikrotik_controller, inst, uid)
        self._sid_data = sid_data
        self._data = mikrotik_controller.data[self._sid_data["sid"]][uid]
        self._config_entry = config_entry

    @property
    def option_sensor_port_tracker(self) -> bool:
        """Config entry option to not track ARP."""
        return self._config_entry.options.get(
            CONF_SENSOR_PORT_TRACKER, DEFAULT_SENSOR_PORT_TRACKER
        )

    @property
    def name(self) -> str:
        """Return the name."""
        return f"{self._inst} {self._data[self._sid_data['sid_name']]}"

    @property
    def unique_id(self) -> str:
        """Return a unique id for this entity."""
        return (
            f"{self._inst.lower()}-{self._sid_data['sid']}-"
            f"{self._data['port-mac-address']}_{self._data['default-name']}"
        )

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._data["running"]

    @property
    def device_class(self) -> Optional[str]:
        """Return the device class."""
        return BinarySensorDeviceClass.CONNECTIVITY

    @property
    def available(self) -> bool:
        """Return if controller is available."""
        if not self.option_sensor_port_tracker:
            return False

        return self._ctrl.connected()

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self._data["running"]:
            icon = "mdi:lan-connect"
        else:
            icon = "mdi:lan-pending"

        if not self._data["enabled"]:
            icon = "mdi:lan-disconnect"

        return icon

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        attributes = self._attrs
        for variable in DEVICE_ATTRIBUTES_IFACE:
            if variable in self._data:
                attributes[format_attribute(variable)] = self._data[variable]

        if "sfp-shutdown-temperature" in self._data:
            for variable in DEVICE_ATTRIBUTES_IFACE_SFP:
                if variable in self._data:
                    attributes[format_attribute(variable)] = self._data[variable]

        return attributes

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return a description for device registry."""
        info = {
            "connections": {
                (CONNECTION_NETWORK_MAC, self._data[self._sid_data["sid_ref"]])
            },
            "manufacturer": self._ctrl.data["resource"]["platform"],
            "model": self._ctrl.data["resource"]["board-name"],
            "name": f"{self._inst} {self._data[self._sid_data['sid_name']]}",
        }

        return info
