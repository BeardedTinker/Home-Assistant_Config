"""Support for the Mikrotik Router device tracker."""

from __future__ import annotations

from logging import getLogger
from collections.abc import Mapping
from datetime import timedelta
from typing import Any, Callable

from homeassistant.components.device_tracker.config_entry import ScannerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.const import STATE_NOT_HOME
from homeassistant.helpers import (
    entity_platform as ep,
    entity_registry as er,
)
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import slugify
from homeassistant.util.dt import utcnow

from homeassistant.components.device_tracker.const import SourceType

from .device_tracker_types import SENSOR_TYPES, SENSOR_SERVICES
from .coordinator import MikrotikCoordinator
from .entity import _skip_sensor, MikrotikEntity
from .helper import format_attribute
from .const import (
    DOMAIN,
    CONF_TRACK_HOSTS,
    DEFAULT_TRACK_HOSTS,
    CONF_TRACK_HOSTS_TIMEOUT,
    DEFAULT_TRACK_HOST_TIMEOUT,
)

_LOGGER = getLogger(__name__)


async def async_add_entities(
    hass: HomeAssistant, config_entry: ConfigEntry, dispatcher: dict[str, Callable]
):
    """Add entities."""
    platform = ep.async_get_current_platform()
    services = platform.platform.SENSOR_SERVICES
    descriptions = platform.platform.SENSOR_TYPES

    for service in services:
        platform.async_register_entity_service(service[0], service[1], service[2])

    @callback
    async def async_update_controller(coordinator):
        """Update the values of the controller."""
        if coordinator.data is None:
            return

        async def async_check_exist(obj, coordinator, uid: None) -> None:
            """Check entity exists."""
            entity_registry = er.async_get(hass)
            if uid:
                unique_id = f"{obj._inst.lower()}-{obj.entity_description.key}-{slugify(str(obj._data[obj.entity_description.data_reference]).lower())}"
            else:
                unique_id = f"{obj._inst.lower()}-{obj.entity_description.key}"

            entity_id = entity_registry.async_get_entity_id(
                platform.domain, DOMAIN, unique_id
            )
            entity = entity_registry.async_get(entity_id)
            if entity is None or (
                (entity_id not in platform.entities) and (entity.disabled is False)
            ):
                _LOGGER.debug("Add entity %s", entity_id)
                await platform.async_add_entities([obj])

        for entity_description in descriptions:
            data = coordinator.data[entity_description.data_path]
            if not entity_description.data_reference:
                if data.get(entity_description.data_attribute) is None:
                    continue
                obj = dispatcher[entity_description.func](
                    coordinator, entity_description
                )
                await async_check_exist(obj, coordinator, None)
            else:
                for uid in data:
                    if _skip_sensor(config_entry, entity_description, data, uid):
                        continue
                    obj = dispatcher[entity_description.func](
                        coordinator, entity_description, uid
                    )
                    await async_check_exist(obj, coordinator, uid)

    await async_update_controller(
        hass.data[DOMAIN][config_entry.entry_id].tracker_coordinator
    )

    unsub = async_dispatcher_connect(hass, "update_sensors", async_update_controller)
    config_entry.async_on_unload(unsub)


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
        "MikrotikDeviceTracker": MikrotikDeviceTracker,
        "MikrotikHostDeviceTracker": MikrotikHostDeviceTracker,
    }
    await async_add_entities(hass, config_entry, dispatcher)


# ---------------------------
#   MikrotikDeviceTracker
# ---------------------------
class MikrotikDeviceTracker(MikrotikEntity, ScannerEntity):
    """Representation of a device tracker."""

    def __init__(
        self,
        coordinator: MikrotikCoordinator,
        entity_description,
        uid: str | None = None,
    ):
        """Initialize entity"""
        super().__init__(coordinator, entity_description, uid)
        self._attr_name = None

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
        return SourceType.ROUTER


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
        return self.coordinator.option_zone if self.is_connected else STATE_NOT_HOME

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        attributes = super().extra_state_attributes
        if self.is_connected:
            attributes[format_attribute("last-seen")] = "Now"

        if not attributes[format_attribute("last-seen")]:
            attributes[format_attribute("last-seen")] = "Unknown"

        return attributes
