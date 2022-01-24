"""Support for the Mikrotik Router sensor service."""

import logging
from typing import Any, Dict, Optional

from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    ATTR_ATTRIBUTION,
    ATTR_DEVICE_CLASS,
    TEMP_CELSIUS,
    ELECTRIC_POTENTIAL_VOLT,
)

from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.sensor import SensorDeviceClass

from .const import (
    CONF_SENSOR_PORT_TRAFFIC,
    DEFAULT_SENSOR_PORT_TRAFFIC,
)

from homeassistant.core import callback
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import DOMAIN, DATA_CLIENT, ATTRIBUTION

_LOGGER = logging.getLogger(__name__)


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


ATTR_ICON = "icon"
ATTR_LABEL = "label"
ATTR_UNIT = "unit"
ATTR_UNIT_ATTR = "unit_attr"
ATTR_GROUP = "group"
ATTR_PATH = "data_path"
ATTR_ATTR = "data_attr"
ATTR_CTGR = "entity_category"

SENSOR_TYPES = {
    "system_temperature": {
        ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        ATTR_ICON: "mdi:thermometer",
        ATTR_LABEL: "Temperature",
        ATTR_UNIT: TEMP_CELSIUS,
        ATTR_GROUP: "System",
        ATTR_PATH: "health",
        ATTR_ATTR: "temperature",
        ATTR_CTGR: None,
    },
    "system_voltage": {
        ATTR_DEVICE_CLASS: SensorDeviceClass.VOLTAGE,
        ATTR_ICON: "mdi:lightning-bolt",
        ATTR_LABEL: "Voltage",
        ATTR_UNIT: ELECTRIC_POTENTIAL_VOLT,
        ATTR_GROUP: "System",
        ATTR_PATH: "health",
        ATTR_ATTR: "voltage",
        ATTR_CTGR: EntityCategory.DIAGNOSTIC,
    },
    "system_cpu-temperature": {
        ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        ATTR_ICON: "mdi:thermometer",
        ATTR_LABEL: "CPU temperature",
        ATTR_UNIT: TEMP_CELSIUS,
        ATTR_GROUP: "System",
        ATTR_PATH: "health",
        ATTR_ATTR: "cpu-temperature",
        ATTR_CTGR: None,
    },
    "system_board-temperature1": {
        ATTR_DEVICE_CLASS: SensorDeviceClass.TEMPERATURE,
        ATTR_ICON: "mdi:thermometer",
        ATTR_LABEL: "Board temperature",
        ATTR_UNIT: TEMP_CELSIUS,
        ATTR_GROUP: "System",
        ATTR_PATH: "health",
        ATTR_ATTR: "board-temperature1",
        ATTR_CTGR: None,
    },
    "system_power-consumption": {
        ATTR_DEVICE_CLASS: SensorDeviceClass.POWER,
        ATTR_ICON: "mdi:transmission-tower",
        ATTR_LABEL: "Power consumption",
        ATTR_UNIT: "W",
        ATTR_GROUP: "System",
        ATTR_PATH: "health",
        ATTR_ATTR: "power-consumption",
        ATTR_CTGR: None,
    },
    "system_fan1-speed": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:fan",
        ATTR_LABEL: "Fan1 speed",
        ATTR_UNIT: "RPM",
        ATTR_GROUP: "System",
        ATTR_PATH: "health",
        ATTR_ATTR: "fan1-speed",
        ATTR_CTGR: None,
    },
    "system_fan2-speed": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:fan",
        ATTR_LABEL: "Fan2 speed",
        ATTR_UNIT: "RPM",
        ATTR_GROUP: "System",
        ATTR_PATH: "health",
        ATTR_ATTR: "fan2-speed",
        ATTR_CTGR: None,
    },
    "system_uptime": {
        ATTR_DEVICE_CLASS: SensorDeviceClass.TIMESTAMP,
        ATTR_ICON: None,
        ATTR_LABEL: "Uptime",
        ATTR_UNIT: None,
        ATTR_GROUP: "System",
        ATTR_PATH: "resource",
        ATTR_ATTR: "uptime",
        ATTR_CTGR: EntityCategory.DIAGNOSTIC,
    },
    "system_cpu-load": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:speedometer",
        ATTR_LABEL: "CPU load",
        ATTR_UNIT: "%",
        ATTR_GROUP: "System",
        ATTR_PATH: "resource",
        ATTR_ATTR: "cpu-load",
        ATTR_CTGR: None,
    },
    "system_memory-usage": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:memory",
        ATTR_LABEL: "Memory usage",
        ATTR_UNIT: "%",
        ATTR_GROUP: "System",
        ATTR_PATH: "resource",
        ATTR_ATTR: "memory-usage",
        ATTR_CTGR: None,
    },
    "system_hdd-usage": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:harddisk",
        ATTR_LABEL: "HDD usage",
        ATTR_UNIT: "%",
        ATTR_GROUP: "System",
        ATTR_PATH: "resource",
        ATTR_ATTR: "hdd-usage",
        ATTR_CTGR: None,
    },
    "traffic_tx": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:upload-network-outline",
        ATTR_LABEL: "TX",
        ATTR_UNIT: "ps",
        ATTR_UNIT_ATTR: "tx-bits-per-second-attr",
        ATTR_PATH: "interface",
        ATTR_ATTR: "tx-bits-per-second",
        ATTR_CTGR: None,
    },
    "traffic_rx": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:download-network-outline",
        ATTR_LABEL: "RX",
        ATTR_UNIT: "ps",
        ATTR_UNIT_ATTR: "rx-bits-per-second-attr",
        ATTR_PATH: "interface",
        ATTR_ATTR: "rx-bits-per-second",
        ATTR_CTGR: None,
    },
    "client_traffic_lan_tx": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:upload-network",
        ATTR_LABEL: "LAN TX",
        ATTR_UNIT: "ps",
        ATTR_UNIT_ATTR: "tx-rx-attr",
        ATTR_PATH: "client_traffic",
        ATTR_ATTR: "lan-tx",
        ATTR_CTGR: None,
    },
    "client_traffic_lan_rx": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:download-network",
        ATTR_LABEL: "LAN RX",
        ATTR_UNIT: "ps",
        ATTR_UNIT_ATTR: "tx-rx-attr",
        ATTR_PATH: "client_traffic",
        ATTR_ATTR: "lan-rx",
        ATTR_CTGR: None,
    },
    "client_traffic_wan_tx": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:upload-network",
        ATTR_LABEL: "WAN TX",
        ATTR_UNIT: "ps",
        ATTR_UNIT_ATTR: "tx-rx-attr",
        ATTR_PATH: "client_traffic",
        ATTR_ATTR: "wan-tx",
        ATTR_CTGR: None,
    },
    "client_traffic_wan_rx": {
        ATTR_DEVICE_CLASS: None,
        ATTR_ICON: "mdi:download-network",
        ATTR_LABEL: "WAN RX",
        ATTR_UNIT: "ps",
        ATTR_UNIT_ATTR: "tx-rx-attr",
        ATTR_PATH: "client_traffic",
        ATTR_ATTR: "wan-rx",
        ATTR_CTGR: None,
    },
}

