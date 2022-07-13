"""UptimeKuma sensor platform."""
from __future__ import annotations

from typing import TypedDict

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory, EntityDescription
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from pyuptimekuma import UptimeKumaMonitor

from . import UptimeKumaDataUpdateCoordinator
from .const import DOMAIN
from .entity import UptimeKumaEntity
from .utils import format_entity_name


class StatusValue(TypedDict):
    """Sensor details."""

    value: str
    icon: str


SENSORS_INFO = {
    0.0: StatusValue(value="down", icon="mdi:television-off"),
    1.0: StatusValue(value="up", icon="mdi:television-shimmer"),
    2.0: StatusValue(value="pending", icon="mdi:sync"),
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the UptimeKuma sensors."""
    coordinator: UptimeKumaDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        UptimeKumaSensor(
            coordinator,
            SensorEntityDescription(
                key=str(monitor.monitor_name),
                name=monitor.monitor_name,
                entity_category=EntityCategory.DIAGNOSTIC,
                device_class="uptimekuma__monitor_status",
            ),
            monitor=monitor,
        )
        for monitor in coordinator.data
    )


class UptimeKumaSensor(UptimeKumaEntity, SensorEntity):
    """Representation of a UptimeKuma sensor."""

    def __init__(
        self,
        coordinator: UptimeKumaDataUpdateCoordinator,
        description: EntityDescription,
        monitor: UptimeKumaMonitor,
    ) -> None:
        """Set entity ID."""
        super().__init__(coordinator, description, monitor)
        self.entity_id = (
            f"sensor.uptimekuma_{format_entity_name(self.monitor.monitor_name)}"
        )

    @property
    def native_value(self) -> str:
        """Return the status of the monitor."""
        return SENSORS_INFO[self.monitor.monitor_status]["value"]

    @property
    def icon(self) -> str:
        """Return the status of the monitor."""
        return SENSORS_INFO[self.monitor.monitor_status]["icon"]
