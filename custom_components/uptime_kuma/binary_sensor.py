"""Summary binary data from Uptime Kuma."""
from voluptuous.validators import Boolean

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Defer sensor setup to the shared sensor module."""
    coordinator = hass.data[DOMAIN]
    async_add_entities(
        UptimeKumaBinarySensor(coordinator, monitor) for monitor in coordinator.data
    )


class UptimeKumaBinarySensor(BinarySensorEntity, CoordinatorEntity):
    """Represents an Uptime Kuma binary sensor."""

    _attr_icon = "mdi:cloud"

    def __init__(self, coordinator: DataUpdateCoordinator, monitor: str) -> None:
        """Initialize the Uptime Kuma binary sensor."""
        super().__init__(coordinator)

        self._attr_name = monitor

    @property
    def is_on(self) -> Boolean:
        """Return true if the binary sensor is on."""
        return self.coordinator.data[self.name]["monitor_status"] == 1.0