DEVICE_ATTRIBUTES_CLIENT_TRAFFIC = ["address", "mac-address", "host-name"]


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

    for sid, sid_uid, sid_name, sid_val, sid_ref, sid_attr, sid_func in zip(
        # Data point name
        ["environment"],
        # Data point unique id
        ["name"],
        # Entry Name
        ["name"],
        # Entry Value
        ["value"],
        # Entry Unique id
        ["name"],
        # Attr
        [
            None,
        ],
        # Switch function
        [
            MikrotikControllerEnvironmentSensor,
        ],
    ):
        for uid in mikrotik_controller.data[sid]:
            item_id = f"{inst}-{sid}-{mikrotik_controller.data[sid][uid][sid_uid]}"
            _LOGGER.debug("Updating sensor %s", item_id)
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
                "sid_attr": sid_attr,
                "sid_val": sid_val,
            }
            sensors[item_id] = sid_func(inst, uid, mikrotik_controller, sid_data)
            new_sensors.append(sensors[item_id])

    for sensor in SENSOR_TYPES:
        if sensor.startswith("system_"):
            if (
                SENSOR_TYPES[sensor][ATTR_ATTR]
                not in mikrotik_controller.data[SENSOR_TYPES[sensor][ATTR_PATH]]
                or mikrotik_controller.data[SENSOR_TYPES[sensor][ATTR_PATH]][
                    SENSOR_TYPES[sensor][ATTR_ATTR]
                ]
                == "unknown"
            ):
                continue
            item_id = f"{inst}-{sensor}"
            _LOGGER.debug("Updating sensor %s", item_id)
            if item_id in sensors:
                if sensors[item_id].enabled:
                    sensors[item_id].async_schedule_update_ha_state()
                continue

            sensors[item_id] = MikrotikControllerSensor(
                mikrotik_controller=mikrotik_controller, inst=inst, sid_data=sensor
            )
            new_sensors.append(sensors[item_id])

        if sensor.startswith("traffic_"):
            if not config_entry.options.get(
                CONF_SENSOR_PORT_TRAFFIC, DEFAULT_SENSOR_PORT_TRAFFIC
            ):
                continue

            for uid in mikrotik_controller.data["interface"]:
                if mikrotik_controller.data["interface"][uid]["type"] != "bridge":
                    item_id = f"{inst}-{sensor}-{mikrotik_controller.data['interface'][uid]['default-name']}"
                    _LOGGER.debug("Updating sensor %s", item_id)
                    if item_id in sensors:
                        if sensors[item_id].enabled:
                            sensors[item_id].async_schedule_update_ha_state()
                        continue

                    sensors[item_id] = MikrotikControllerTrafficSensor(
                        mikrotik_controller=mikrotik_controller,
                        inst=inst,
                        sensor=sensor,
                        uid=uid,
                    )
                    new_sensors.append(sensors[item_id])

        if sensor.startswith("client_traffic_"):
            for uid in mikrotik_controller.data["client_traffic"]:
                item_id = f"{inst}-{sensor}-{mikrotik_controller.data['client_traffic'][uid]['mac-address']}"
                if item_id in sensors:
                    if sensors[item_id].enabled:
                        sensors[item_id].async_schedule_update_ha_state()
                    continue

                if (
                    SENSOR_TYPES[sensor][ATTR_ATTR]
                    in mikrotik_controller.data["client_traffic"][uid].keys()
                ):
                    sensors[item_id] = MikrotikClientTrafficSensor(
                        mikrotik_controller=mikrotik_controller,
                        inst=inst,
                        sensor=sensor,
                        uid=uid,
                    )
                    new_sensors.append(sensors[item_id])

    if new_sensors:
        async_add_entities(new_sensors, True)


