"""Joke Sensor."""

from .const import DOMAIN
from homeassistant import core
from homeassistant.helpers.update_coordinator import CoordinatorEntity, DataUpdateCoordinator

async def async_setup_platform(
    hass: core.HomeAssistant, config, async_add_entities, discovery_info=None
):
    """Setup the sensor platform."""
    coordinator = hass.data[DOMAIN]["coordinator"]
    async_add_entities([JokeEntity(coordinator)], True)

class JokeEntity(CoordinatorEntity):
    """Dummy entity to trigger updates."""

    _attr_icon = "mdi:emoticon-excited-outline"

    def __init__(self, coordinator: DataUpdateCoordinator):
        """Pass coordinator to CoordinatorEntity."""
        super().__init__(coordinator)

    @property
    def entity_id(self):
        """Return the entity id of the sensor."""
        return "sensor.random_joke"

    @property
    def name(self):
        """Return the name of the sensor."""
        return "Random Joke"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.coordinator.data["joke"]

    @property
    def extra_state_attributes(self):
        return self.coordinator.data
    