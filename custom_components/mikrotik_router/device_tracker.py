"""Support for the Mikrotik Router device tracker."""
import logging
from typing import Any
from collections.abc import Mapping
from datetime import timedelta
from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.components.device_tracker.const import SOURCE_TYPE_ROUTER
from homeassistant.const import STATE_NOT_HOME
from homeassistant.util.dt import get_age, utcnow
from .helper import format_attribute
from .const import (
    CONF_TRACK_HOSTS,
    DEFAULT_TRACK_HOSTS,
    CONF_TRACK_HOSTS_TIMEOUT,
    DEFAULT_TRACK_HOST_TIMEOUT,
)
from .model import model_async_setup_entry, MikrotikEntity
from .device_tracker_types import SENSOR_TYPES, SENSOR_SERVICES

_LOGGER = logging.getLogger(__name__)


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up entry for component"""
    dispatcher = {
        "MikrotikDeviceTracker": MikrotikDeviceTracker,
        "MikrotikHostDeviceTracker": MikrotikHostDeviceTracker,
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
#   MikrotikDeviceTracker
# ---------------------------
class MikrotikDeviceTracker(MikrotikEntity, ScannerEntity):
    """Representation of a device tracker."""

    @property
    def ip_address(self) -> str:
        """Return the primary ip address of the device."""
        return self._data["address"] if "address" in self._data else None

    @property
    def mac_address(self) -> str:
        """Return the mac address of the device."""
        if self.entity_description.data_reference in self._data:
            return self._data[self.entity_description.data_reference]

        return ""

    @property
    def hostname(self) -> str:
        """Return hostname of the device."""
        if self.entity_description.data_name in self._data:
            return self._data[self.entity_description.data_name]

        return ""

    @property
    def is_connected(self) -> bool:
        """Return true if device is connected."""
        return self._data[self.entity_description.data_attribute]

    @property
    def source_type(self) -> str:
        """Return the source type of the port."""
        return SOURCE_TYPE_ROUTER


# ---------------------------
#   MikrotikHostDeviceTracker
# ---------------------------
class MikrotikHostDeviceTracker(MikrotikDeviceTracker):
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
    def is_connected(self) -> bool:
        """Return true if the host is connected to the network."""
        if not self.option_track_network_hosts:
            return False

        if self._data["source"] in ["capsman", "wireless"]:
            return self._data[self.entity_description.data_attribute]

        return bool(
            self._data["last-seen"]
            and utcnow() - self._data["last-seen"]
            < self.option_track_network_hosts_timeout
        )

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self._data["source"] in ["capsman", "wireless"]:
            if self._data[self.entity_description.data_attribute]:
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
        return self._ctrl.option_zone if self.is_connected else STATE_NOT_HOME

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        attributes = super().extra_state_attributes
        if self.is_connected:
            attributes[format_attribute("last-seen")] = "Now"

        if not attributes[format_attribute("last-seen")]:
            attributes[format_attribute("last-seen")] = "Unknown"

        return attributes