# ---------------------------
#   MikrotikControllerSensor
# ---------------------------
class MikrotikControllerSensor(SensorEntity):
    """Define an Mikrotik Controller sensor."""

    def __init__(self, mikrotik_controller, inst, sid_data):
        """Initialize."""
        self._inst = inst
        self._sensor = sid_data
        self._ctrl = mikrotik_controller

        if sid_data in SENSOR_TYPES:
            self._data = mikrotik_controller.data[SENSOR_TYPES[sid_data][ATTR_PATH]]
            self._type = SENSOR_TYPES[sid_data]
            self._icon = self._type[ATTR_ICON]
            self._attr = self._type[ATTR_ATTR]
            self._dcls = self._type[ATTR_DEVICE_CLASS]
            self._ctgr = self._type[ATTR_CTGR]
        else:
            self._type = {}
            self._icon = None
            self._attr = None
            self._dcls = None
            self._ctgr = None

        self._state = None
        self._attrs = {ATTR_ATTRIBUTION: ATTRIBUTION}

    @property
    def name(self) -> str:
        """Return the name."""
        return f"{self._inst} {self._type[ATTR_LABEL]}"

    @property
    def state(self) -> Optional[str]:
        """Return the state."""
        val = "unknown"
        if self._attr in self._data:
            val = self._data[self._attr]

        return val

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        return self._attrs

    @property
    def icon(self) -> str:
        """Return the icon."""
        return self._icon

    @property
    def entity_category(self) -> str:
        """Return entity category"""
        return self._ctgr

    @property
    def device_class(self) -> Optional[str]:
        """Return the device class."""
        return self._dcls

    @property
    def unique_id(self) -> str:
        """Return a unique id for this entity."""
        return f"{self._inst.lower()}-{self._sensor.lower()}"

    @property
    def unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        if ATTR_UNIT_ATTR in self._type:
            return self._data[SENSOR_TYPES[self._sensor][ATTR_UNIT_ATTR]]

        if ATTR_UNIT in self._type:
            return self._type[ATTR_UNIT]

    @property
    def available(self) -> bool:
        """Return if controller is available."""
        return self._ctrl.connected()

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return a description for device registry."""
        if self._type[ATTR_GROUP] == "System":
            self._type[ATTR_GROUP] = self._ctrl.data["resource"]["board-name"]

        info = {
            "connections": {
                (DOMAIN, f"{self._ctrl.data['routerboard']['serial-number']}")
            },
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
                    f"{self._ctrl.data['routerboard']['serial-number']}",
                    "sensor",
                    f"{self._inst} {self._type[ATTR_GROUP]}",
                )
            }

        return info

    async def async_update(self):
        """Synchronize state with controller."""

    async def async_added_to_hass(self):
        """Run when entity about to be added to hass."""
        _LOGGER.debug("New sensor %s (%s)", self._inst, self._sensor)


# ---------------------------
#   MikrotikControllerTrafficSensor
# ---------------------------
class MikrotikControllerTrafficSensor(MikrotikControllerSensor):
    """Define a traffic sensor."""

    def __init__(self, mikrotik_controller, inst, sensor, uid):
        """Initialize."""
        super().__init__(mikrotik_controller, inst, sensor)
        self._uid = uid
        self._data = mikrotik_controller.data[SENSOR_TYPES[sensor][ATTR_PATH]][uid]

    @property
    def name(self) -> str:
        """Return the name."""
        return f"{self._inst} {self._data['name']} {self._type[ATTR_LABEL]}"

    @property
    def unique_id(self) -> str:
        """Return a unique id for this entity."""
        return f"{self._inst.lower()}-{self._sensor.lower()}-{self._data['default-name'].lower()}"

    @property
    def state_class(self) -> str:
        """Return the state_class"""
        return f"measurement"

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return a description for device registry."""
        info = {
            "connections": {(CONNECTION_NETWORK_MAC, self._data["port-mac-address"])},
            "manufacturer": self._ctrl.data["resource"]["platform"],
            "model": self._ctrl.data["resource"]["board-name"],
            "name": f"{self._inst} {self._data['default-name']}",
        }

        return info


