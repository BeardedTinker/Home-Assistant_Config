"""Definition and setup of the SpaceX Binary Sensors for Home Assistant."""

import logging
import time

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.components.sensor import ENTITY_ID_FORMAT

from .const import COORDINATOR, DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities, discovery_info=None):
    """Set up the binary sensor platforms."""

    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    sensors = []

    sensors.append(
        SpaceXBinarySensor(
            coordinator,
            "Next Launch Confirmed",
            "spacex_next_launch_confirmed",
            "mdi:check-circle",
        )
    )

    sensors.append(
        SpaceXBinarySensor(
            coordinator,
            "Launch within 24 Hours",
            "spacex_launch_24_hour_warning",
            "mdi:rocket",
        )
    )

    sensors.append(
        SpaceXBinarySensor(
            coordinator,
            "Launch within 20 Minutes",
            "spacex_launch_20_minute_warning",
            "mdi:rocket-launch",
        )
    )

    async_add_entities(sensors, update_before_add=True)


class SpaceXBinarySensor(BinarySensorEntity):
    """Defines a SpaceX Binary sensor."""

    def __init__(self, coordinator, name, entity_id, icon):
        """Initialize Entities."""

        self._name = name
        self.entity_id = ENTITY_ID_FORMAT.format(entity_id)
        self._state = None
        self._icon = icon
        self._kind = entity_id
        self.coordinator = coordinator
        self.attrs = {}

    @property
    def should_poll(self):
        """Return the polling requirement of an entity."""
        return True

    @property
    def unique_id(self):
        """Return the unique Home Assistant friendly identifier for this entity."""
        return self.entity_id

    @property
    def name(self):
        """Return the friendly name of this entity."""
        return self._name

    @property
    def icon(self):
        """Return the icon for this entity."""
        return self._icon

    @property
    def device_state_attributes(self):
        """Return the attributes."""
        return self.attrs

    @property
    def is_on(self) -> bool:
        """Return the state."""
        return self._state

    async def async_update(self):
        """Update SpaceX Binary Sensor Entity."""
        await self.coordinator.async_request_refresh()
        _LOGGER.debug("Updating state of the sensors.")
        coordinator_data = self.coordinator.data
        launch_data = coordinator_data[1]

        if self._kind == "spacex_next_launch_confirmed":
            self.attrs["last_updated"] = launch_data.get("last_date_update")
            if launch_data.get("is_tentative") is True:
                self._state = False
                self._icon = "mdi:do-not-disturb"
            else:
                self._state = True
                self._icon = "mdi:check-circle"

        elif self._kind == "spacex_launch_24_hour_warning":
            if launch_data.get("launch_date_unix") < (
                time.time() + (24 * 60 * 60)
            ) and launch_data.get("launch_date_unix") > (time.time()):
                self._state = True
            else:
                self._state = False

        elif self._kind == "spacex_launch_20_minute_warning":
            if launch_data.get("launch_date_unix") < (
                time.time() + (20 * 60)
            ) and launch_data.get("launch_date_unix") > (time.time()):
                self._state = True
            else:
                self._state = False

    async def async_added_to_hass(self):
        """Subscribe to updates."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
