"""Support for the Mikrotik Router binary sensor service."""

import logging
from typing import Any
from collections.abc import Mapping
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
)
from .helper import format_attribute
from .const import (
    CONF_SENSOR_PPP,
    DEFAULT_SENSOR_PPP,
    CONF_SENSOR_PORT_TRACKER,
    DEFAULT_SENSOR_PORT_TRACKER,
)
from .model import model_async_setup_entry, MikrotikEntity
from .binary_sensor_types import (
    SENSOR_TYPES,
    SENSOR_SERVICES,
    DEVICE_ATTRIBUTES_IFACE_ETHER,
    DEVICE_ATTRIBUTES_IFACE_SFP,
    DEVICE_ATTRIBUTES_IFACE_WIRELESS,
)

_LOGGER = logging.getLogger(__name__)


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up entry for component"""
    dispatcher = {
        "MikrotikBinarySensor": MikrotikBinarySensor,
        "MikrotikPPPSecretBinarySensor": MikrotikPPPSecretBinarySensor,
        "MikrotikPortBinarySensor": MikrotikPortBinarySensor,
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
#   MikrotikBinarySensor
# ---------------------------
class MikrotikBinarySensor(MikrotikEntity, BinarySensorEntity):
    """Define an Mikrotik Controller Binary Sensor."""

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._data[self.entity_description.data_attribute]

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self.entity_description.icon_enabled:
            if self._data[self.entity_description.data_attribute]:
                return self.entity_description.icon_enabled
            else:
                return self.entity_description.icon_disabled


# ---------------------------
#   MikrotikPPPSecretBinarySensor
# ---------------------------
class MikrotikPPPSecretBinarySensor(MikrotikBinarySensor):
    """Representation of a network device."""

    @property
    def option_sensor_ppp(self) -> bool:
        """Config entry option."""
        return self._config_entry.options.get(CONF_SENSOR_PPP, DEFAULT_SENSOR_PPP)

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return (
            self._data[self.entity_description.data_attribute]
            if self.option_sensor_ppp
            else False
        )

    @property
    def available(self) -> bool:
        """Return if controller is available."""
        return self._ctrl.connected() if self.option_sensor_ppp else False


# ---------------------------
#   MikrotikPortBinarySensor
# ---------------------------
class MikrotikPortBinarySensor(MikrotikBinarySensor):
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
        return self._ctrl.connected() if self.option_sensor_port_tracker else False

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self._data[self.entity_description.data_attribute]:
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

        elif self._data["type"] == "wlan":
            for variable in DEVICE_ATTRIBUTES_IFACE_WIRELESS:
                if variable in self._data:
                    attributes[format_attribute(variable)] = self._data[variable]

        return attributes