# ---------------------------
#   MikrotikClientTrafficSensor
# ---------------------------
class MikrotikClientTrafficSensor(MikrotikControllerSensor):
    """Define an Mikrotik MikrotikClientTrafficSensor sensor."""

    def __init__(self, mikrotik_controller, inst, sensor, uid):
        """Initialize."""
        super().__init__(mikrotik_controller, inst, sensor)
        self._uid = uid
        self._data = mikrotik_controller.data[SENSOR_TYPES[sensor][ATTR_PATH]][uid]

    @property
    def name(self) -> str:
        """Return the name."""
        return f"{self._data['host-name']} {self._type[ATTR_LABEL]}"

    @property
    def unique_id(self) -> str:
        """Return a unique id for this entity."""
        return f"{self._inst.lower()}-{self._sensor.lower()}-{self._data['mac-address'].lower()}"

    @property
    def available(self) -> bool:
        """Return if controller and accounting feature in Mikrotik is available.
        Additional check for lan-tx/rx sensors
        """
        if self._attr in ["lan-tx", "lan-rx"]:
            return (
                self._ctrl.connected()
                and self._data["available"]
                and self._data["local_accounting"]
            )
        else:
            return self._ctrl.connected() and self._data["available"]

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return a description for device registry."""
        info = {
            "connections": {(CONNECTION_NETWORK_MAC, self._data["mac-address"])},
            "default_name": self._data["host-name"],
        }
        if "manufacturer" in self._data and self._data["manufacturer"] != "":
            info["manufacturer"] = self._data["manufacturer"]

        return info

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        attributes = self._attrs
        for variable in DEVICE_ATTRIBUTES_CLIENT_TRAFFIC:
            if variable in self._data:
                attributes[format_attribute(variable)] = self._data[variable]

        return attributes


# ---------------------------
#   MikrotikControllerEnvironmentSensor
# ---------------------------
class MikrotikControllerEnvironmentSensor(MikrotikControllerSensor):
    """Define an Enviroment variable sensor."""

    def __init__(self, inst, uid, mikrotik_controller, sid_data):
        """Initialize."""
        super().__init__(mikrotik_controller, inst, "")
        self._uid = uid
        self._sid_data = sid_data
        self._data = mikrotik_controller.data[self._sid_data["sid"]][uid]

    @property
    def name(self) -> str:
        """Return the name."""
        return f"{self._inst} {self._data[self._sid_data['sid_ref']]}"

    @property
    def unique_id(self) -> str:
        """Return a unique id for this entity."""
        return f"{self._inst.lower()}-{self._sid_data['sid']}-{self._data[self._sid_data['sid_ref']]}"

    @property
    def state(self) -> Optional[str]:
        """Return the state."""
        return self._data[self._sid_data["sid_val"]]

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:clipboard-list"

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return a description for device registry."""
        info = {
            "identifiers": {
                (
                    DOMAIN,
                    "serial-number",
                    f"{self._ctrl.data['routerboard']['serial-number']}",
                    "sensor",
                    "Environment",
                )
            },
            "manufacturer": self._ctrl.data["resource"]["platform"],
            "model": self._ctrl.data["resource"]["board-name"],
            "name": f"{self._inst} Environment",
        }

        return info
