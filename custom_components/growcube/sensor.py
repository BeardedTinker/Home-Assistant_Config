"""Support for Growcube sensors."""
from homeassistant.const import PERCENTAGE, UnitOfTemperature, Platform
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN, CHANNEL_ID, CHANNEL_NAME
import logging

from .coordinator import GrowcubeDataCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Growcube sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([TemperatureSensor(coordinator),
                        HumiditySensor(coordinator),
                        MoistureSensor(coordinator, 0),
                        MoistureSensor(coordinator, 1),
                        MoistureSensor(coordinator, 2),
                        MoistureSensor(coordinator, 3)], True)


class TemperatureSensor(SensorEntity):
    def __init__(self, coordinator: GrowcubeDataCoordinator) -> None:
        self._coordinator = coordinator
        self._coordinator.entities.append(self)
        self._attr_unique_id = f"{coordinator.data.device_id}" + "_temperature"
        self.entity_id = f"{Platform.SENSOR}.{self._attr_unique_id}"
        self._attr_native_value = coordinator.data.temperature
        self._attr_name = "Temperature"
        self._attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
        self._attr_device_class = SensorDeviceClass.TEMPERATURE
        self.temperature = coordinator.data.temperature

    @property
    def device_info(self) -> DeviceInfo | None:
        return self._coordinator.data.device_info

    @callback
    def update(self) -> None:
        _LOGGER.debug(
            "%s: Update temperature %s",
            self._coordinator.data.device_id,
            self._coordinator.data.temperature
        )
        if self._coordinator.data.temperature != self.temperature:
            self._attr_native_value = self._coordinator.data.temperature
            self.schedule_update_ha_state()


class HumiditySensor(SensorEntity):
    def __init__(self, coordinator: GrowcubeDataCoordinator) -> None:
        self._coordinator = coordinator
        self._coordinator.entities.append(self)
        self._attr_unique_id = f"{coordinator.data.device_id}" + "_humidity"
        self.entity_id = f"{Platform.SENSOR}.{self._attr_unique_id}"
        self._attr_native_value = coordinator.data.humidity
        self._attr_name = "Humidity"
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_device_class = SensorDeviceClass.HUMIDITY

    @property
    def device_info(self) -> DeviceInfo | None:
        return self._coordinator.data.device_info

    @callback
    def update(self) -> None:
        _LOGGER.debug(
            "%s: Update humidity %s",
            self._coordinator.data.device_id,
            self._coordinator.data.humidity
        )
        if self._coordinator.data.humidity != self._attr_native_value:
            self._attr_native_value = self._coordinator.data.humidity
            self.schedule_update_ha_state()


class MoistureSensor(SensorEntity):
    def __init__(self, coordinator: GrowcubeDataCoordinator, channel: int) -> None:
        """Initialize the sensor."""
        self._coordinator = coordinator
        self._coordinator.entities.append(self)
        self._channel = channel
        self._attr_unique_id = f"{coordinator.data.device_id}" + "_moisture_" + CHANNEL_ID[self._channel]
        self.entity_id = f"{Platform.SENSOR}.{self._attr_unique_id}"
        self._attr_name = "Moisture " + CHANNEL_NAME[self._channel]
        self._attr_native_unit_of_measurement = PERCENTAGE
        self._attr_device_class = SensorDeviceClass.MOISTURE
        self._attr_native_value = coordinator.data.moisture[self._channel]

    @property
    def device_info(self) -> DeviceInfo | None:
        return self._coordinator.data.device_info

    @property
    def icon(self):
        return "mdi:cup-water"

    @callback
    def update(self) -> None:
        _LOGGER.debug(
            "%s: Update moisture[%s] %s",
            self._coordinator.data.device_id,
            self._channel,
            self._coordinator.data.moisture[self._channel]
        )
        if self._coordinator.data.moisture[self._channel] != self._attr_native_value:
            self._attr_native_value = self._coordinator.data.moisture[self._channel]
            self.schedule_update_ha_state()
