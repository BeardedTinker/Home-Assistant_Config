"""Support for the Mikrotik Router device tracker."""

import logging
from typing import Any, Dict
from collections.abc import Mapping
from datetime import timedelta
from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.components.device_tracker.const import SOURCE_TYPE_ROUTER
from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    ATTR_ATTRIBUTION,
    STATE_NOT_HOME,
)
from homeassistant.core import callback
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util.dt import get_age, utcnow
from .helper import format_attribute, format_value
from .const import (
    DOMAIN,
    ATTRIBUTION,
    CONF_TRACK_HOSTS,
    DEFAULT_TRACK_HOSTS,
    CONF_TRACK_HOSTS_TIMEOUT,
    DEFAULT_TRACK_HOST_TIMEOUT,
)
from .device_tracker_types import (
    MikrotikDeviceTrackerEntityDescription,
    SENSOR_TYPES,
)

_LOGGER = logging.getLogger(__name__)


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up device tracker for Mikrotik Router component."""
    inst = config_entry.data[CONF_NAME]
    mikrotik_controller = hass.data[DOMAIN][config_entry.entry_id]
    trackers = {}

    @callback
    def update_controller():
        """Update the values of the controller."""
        update_items(
            inst, config_entry, mikrotik_controller, async_add_entities, trackers
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
def update_items(inst, config_entry, mikrotik_controller, async_add_entities, trackers):
    """Update trackers device state from the controller."""
    new_trackers = []

    for sensor, sid_func in zip(
        # Sensor type name
        ["host"],
        # Entity function
        [MikrotikControllerHostDeviceTracker],
    ):
        uid_sensor = SENSOR_TYPES[sensor]
        if (
            # Skip if host tracking is disabled
            sensor == "host"
            and not config_entry.options.get(CONF_TRACK_HOSTS, DEFAULT_TRACK_HOSTS)
        ):
            continue

        for uid in mikrotik_controller.data[uid_sensor.data_path]:
            uid_data = mikrotik_controller.data[uid_sensor.data_path]
            item_id = f"{inst}-{sensor}-{uid_data[uid][uid_sensor.data_reference]}"
            _LOGGER.debug("Updating device tracker %s", item_id)
            if item_id in trackers:
                if trackers[item_id].enabled:
                    trackers[item_id].async_schedule_update_ha_state()
                continue

            trackers[item_id] = sid_func(
                inst=inst,
                uid=uid,
                mikrotik_controller=mikrotik_controller,
                entity_description=uid_sensor,
                config_entry=config_entry,
            )
            new_trackers.append(trackers[item_id])

    # Register new entities
    if new_trackers:
        async_add_entities(new_trackers)


# ---------------------------
#   MikrotikControllerDeviceTracker
# ---------------------------
class MikrotikControllerDeviceTracker(ScannerEntity):
    """Representation of a device tracker."""

    def __init__(
        self,
        inst,
        uid: "",
        mikrotik_controller,
        entity_description: MikrotikDeviceTrackerEntityDescription,
        config_entry,
    ):
        """Initialize."""
        self.entity_description = entity_description
        self._config_entry = config_entry
        self._inst = inst
        self._ctrl = mikrotik_controller
        self._attr_extra_state_attributes = {ATTR_ATTRIBUTION: ATTRIBUTION}
        self._data = mikrotik_controller.data[self.entity_description.data_path][uid]

    @property
    def name(self) -> str:
        """Return the name."""
        if self.entity_description.name:
            return f"{self._inst} {self._data[self.entity_description.data_name]} {self.entity_description.name}"

        return f"{self._inst} {self._data[self.entity_description.data_name]}"

    @property
    def unique_id(self) -> str:
        """Return a unique id for this entity."""
        return f"{self._inst.lower()}-{self.entity_description.key}-{self._data[self.entity_description.data_reference].lower()}"

    @property
    def ip_address(self) -> str:
        """Return the primary ip address of the device."""
        if "address" in self._data:
            return self._data["address"]

        return None

    @property
    def mac_address(self) -> str:
        """Return the mac address of the device."""
        if self.entity_description.data_reference in self._data:
            return self._data[self.entity_description.data_reference]

        return None

    @property
    def hostname(self) -> str:
        """Return hostname of the device."""
        if self.entity_description.data_name in self._data:
            return self._data[self.entity_description.data_name]

        return None

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return a description for device registry."""
        info = {
            "connections": {
                (CONNECTION_NETWORK_MAC, self._data[self._sid_data["sid_ref"]])
            },
            "manufacturer": self._ctrl.data["resource"]["platform"],
            "model": self._ctrl.data["resource"]["board-name"],
            "name": self._data[self._sid_data["sid_name"]],
        }
        if self._sid_data["sid"] == "interface":
            info["name"] = f"{self._inst} {self._data[self._sid_data['sid_name']]}"
        return info

    @property
    def is_connected(self) -> bool:
        """Return true if device is connected."""
        return self._data[self.entity_description.data_is_on]

    @property
    def device_info(self) -> DeviceInfo:
        """Return a description for device registry."""
        dev_connection = DOMAIN
        dev_connection_value = self.entity_description.data_reference
        dev_group = self.entity_description.ha_group
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

    @property
    def source_type(self) -> str:
        """Return the source type of the port."""
        return SOURCE_TYPE_ROUTER

    async def async_added_to_hass(self):
        """Run when entity about to be added to hass."""
        _LOGGER.debug("New device tracker %s (%s)", self._inst, self.unique_id)


