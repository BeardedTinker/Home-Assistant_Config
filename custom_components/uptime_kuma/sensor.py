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
from .utils import format_entity_name, sensor_name_from_url


class StatusValue(TypedDict):
    """Sensor details."""

    value: str
    icon: str

SYSTEM_INFO = {
    0.0: StatusValue(value="degraded", icon="mdi:alert"),
    1.0: StatusValue(value="up", icon="mdi:check-circle-outline"),
    2.0: StatusValue(value="down", icon="mdi:alpha-x-circle-outline"),
}

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
    async_add_entities(
        [UptimeKumaSummarySensor(
            coordinator,
            SensorEntityDescription(
                key=sensor_name_from_url(coordinator.api._base_url)+"system_summary",
                name=sensor_name_from_url(coordinator.api._base_url)+"system_summary",
                entity_category=EntityCategory.DIAGNOSTIC,
                device_class="uptimekuma__monitor_status",
            )
        )]
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


class UptimeKumaSummarySensor(SensorEntity):
    """Representation of a UptimeKuma sensor."""

    def __init__(
        self,
        coordinator: UptimeKumaDataUpdateCoordinator,
        description: EntityDescription
    ) -> None:
        """Set entity ID."""
        super().__init__()
        self.description=description
        self.coordinator=coordinator
        self.ups=0
        self.downs=0
        self.pendings=0
        self.ukstate=0.0
        self.entity_id = ("sensor.uptimekuma_"+sensor_name_from_url(coordinator.api._base_url))

        self._attr_extra_state_attributes = {
            "monitors": len(self.coordinator.data),
            "monitors_up": self.ups,
            "monitors_down": self.downs,
            "monitors_pending": self.pendings,
        }

    def determine_status(self):
        self.downs=0
        self.ups=0
        self.pendings=0
        for m in self.coordinator.data:
            if m.monitor_status == 0.0:
                self.downs+=1
            elif m.monitor_status == 1.0:
                self.ups+=1
            elif m.monitor_status == 2.0:
                self.pendings+=1

        self._attr_extra_state_attributes = {
            "monitors": len(self.coordinator.data),
            "monitors_up": self.ups,
            "monitors_down": self.downs,
            "monitors_pending": self.pendings,
        }

        if self.downs==0 and self.pendings==0:
            self.ukstate=1.0
        elif self.ups==0 and self.pendings==0:
            self.ukstate=2.0
        else:
            self.ukstate=0.0

        return self.ukstate

    @property
    def native_value(self) -> str:
        """Return the status of the monitor."""    
        return SYSTEM_INFO[self.determine_status()]["value"]

    @property
    def icon(self) -> str:
        """Return the status of the monitor."""
        return SYSTEM_INFO[self.determine_status()]["icon"]
