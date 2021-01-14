"""Reolink parent entity class."""

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import BASE, COORDINATOR, DOMAIN


class ReolinkEntity(CoordinatorEntity):
    """Parent class for Reolink Entities."""

    def __init__(self, hass, config):
        """Initialize common aspects of a Reolink entity."""
        coordinator = hass.data[DOMAIN][config.entry_id][COORDINATOR]
        super().__init__(coordinator)

        self._base = hass.data[DOMAIN][config.entry_id][BASE]
        self._hass = hass
        self._state = False

    @property
    def device_info(self):
        """Information about this entity/device."""
        return {
            "identifiers": {(DOMAIN, self._base.unique_id)},
            "connections": {(CONNECTION_NETWORK_MAC, self._base.api.mac_address)},
            "name": self._base.name,
            "sw_version": self._base.api.sw_version,
            "model": self._base.api.model,
            "manufacturer": self._base.api.manufacturer,
            "channel": self._base.channel
        }

    @property
    def available(self):
        """Return True if entity is available."""
        return self._base.api.session_active

    async def request_refresh(self):
        """Call the coordinator to update the API."""
        await self.coordinator.async_request_refresh()
