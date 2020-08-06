"""Support for the Mikrotik Router binary sensor service."""

import logging

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import (
    CONF_NAME,
    ATTR_ATTRIBUTION,
)
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import (
    DOMAIN,
    DATA_CLIENT,
    ATTRIBUTION,
)

_LOGGER = logging.getLogger(__name__)

ATTR_LABEL = "label"
ATTR_GROUP = "group"
ATTR_PATH = "data_path"
ATTR_ATTR = "data_attr"

SENSOR_TYPES = {
    "system_fwupdate": {
        ATTR_LABEL: "Firmware update",
        ATTR_GROUP: "System",
        ATTR_PATH: "fw-update",
        ATTR_ATTR: "available",
    },
}


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
        update_items(inst, mikrotik_controller, async_add_entities, sensors)

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
def update_items(inst, mikrotik_controller, async_add_entities, sensors):
    """Update sensor state from the controller."""
    new_sensors = []

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
        self._data = mikrotik_controller.data[SENSOR_TYPES[sensor][ATTR_PATH]]
        self._type = SENSOR_TYPES[sensor]
        self._attr = SENSOR_TYPES[sensor][ATTR_ATTR]

        self._device_class = None
        self._state = None
        self._icon = None
        self._unit_of_measurement = None
        self._attrs = {ATTR_ATTRIBUTION: ATTRIBUTION}

    @property
    def name(self):
        """Return the name."""
        return f"{self._inst} {self._type[ATTR_LABEL]}"

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attrs

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return f"{self._inst.lower()}-{self._sensor.lower()}"

    @property
    def available(self) -> bool:
        """Return if controller is available."""
        return self._ctrl.connected()

    @property
    def device_info(self):
        """Return a port description for device registry."""
        info = {
            "manufacturer": self._ctrl.data["resource"]["platform"],
            "model": self._ctrl.data["resource"]["board-name"],
            "name": f"{self._inst} {self._type[ATTR_GROUP]}",
        }
        if ATTR_GROUP in self._type:
            info["identifiers"] = {
                (
                    DOMAIN,
                    "serial-number",
                    self._ctrl.data["routerboard"]["serial-number"],
                    "switch",
                    self._type[ATTR_GROUP],
                )
            }

        return info

    async def async_update(self):
        """Synchronize state with controller."""

    async def async_added_to_hass(self):
        """Port entity created."""
        _LOGGER.debug("New sensor %s (%s)", self._inst, self._sensor)

    @property
    def is_on(self):
        """Return true if sensor is on."""
        val = False
        if self._attr in self._data:
            val = self._data[self._attr]

        return val
