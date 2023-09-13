"""Mikrotik sensor platform."""
from __future__ import annotations

from logging import getLogger
from collections.abc import Mapping
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import MikrotikCoordinator
from .entity import MikrotikEntity, async_add_entities
from .helper import format_attribute
from .sensor_types import (
    SENSOR_TYPES,
    SENSOR_SERVICES,
    DEVICE_ATTRIBUTES_IFACE_ETHER,
    DEVICE_ATTRIBUTES_IFACE_SFP,
    DEVICE_ATTRIBUTES_IFACE_WIRELESS,
)

_LOGGER = getLogger(__name__)


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    _async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up entry for component"""
    dispatcher = {
        "MikrotikSensor": MikrotikSensor,
        "MikrotikInterfaceTrafficSensor": MikrotikInterfaceTrafficSensor,
        # "MikrotikClientTrafficSensor": MikrotikClientTrafficSensor,
    }
    await async_add_entities(hass, config_entry, dispatcher)


# ---------------------------
#   MikrotikSensor
# ---------------------------
class MikrotikSensor(MikrotikEntity, SensorEntity):
    """Define an Mikrotik sensor."""

    def __init__(
        self,
        coordinator: MikrotikCoordinator,
        entity_description,
        uid: str | None = None,
    ):
        super().__init__(coordinator, entity_description, uid)
        self._attr_suggested_unit_of_measurement = (
            self.entity_description.suggested_unit_of_measurement
        )

    @property
    def native_value(self) -> StateType | date | datetime | Decimal:
        """Return the value reported by the sensor."""
        return self._data[self.entity_description.data_attribute]

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit the value is expressed in."""
        if self.entity_description.native_unit_of_measurement:
            if self.entity_description.native_unit_of_measurement.startswith("data__"):
                uom = self.entity_description.native_unit_of_measurement[6:]
                if uom in self._data:
                    return self._data[uom]

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

        elif self._data["type"] == "wlan":
            for variable in DEVICE_ATTRIBUTES_IFACE_WIRELESS:
                if variable in self._data:
                    attributes[format_attribute(variable)] = self._data[variable]

        return attributes


# # ---------------------------
# #   MikrotikClientTrafficSensor
# # ---------------------------
# class MikrotikClientTrafficSensor(MikrotikSensor):
#     """Define an Mikrotik MikrotikClientTrafficSensor sensor."""
#
#     @property
#     def name(self) -> str:
#         """Return the name."""
#         return f"{self.entity_description.name}"
#
#     # @property
#     # def available(self) -> bool:
#     #     """Return if controller and accounting feature in Mikrotik is available.
#     #     Additional check for lan-tx/rx sensors
#     #     """
#     #     if self.entity_description.data_attribute in ["lan-tx", "lan-rx"]:
#     #         return (
#     #             self.coordinator.connected()
#     #             and self._data["available"]
#     #             and self._data["local_accounting"]
#     #         )
#     #     else:
#     #         return self.coordinator.connected() and self._data["available"]
