"""Implementation of Mikrotik Router sensor entities."""

import logging
from typing import Any, Optional
from collections.abc import Mapping
from homeassistant.components.sensor import SensorEntity
from .helper import format_attribute
from .model import model_async_setup_entry, MikrotikEntity
from .sensor_types import (
    SENSOR_TYPES,
    SENSOR_SERVICES,
    DEVICE_ATTRIBUTES_IFACE_ETHER,
    DEVICE_ATTRIBUTES_IFACE_SFP,
)

_LOGGER = logging.getLogger(__name__)


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up entry for component"""
    dispatcher = {
        "MikrotikSensor": MikrotikSensor,
        "MikrotikInterfaceTrafficSensor": MikrotikInterfaceTrafficSensor,
        "MikrotikClientTrafficSensor": MikrotikClientTrafficSensor,
    }
    await model_async_setup_entry(
        hass,
        config_entry,
        async_add_entities,
        SENSOR_SERVICES,
        SENSOR_TYPES,
        dispatcher,
    )


# ---------------------------
#   MikrotikSensor
# ---------------------------
class MikrotikSensor(MikrotikEntity, SensorEntity):
    """Define an Mikrotik Controller sensor."""

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


# ---------------------------
#   MikrotikInterfaceTrafficSensor
# ---------------------------
class MikrotikInterfaceTrafficSensor(MikrotikSensor):
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
class MikrotikClientTrafficSensor(MikrotikSensor):
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
