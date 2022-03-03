"""Implementation of Mikrotik Router sensor entities."""

import logging
from typing import Any, Optional
from collections.abc import Mapping
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    ATTR_ATTRIBUTION,
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.sensor import SensorEntity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .helper import format_attribute
from .const import (
    CONF_SENSOR_PORT_TRAFFIC,
    DEFAULT_SENSOR_PORT_TRAFFIC,
    DOMAIN,
    ATTRIBUTION,
)
from .sensor_types import (
    MikrotikSensorEntityDescription,
    SENSOR_TYPES,
    DEVICE_ATTRIBUTES_IFACE_ETHER,
    DEVICE_ATTRIBUTES_IFACE_SFP,
)

_LOGGER = logging.getLogger(__name__)


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up device tracker for Mikrotik Router component."""
    inst = config_entry.data[CONF_NAME]
    mikrotik_controller = hass.data[DOMAIN][config_entry.entry_id]
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

    for sensor, sid_func in zip(
        # Sensor type name
        [
            "environment",
            "traffic_rx",
            "traffic_tx",
            "client_traffic_rx",
            "client_traffic_tx",
            "client_traffic_lan_rx",
            "client_traffic_lan_tx",
            "client_traffic_wan_rx",
            "client_traffic_wan_tx",
        ],
        # Entity function
        [
            MikrotikControllerSensor,
            MikrotikInterfaceTrafficSensor,
            MikrotikInterfaceTrafficSensor,
            MikrotikClientTrafficSensor,
            MikrotikClientTrafficSensor,
            MikrotikClientTrafficSensor,
            MikrotikClientTrafficSensor,
            MikrotikClientTrafficSensor,
            MikrotikClientTrafficSensor,
        ],
    ):
        if sensor.startswith("traffic_") and not config_entry.options.get(
            CONF_SENSOR_PORT_TRAFFIC, DEFAULT_SENSOR_PORT_TRAFFIC
        ):
            continue

        uid_sensor = SENSOR_TYPES[sensor]
        for uid in mikrotik_controller.data[uid_sensor.data_path]:
            uid_data = mikrotik_controller.data[uid_sensor.data_path]
            if (
                uid_sensor.data_path == "interface"
                and uid_data[uid]["type"] == "bridge"
            ):
                continue

            if (
                uid_sensor.data_path == "client_traffic"
                and uid_sensor.data_attribute not in uid_data[uid].keys()
            ):
                continue

            item_id = f"{inst}-{sensor}-{uid_data[uid][uid_sensor.data_reference]}"
            _LOGGER.debug("Updating sensor %s", item_id)
            if item_id in sensors:
                if sensors[item_id].enabled:
                    sensors[item_id].async_schedule_update_ha_state()
                continue

            sensors[item_id] = sid_func(
                inst=inst,
                uid=uid,
                mikrotik_controller=mikrotik_controller,
                entity_description=uid_sensor,
            )
            new_sensors.append(sensors[item_id])

    for sensor in SENSOR_TYPES:
        if sensor.startswith("system_"):
            uid_sensor = SENSOR_TYPES[sensor]
            if (
                uid_sensor.data_attribute
                not in mikrotik_controller.data[uid_sensor.data_path]
                or mikrotik_controller.data[uid_sensor.data_path][
                    uid_sensor.data_attribute
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
                inst=inst,
                uid="",
                mikrotik_controller=mikrotik_controller,
                entity_description=uid_sensor,
            )
            new_sensors.append(sensors[item_id])

    if new_sensors:
        async_add_entities(new_sensors, True)


# ---------------------------
#   MikrotikControllerSensor
# ---------------------------
class MikrotikControllerSensor(SensorEntity):
    """Define an Mikrotik Controller sensor."""

    def __init__(
        self,
        inst,
        uid: "",
        mikrotik_controller,
        entity_description: MikrotikSensorEntityDescription,
    ):
        """Initialize."""
        self.entity_description = entity_description
        self._inst = inst
        self._ctrl = mikrotik_controller
        self._attr_extra_state_attributes = {ATTR_ATTRIBUTION: ATTRIBUTION}
        self._uid = uid
        if self._uid:
            self._data = mikrotik_controller.data[self.entity_description.data_path][
                self._uid
            ]
        else:
            self._data = mikrotik_controller.data[self.entity_description.data_path]

    @property
    def name(self) -> str:
        """Return the name."""
        if self._uid:
            if self.entity_description.name:
                return f"{self._inst} {self._data[self.entity_description.data_name]} {self.entity_description.name}"

            return f"{self._inst} {self._data[self.entity_description.data_name]}"
        else:
            return f"{self._inst} {self.entity_description.name}"

    @property
    def unique_id(self) -> str:
        """Return a unique id for this entity."""
        if self._uid:
            return f"{self._inst.lower()}-{self.entity_description.key}-{self._data[self.entity_description.data_reference].lower()}"
        else:
            return f"{self._inst.lower()}-{self.entity_description.key}"

    @property
    def state(self) -> Optional[str]:
        """Return the state."""
        if self.entity_description.data_attribute:
            return self._data[self.entity_description.data_attribute]
        else:
            return "unknown"

    @property
    def native_unit_of_measurement(self):
        """Return the unit the value is expressed in."""
        if self.entity_description.native_unit_of_measurement:
            if self.entity_description.native_unit_of_measurement.startswith("data__"):
                uom = self.entity_description.native_unit_of_measurement[6:]
                if uom in self._data:
                    uom = self._data[uom]
                    return uom

            return self.entity_description.native_unit_of_measurement

        return None

    @property
    def available(self) -> bool:
        """Return if controller is available."""
        return self._ctrl.connected()

    @property
    def device_info(self) -> DeviceInfo:
        """Return a description for device registry."""
        dev_connection = DOMAIN
        dev_connection_value = self.entity_description.data_reference
        dev_group = self.entity_description.ha_group
        if self.entity_description.ha_group == "System":
            dev_group = self._ctrl.data["resource"]["board-name"]
            dev_connection_value = self._ctrl.data["routerboard"]["serial-number"]

        if self.entity_description.ha_group.startswith("data__"):
            dev_group = self.entity_description.ha_group[6:]
            if dev_group in self._data:
                dev_group = self._data[dev_group]
                dev_connection_value = dev_group

        if self.entity_description.ha_connection:
            dev_connection = self.entity_description.ha_connection

        if self.entity_description.ha_connection_value:
            dev_connection_value = self.entity_description.ha_connection_value
            if dev_connection_value.startswith("data__"):
                dev_connection_value = dev_connection_value[6:]
                dev_connection_value = self._data[dev_connection_value]

        info = DeviceInfo(
            connections={(dev_connection, f"{dev_connection_value}")},
            identifiers={(dev_connection, f"{dev_connection_value}")},
            default_name=f"{self._inst} {dev_group}",
            model=f"{self._ctrl.data['resource']['board-name']}",
            manufacturer=f"{self._ctrl.data['resource']['platform']}",
            sw_version=f"{self._ctrl.data['resource']['version']}",
            configuration_url=f"http://{self._ctrl.config_entry.data[CONF_HOST]}",
            via_device=(DOMAIN, f"{self._ctrl.data['routerboard']['serial-number']}"),
        )

        if "mac-address" in self.entity_description.data_reference:
            dev_group = self._data[self.entity_description.data_name]
            dev_manufacturer = ""
            if dev_connection_value in self._ctrl.data["host"]:
                dev_group = self._ctrl.data["host"][dev_connection_value]["host-name"]
                dev_manufacturer = self._ctrl.data["host"][dev_connection_value][
                    "manufacturer"
                ]

            info = DeviceInfo(
                connections={(dev_connection, f"{dev_connection_value}")},
                default_name=f"{dev_group}",
                manufacturer=f"{dev_manufacturer}",
                via_device=(
                    DOMAIN,
                    f"{self._ctrl.data['routerboard']['serial-number']}",
                ),
            )

        return info

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        attributes = super().extra_state_attributes
        for variable in self.entity_description.data_attributes_list:
            if variable in self._data:
                attributes[format_attribute(variable)] = self._data[variable]

        return attributes

    async def async_added_to_hass(self):
        """Run when entity about to be added to hass."""
        _LOGGER.debug("New sensor %s (%s)", self._inst, self.unique_id)


# ---------------------------
#   MikrotikInterfaceTrafficSensor
# ---------------------------
class MikrotikInterfaceTrafficSensor(MikrotikControllerSensor):
    """Define an Mikrotik MikrotikInterfaceTrafficSensor sensor."""

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        attributes = super().extra_state_attributes

        if self._data["type"] == "ether":
            for variable in DEVICE_ATTRIBUTES_IFACE_ETHER:
                if variable in self._data:
                    attributes[format_attribute(variable)] = self._data[variable]

            if "sfp-shutdown-temperature" in self._data:
                for variable in DEVICE_ATTRIBUTES_IFACE_SFP:
                    if variable in self._data:
                        attributes[format_attribute(variable)] = self._data[variable]

        return attributes


# ---------------------------
#   MikrotikClientTrafficSensor
# ---------------------------
class MikrotikClientTrafficSensor(MikrotikControllerSensor):
    """Define an Mikrotik MikrotikClientTrafficSensor sensor."""

    @property
    def name(self) -> str:
        """Return the name."""
        return f"{self._data[self.entity_description.data_name]} {self.entity_description.name}"

    @property
    def available(self) -> bool:
        """Return if controller and accounting feature in Mikrotik is available.
        Additional check for lan-tx/rx sensors
        """
        if self.entity_description.data_attribute in ["lan-tx", "lan-rx"]:
            return (
                self._ctrl.connected()
                and self._data["available"]
                and self._data["local_accounting"]
            )
        else:
            return self._ctrl.connected() and self._data["available"]
