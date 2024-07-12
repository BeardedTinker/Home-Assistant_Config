from homeassistant.const import EntityCategory, Platform
from homeassistant.core import callback
from homeassistant.helpers.device_registry import DeviceInfo
from .coordinator import GrowcubeDataCoordinator
from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from .const import DOMAIN, CHANNEL_NAME, CHANNEL_ID
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Growcube sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([DeviceLockedSensor(coordinator),
                        WaterWarningSensor(coordinator),
                        PumpOpenStateSensor(coordinator, 0),
                        PumpOpenStateSensor(coordinator, 1),
                        PumpOpenStateSensor(coordinator, 2),
                        PumpOpenStateSensor(coordinator, 3),
                        OutletLockedSensor(coordinator, 0),
                        OutletLockedSensor(coordinator, 1),
                        OutletLockedSensor(coordinator, 2),
                        OutletLockedSensor(coordinator, 3),
                        OutletBlockedSensor(coordinator, 0),
                        OutletBlockedSensor(coordinator, 1),
                        OutletBlockedSensor(coordinator, 2),
                        OutletBlockedSensor(coordinator, 3),
                        SensorFaultSensor(coordinator, 0),
                        SensorFaultSensor(coordinator, 1),
                        SensorFaultSensor(coordinator, 2),
                        SensorFaultSensor(coordinator, 3),
                        SensorDisconnectedSensor(coordinator, 0),
                        SensorDisconnectedSensor(coordinator, 1),
                        SensorDisconnectedSensor(coordinator, 2),
                        SensorDisconnectedSensor(coordinator, 3),
                        ], True)


class DeviceLockedSensor(BinarySensorEntity):
    def __init__(self, coordinator: GrowcubeDataCoordinator):
        self._coordinator = coordinator
        self._coordinator.entities.append(self)
        self._attr_unique_id = f"{coordinator.data.device_id}_device_locked"
        self.entity_id = f"{Platform.SENSOR}.{self._attr_unique_id}"
        self._attr_name = f"Device locked"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_native_value = coordinator.data.device_locked

    @property
    def device_info(self) -> DeviceInfo | None:
        return self._coordinator.data.device_info

    @property
    def is_on(self):
        """Return True if the binary sensor is on."""
        return self._coordinator.data.device_locked

    @callback
    def update(self) -> None:
        _LOGGER.debug("%s: Update device_locked %s",
                      self._coordinator.data.device_id,
                      self._coordinator.data.device_locked
                      )
        if self._coordinator.data.device_locked != self._attr_native_value:
            self._attr_native_value = self._coordinator.data.device_locked
            self.schedule_update_ha_state()


class WaterWarningSensor(BinarySensorEntity):
    def __init__(self, coordinator: GrowcubeDataCoordinator):
        self._coordinator = coordinator
        self._coordinator.entities.append(self)
        self._attr_unique_id = f"{coordinator.data.device_id}_water_warning"
        self.entity_id = f"{Platform.SENSOR}.{self._attr_unique_id}"
        self._attr_name = f"Water warning"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_native_value = coordinator.data.water_warning

    @property
    def device_info(self) -> DeviceInfo | None:
        return self._coordinator.data.device_info

    @property
    def icon(self):
        if self.is_on:
            return "mdi:water-alert"
        else:
            return "mdi:water-check"

    @property
    def is_on(self):
        return self._coordinator.data.water_warning

    @callback
    def update(self) -> None:
        _LOGGER.debug("%s: Update water_state %s",
                      self._coordinator.data.device_id,
                      self._coordinator.data.water_warning
                      )
        if self._coordinator.data.water_warning != self._attr_native_value:
            self._attr_native_value = self._coordinator.data.water_warning
            self.schedule_update_ha_state()


class PumpOpenStateSensor(BinarySensorEntity):
    def __init__(self, coordinator: GrowcubeDataCoordinator, channel: int) -> None:
        self._coordinator = coordinator
        self._coordinator.entities.append(self)
        self._channel = channel
        self._attr_unique_id = f"{coordinator.data.device_id}_pump_" + CHANNEL_ID[channel] + "_open"
        self.entity_id = f"{Platform.SENSOR}.{self._attr_unique_id}"
        self._attr_name = f"Pump " + CHANNEL_NAME[channel] + " open"
        self._attr_device_class = BinarySensorDeviceClass.OPENING
        self._attr_native_value = coordinator.data.pump_open[self._channel]
        self._attr_entity_registry_enabled_default = False

    @property
    def device_info(self) -> DeviceInfo | None:
        return self._coordinator.data.device_info

    @property
    def icon(self):
        if self.is_on:
            return "mdi:water"
        else:
            return "mdi:water-off"

    @property
    def is_on(self):
        """Return True if the binary sensor is on."""
        return self._coordinator.data.pump_open[self._channel]

    @callback
    def update(self) -> None:
        _LOGGER.debug("%s: Update pump_state[%s] %s",
                      self._coordinator.data.device_id,
                      self._channel,
                      self._coordinator.data.pump_open[self._channel]
                      )
        if self._coordinator.data.pump_open[self._channel] != self._attr_native_value:
            self._attr_native_value = self._coordinator.data.pump_open[self._channel]
            self.schedule_update_ha_state()


