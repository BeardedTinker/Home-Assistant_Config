"""Base Uptime Kuma entity."""
from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo, EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from pyuptimekuma import UptimeKumaMonitor

from . import UptimeKumaDataUpdateCoordinator
from .const import ATTRIBUTION, DOMAIN

# from uptime_kuma_monitor import UptimeKumaMonitor


class UptimeKumaEntity(CoordinatorEntity[UptimeKumaDataUpdateCoordinator]):
    """Base UptimeKuma entity."""

    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        coordinator: UptimeKumaDataUpdateCoordinator,
        description: EntityDescription,
        monitor: UptimeKumaMonitor,
    ) -> None:
        """Initialize UptimeRobot entities."""
        super().__init__(coordinator)
        self.entity_description = description
        self._monitor = monitor
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, str(self.monitor.monitor_name))},
            name=self.monitor.monitor_name,
            manufacturer="Uptime Kuma Integration",
            entry_type=DeviceEntryType.SERVICE,
            model=self.monitor.monitor_type,
        )
        self._attr_extra_state_attributes = {
            "monitor_cert_days_remaining": self.monitor.monitor_cert_days_remaining,
            "monitor_cert_is_valid": self.monitor.monitor_cert_is_valid,
            "monitor_hostname": self.monitor.monitor_hostname,
            "monitor_name": self.monitor.monitor_name,
            "monitor_port": self.monitor.monitor_port,
            "monitor_response_time": self.monitor.monitor_response_time,
            "monitor_status": self.monitor.monitor_status,
            "monitor_type": self.monitor.monitor_type,
            "monitor_url": self.monitor.monitor_url,
        }
        self._attr_unique_id = f"uptimekuma_{self.monitor.monitor_name}"
        self.api = coordinator.api

    @property
    def _monitors(self) -> list[UptimeKumaMonitor]:
        """Return all monitors."""
        return self.coordinator.data or []

    @property
    def monitor(self) -> UptimeKumaMonitor:
        """Return the monitor for this entity."""
        return next(
            (
                monitor
                for monitor in self._monitors
                if str(monitor.monitor_name) == self.entity_description.key
            ),
            self._monitor,
        )

    @property
    def monitor_available(self) -> bool:
        """Returtn if the monitor is available."""
        return bool(
            self.monitor.monitor_status == 1.0 or self.monitor.monitor_status == 2.0
        )
