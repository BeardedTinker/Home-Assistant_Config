"""Support for the Mikrotik Router binary sensor service."""

import logging
from typing import Any
from collections.abc import Mapping
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    ATTR_ATTRIBUTION,
)
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from .helper import format_attribute
from .const import (
    DOMAIN,
    ATTRIBUTION,
    CONF_SENSOR_PPP,
    DEFAULT_SENSOR_PPP,
    CONF_SENSOR_PORT_TRACKER,
    DEFAULT_SENSOR_PORT_TRACKER,
)
from .binary_sensor_types import (
    MikrotikBinarySensorEntityDescription,
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
        ["ppp_tracker", "interface"],
        # Entity function
        [MikrotikControllerPPPSecretBinarySensor, MikrotikControllerPortBinarySensor],
    ):
        if sensor == "interface" and not config_entry.options.get(
            CONF_SENSOR_PORT_TRACKER, DEFAULT_SENSOR_PORT_TRACKER
        ):
            continue

        uid_sensor = SENSOR_TYPES[sensor]
        for uid in mikrotik_controller.data[uid_sensor.data_path]:
            uid_data = mikrotik_controller.data[uid_sensor.data_path]
            if uid_sensor.data_path == "interface" and uid_data[uid]["type"] == "wlan":
                continue

            item_id = f"{inst}-{sensor}-{uid_data[uid][uid_sensor.data_reference]}"
            _LOGGER.debug("Updating binary sensor %s", item_id)
            if item_id in sensors:
                if sensors[item_id].enabled:
                    sensors[item_id].async_schedule_update_ha_state()
                continue

            sensors[item_id] = sid_func(
                inst=inst,
                uid=uid,
                mikrotik_controller=mikrotik_controller,
                entity_description=uid_sensor,
                config_entry=config_entry,
            )
            new_sensors.append(sensors[item_id])

    for sensor in SENSOR_TYPES:
        if sensor.startswith("system_"):
            uid_sensor = SENSOR_TYPES[sensor]
            item_id = f"{inst}-{sensor}"
            _LOGGER.debug("Updating binary sensor %s", item_id)
            if item_id in sensors:
                if sensors[item_id].enabled:
                    sensors[item_id].async_schedule_update_ha_state()
                continue

            sensors[item_id] = MikrotikControllerBinarySensor(
                inst=inst,
                uid="",
                mikrotik_controller=mikrotik_controller,
                entity_description=uid_sensor,
                config_entry=config_entry,
            )
            new_sensors.append(sensors[item_id])

    #
    # # Add switches
    # for sid, sid_uid, sid_name, sid_ref, sid_attr, sid_func in zip(
    #     # Data point name
    #     ["ppp_secret", "interface"],
    #     # Data point unique id
    #     ["name", "default-name"],
    #     # Entry Name
    #     ["name", "name"],
    #     # Entry Unique id
    #     ["name", "port-mac-address"],
    #     # Attr
    #     [None, DEVICE_ATTRIBUTES_IFACE],
    #     # Tracker function
    #     [
    #         MikrotikControllerPPPSecretBinarySensor,
    #         MikrotikControllerPortBinarySensor,
    #     ],
    # ):
    #     if (
    #         sid_func == MikrotikControllerPortBinarySensor
    #         and not config_entry.options.get(
    #             CONF_SENSOR_PORT_TRACKER, DEFAULT_SENSOR_PORT_TRACKER
    #         )
    #     ):
    #         continue
    #     for uid in mikrotik_controller.data[sid]:
    #         if (
    #             # Skip if interface is wlan
    #             sid == "interface"
    #             and mikrotik_controller.data[sid][uid]["type"] == "wlan"
    #         ):
    #             continue
    #         # Update entity
    #         item_id = f"{inst}-{sid}-{mikrotik_controller.data[sid][uid][sid_uid]}"
    #         _LOGGER.debug("Updating binary_sensor %s", item_id)
    #         if item_id in sensors:
    #             if sensors[item_id].enabled:
    #                 sensors[item_id].async_schedule_update_ha_state()
    #             continue
    #
    #         # Create new entity
    #         sid_data = {
    #             "sid": sid,
    #             "sid_uid": sid_uid,
    #             "sid_name": sid_name,
    #             "sid_ref": sid_ref,
    #             "sid_attr": sid_attr,
    #         }
    #         sensors[item_id] = sid_func(
    #             inst, uid, mikrotik_controller, config_entry, sid_data
    #         )
    #         new_sensors.append(sensors[item_id])
    #
    # for sensor in SENSOR_TYPES:
    #     item_id = f"{inst}-{sensor}"
    #     _LOGGER.debug("Updating binary_sensor %s", item_id)
    #     if item_id in sensors:
    #         if sensors[item_id].enabled:
    #             sensors[item_id].async_schedule_update_ha_state()
    #         continue
    #
    #     sensors[item_id] = MikrotikControllerBinarySensor(
    #         mikrotik_controller=mikrotik_controller, inst=inst, sid_data=sensor
    #     )
    #     new_sensors.append(sensors[item_id])

    if new_sensors:
        async_add_entities(new_sensors, True)


class MikrotikControllerBinarySensor(BinarySensorEntity):
    """Define an Mikrotik Controller Binary Sensor."""

    def __init__(
        self,
        inst,
        uid: "",
        mikrotik_controller,
        entity_description: MikrotikBinarySensorEntityDescription,
        config_entry,
    ):
        """Initialize."""
        self.entity_description = entity_description
        self._config_entry = config_entry
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
    def available(self) -> bool:
        """Return if controller is available."""
        return self._ctrl.connected()

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._data[self.entity_description.data_is_on]

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self.entity_description.icon_enabled:
            if self._data[self.entity_description.data_is_on]:
                return self.entity_description.icon_enabled
            else:
                return self.entity_description.icon_disabled

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
        _LOGGER.debug("New binary sensor %s (%s)", self._inst, self.unique_id)


# ---------------------------
#   MikrotikControllerPPPSecretBinarySensor
# ---------------------------
class MikrotikControllerPPPSecretBinarySensor(MikrotikControllerBinarySensor):
    """Representation of a network device."""

    @property
    def option_sensor_ppp(self) -> bool:
        """Config entry option."""
        return self._config_entry.options.get(CONF_SENSOR_PPP, DEFAULT_SENSOR_PPP)

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        if not self.option_sensor_ppp:
            return False

        return self._data[self.entity_description.data_is_on]

    @property
    def available(self) -> bool:
        """Return if controller is available."""
        if not self.option_sensor_ppp:
            return False

        return self._ctrl.connected()


# ---------------------------
#   MikrotikControllerPortBinarySensor
# ---------------------------
class MikrotikControllerPortBinarySensor(MikrotikControllerBinarySensor):
    """Representation of a network port."""

    @property
    def option_sensor_port_tracker(self) -> bool:
        """Config entry option to not track ARP."""
        return self._config_entry.options.get(
            CONF_SENSOR_PORT_TRACKER, DEFAULT_SENSOR_PORT_TRACKER
        )

    @property
    def available(self) -> bool:
        """Return if controller is available."""
        if not self.option_sensor_port_tracker:
            return False

        return self._ctrl.connected()

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self._data[self.entity_description.data_is_on]:
            icon = self.entity_description.icon_enabled
        else:
            icon = self.entity_description.icon_disabled

        if not self._data["enabled"]:
            icon = "mdi:lan-disconnect"

        return icon

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