class OutletLockedSensor(BinarySensorEntity):
    def __init__(self, coordinator: GrowcubeDataCoordinator, channel: int) -> None:
        self._coordinator = coordinator
        self._coordinator.entities.append(self)
        self._channel = channel
        self._attr_unique_id = f"{coordinator.data.device_id}_outlet_" + CHANNEL_ID[channel] + "_locked"
        self.entity_id = f"{Platform.SENSOR}.{self._attr_unique_id}"
        self._attr_name = f"Outlet " + CHANNEL_NAME[channel] + " locked"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_native_value = coordinator.data.outlet_locked_state[self._channel]

    @property
    def device_info(self) -> DeviceInfo | None:
        return self._coordinator.data.device_info

    @property
    def icon(self):
        if self.is_on:
            return "mdi:pump-off"
        else:
            return "mdi:pump"

    @property
    def is_on(self):
        """Return True if the binary sensor is on."""
        return self._coordinator.data.outlet_locked_state[self._channel]

    @callback
    def update(self) -> None:
        _LOGGER.debug("%s: Update pump_lock_state[%s] %s",
                      self._coordinator.data.device_id,
                      self._channel,
                      self._coordinator.data.outlet_locked_state[self._channel]
                      )
        if self._coordinator.data.outlet_locked_state[self._channel] != self._attr_native_value:
            self._attr_native_value = self._coordinator.data.outlet_locked_state[self._channel]
            self.schedule_update_ha_state()


class OutletBlockedSensor(BinarySensorEntity):
    def __init__(self, coordinator: GrowcubeDataCoordinator, channel: int) -> None:
        self._coordinator = coordinator
        self._coordinator.entities.append(self)
        self._channel = channel
        self._attr_unique_id = f"{coordinator.data.device_id}_outlet_" + CHANNEL_ID[channel] + "_blocked"
        self.entity_id = f"{Platform.SENSOR}.{self._attr_unique_id}"
        self._attr_name = f"Outlet " + CHANNEL_NAME[channel] + " blocked"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_native_value = coordinator.data.outlet_blocked_state[self._channel]

    @property
    def device_info(self) -> DeviceInfo | None:
        return self._coordinator.data.device_info

    @property
    def icon(self):
        if self.is_on:
            return "mdi:water-pump-off"
        else:
            return "mdi:water-pump"

    @property
    def is_on(self):
        """Return True if the binary sensor is on."""
        return self._coordinator.data.outlet_blocked_state[self._channel]

    @callback
    def update(self) -> None:
        _LOGGER.debug("%s: Update pump_lock_state[%s] %s",
                      self._coordinator.data.device_id,
                      self._channel,
                      self._coordinator.data.outlet_blocked_state[self._channel]
                      )
        if self._coordinator.data.outlet_blocked_state[self._channel] != self._attr_native_value:
            self._attr_native_value = self._coordinator.data.outlet_blocked_state[self._channel]
            self.schedule_update_ha_state()


class SensorFaultSensor(BinarySensorEntity):
    def __init__(self, coordinator: GrowcubeDataCoordinator, channel: int) -> None:
        self._coordinator = coordinator
        self._coordinator.entities.append(self)
        self._channel = channel
        self._attr_unique_id = f"{coordinator.data.device_id}_sensor_" + CHANNEL_ID[channel] + "_fault"
        self.entity_id = f"{Platform.SENSOR}.{self._attr_unique_id}"
        self._attr_name = f"Sensor " + CHANNEL_NAME[channel] + " fault"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_native_value = coordinator.data.sensor_abnormal[self._channel]

    @property
    def device_info(self) -> DeviceInfo | None:
        return self._coordinator.data.device_info

    @property
    def icon(self):
        if self.is_on:
            return "mdi:thermometer-probe-off"
        else:
            return "mdi:thermometer-probe"

    @property
    def is_on(self):
        """Return True if the binary sensor is on."""
        return self._coordinator.data.sensor_abnormal[self._channel]

    @callback
    def update(self) -> None:
        _LOGGER.debug("%s: Update sensor_state[%s] %s",
                      self._coordinator.data.device_id,
                      self._channel,
                      self._coordinator.data.sensor_abnormal[self._channel]
                      )
        if self._coordinator.data.sensor_abnormal[self._channel] != self._attr_native_value:
            self._attr_native_value = self._coordinator.data.sensor_abnormal[self._channel]
            self.schedule_update_ha_state()


class SensorDisconnectedSensor(BinarySensorEntity):
    def __init__(self, coordinator: GrowcubeDataCoordinator, channel: int) -> None:
        self._coordinator = coordinator
        self._coordinator.entities.append(self)
        self._channel = channel
        self._attr_unique_id = f"{coordinator.data.device_id}_sensor_" + CHANNEL_ID[channel] + "_disconnected"
        self.entity_id = f"{Platform.SENSOR}.{self._attr_unique_id}"
        self._attr_name = f"Sensor " + CHANNEL_NAME[channel] + " disconnected"
        self._attr_device_class = BinarySensorDeviceClass.PROBLEM
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_native_value = coordinator.data.sensor_disconnected[self._channel]

    @property
    def device_info(self) -> DeviceInfo | None:
        return self._coordinator.data.device_info

    @property
    def icon(self):
        if self.is_on:
            return "mdi:thermometer-probe-off"
        else:
            return "mdi:thermometer-probe"

    @property
    def is_on(self):
        """Return True if the binary sensor is on."""
        return self._coordinator.data.sensor_disconnected[self._channel]

    @callback
    def update(self) -> None:
        _LOGGER.debug("%s: Update sensor_state[%s] %s",
                      self._coordinator.data.device_id,
                      self._channel,
                      self._coordinator.data.sensor_disconnected[self._channel]
                      )
        if self._coordinator.data.sensor_disconnected[self._channel] != self._attr_native_value:
            self._attr_native_value = self._coordinator.data.sensor_disconnected[self._channel]
            self.schedule_update_ha_state()