# ---------------------------
#   MikrotikControllerHostDeviceTracker
# ---------------------------
class MikrotikControllerHostDeviceTracker(MikrotikControllerDeviceTracker):
    """Representation of a network device."""

    @property
    def option_track_network_hosts(self):
        """Config entry option to not track ARP."""
        return self._config_entry.options.get(CONF_TRACK_HOSTS, DEFAULT_TRACK_HOSTS)

    @property
    def option_track_network_hosts_timeout(self):
        """Config entry option scan interval."""
        track_network_hosts_timeout = self._config_entry.options.get(
            CONF_TRACK_HOSTS_TIMEOUT, DEFAULT_TRACK_HOST_TIMEOUT
        )
        return timedelta(seconds=track_network_hosts_timeout)

    @property
    def name(self) -> str:
        """Return the name."""
        return f"{self._data[self.entity_description.data_name]}"

    @property
    def unique_id(self) -> str:
        """Return a unique id for this entity."""
        return f"{self._data[self.entity_description.data_reference].lower()}"

    @property
    def is_connected(self) -> bool:
        """Return true if the host is connected to the network."""
        if not self.option_track_network_hosts:
            return False

        if self._data["source"] in ["capsman", "wireless"]:
            return self._data[self.entity_description.data_is_on]

        if (
            self._data["last-seen"]
            and (utcnow() - self._data["last-seen"])
            < self.option_track_network_hosts_timeout
        ):
            return True

        return False

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self._data["source"] in ["capsman", "wireless"]:
            if self._data[self.entity_description.data_is_on]:
                return self.entity_description.icon_enabled
            else:
                return self.entity_description.icon_disabled

        if (
            self._data["last-seen"]
            and (utcnow() - self._data["last-seen"])
            < self.option_track_network_hosts_timeout
        ):
            return self.entity_description.icon_enabled
        return self.entity_description.icon_disabled

    @property
    def state(self) -> str:
        """Return the state of the device."""
        if self.is_connected:
            return self._ctrl.option_zone
        return STATE_NOT_HOME

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        attributes = super().extra_state_attributes
        if self._data["last-seen"]:
            attributes[format_attribute("last-seen")] = get_age(self._data["last-seen"])
        else:
            attributes[format_attribute("last-seen")] = "unknown"

        return attributes
