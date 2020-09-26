"""Definition and setup of the SpaceX Binary Sensors for Home Assistant."""

import logging
import time

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.const import ATTR_NAME
from homeassistant.components.sensor import ENTITY_ID_FORMAT
from . import SpaceXUpdateCoordinator
from .const import ATTR_IDENTIFIERS, ATTR_MANUFACTURER, ATTR_MODEL, DOMAIN, COORDINATOR

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the binary sensor platforms."""

    coordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    sensors = []

    sensors.append(
        SpaceXBinarySensor(
            coordinator,
            "Next Launch Confirmed",
            "spacex_next_launch_confirmed",
            "mdi:check-circle",
            "spacexlaunch",
        )
    )

    sensors.append(
        SpaceXBinarySensor(
            coordinator,
            "Launch within 24 Hours",
            "spacex_launch_24_hour_warning",
            "mdi:rocket",
            "spacexlaunch",
        )
    )

    sensors.append(
        SpaceXBinarySensor(
            coordinator,
            "Launch within 20 Minutes",
            "spacex_launch_20_minute_warning",
            "mdi:rocket-launch",
            "spacexlaunch",
        )
    )

    async_add_entities(sensors)


class SpaceXBinarySensor(BinarySensorEntity):
    """Defines a SpaceX Binary sensor."""

    def __init__(
        self, 
        coordinator: SpaceXUpdateCoordinator, 
        name: str, 
        entity_id: str, 
        icon: str,
        device_identifier: str,
        ):
        """Initialize Entities."""

        self._name = name
        self._unique_id = f"spacex_{entity_id}"
        self._state = None
        self._icon = icon
        self._kind = entity_id
        self._device_identifier = device_identifier
        self.coordinator = coordinator
        self.attrs = {}

    @property
    def should_poll(self) -> bool:
        """No need to poll. Coordinator notifies entity of updates."""
        return False

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success

    @property
    def unique_id(self):
        """Return the unique Home Assistant friendly identifier for this entity."""
        return self._unique_id

    @property
    def name(self):
        """Return the friendly name of this entity."""
        return self._name

    @property
    def icon(self):
        """Return the icon for this entity."""
        launch_data = self.coordinator.data["next_launch"]

        if self._kind == "spacex_next_launch_confirmed":
            if launch_data.get("is_tentative") is True:
                return "mdi:do-not-disturb"
            else:
                return "mdi:check-circle"

        else:
            return self._icon

    @property
    def device_state_attributes(self):
        """Return the attributes."""
        launch_data = self.coordinator.data["next_launch"]

        self.attrs["last_updated"] = launch_data["last_date_update"]

        return self.attrs

    @property
    def device_info(self):
        """Define the device based on device_identifier."""

        device_name = "SpaceX Launches"
        device_model = "Launch"

        if self._device_identifier != "spacexlaunch":
            device_name = "SpaceX Starman"
            device_model = "Starman"

        return {
            ATTR_IDENTIFIERS: {(DOMAIN, self._device_identifier)},
            ATTR_NAME: device_name,
            ATTR_MANUFACTURER: "SpaceX",
            ATTR_MODEL: device_model,
        }

    @property
    def is_on(self) -> bool:
        """Return the state."""
        launch_data = self.coordinator.data["next_launch"]

        if self._kind == "spacex_next_launch_confirmed":
            if launch_data["is_tentative"] is True:
                return False
            else:
                return True

        elif self._kind == "spacex_launch_24_hour_warning":
            if launch_data["launch_date_unix"] < (
                time.time() + (24 * 60 * 60)
            ) and launch_data["launch_date_unix"] > (time.time()):
                return True
            else:
                return False

        elif self._kind == "spacex_launch_20_minute_warning":
            if launch_data["launch_date_unix"] < (
                time.time() + (20 * 60)
            ) and launch_data["launch_date_unix"] > (time.time()):
                return True
            else:
                return False

    async def async_update(self):
        """Update SpaceX Binary Sensor Entity."""
        await self.coordinator.async_request_refresh()
        
    async def async_added_to_hass(self):
        """Subscribe to updates."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
