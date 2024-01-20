from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import EntityCategory

import logging
from datetime import datetime

from . import NukiEntity, NukiBridge
from .constants import DOMAIN
from .states import DoorSensorStates, LockStates, DoorSecurityStates

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    entities = []
    data = entry.as_dict()
    coordinator = hass.data[DOMAIN][entry.entry_id]

    if coordinator.api.can_bridge():
        entities.append(BridgeWifiVersion(coordinator))
        entities.append(BridgeVersion(coordinator))
    for dev_id in coordinator.data.get("devices", {}):
        entities.append(LockState(coordinator, dev_id))
        if coordinator.api.can_bridge():
            entities.append(RSSI(coordinator, dev_id))
        entities.append(LockVersion(coordinator, dev_id))
        if coordinator.device_supports(dev_id, "batteryChargeState"):
            entities.append(Battery(coordinator, dev_id))
        if coordinator.device_supports(dev_id, "doorsensorStateName"):
            entities.append(DoorSensorState(coordinator, dev_id))
            entities.append(DoorSecurityState(coordinator, dev_id))
        if coordinator.info_field(dev_id, None, "last_log"):
            entities.append(LastLog(coordinator, dev_id))
        if coordinator.info_field(dev_id, None, "last_unlock_log"):
            entities.append(LastUnlockUser(coordinator, dev_id))
        
    async_add_entities(entities)
    return True


class Battery(NukiEntity, SensorEntity):
    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("sensor", "battery")
        self.set_name("Battery")
        self._attr_device_class = "battery"
        self._attr_state_class = "measurement"

    @property
    def native_unit_of_measurement(self):
        return "%"

    @property
    def native_value(self):
        return self.last_state.get("batteryChargeState", 0)

    @property
    def state(self):
        return self.native_value

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class LockState(NukiEntity, SensorEntity):
    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("sensor", "state")
        self.set_name("State")
        self._attr_icon = "mdi:door"

    @property
    def state(self):
        return self.last_state.get("stateName")

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class RSSI(NukiEntity, SensorEntity):
    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("sensor", "rssi")
        self.set_name("RSSI")
        self._attr_device_class = "signal_strength"
        self._attr_state_class = "measurement"

    @property
    def native_unit_of_measurement(self):
        return "dBm"

    @property
    def native_value(self):
        return self.data.get("bridge_info", {}).get("rssi")

    @property
    def state(self):
        return self.native_value

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class DoorSensorState(NukiEntity, SensorEntity):
    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("sensor", "door_state")
        self.set_name("Door State")
        self._attr_icon = "mdi:door"

    @property
    def state(self):
        return self.last_state.get("doorsensorStateName")

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class DoorSecurityState(NukiEntity, SensorEntity):
    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("sensor", "door_security_state")
        self.set_name("Door Security State")
        self._attr_icon = "mdi:door-closed-lock"

    @property
    def icon(self):

        state = self.get_state()

        if state == DoorSecurityStates.CLOSED_AND_LOCKED:
            return "mdi:door-closed-lock"
        elif state == DoorSecurityStates.CLOSED_AND_UNLOCKED:
            return "mdi:door-closed"
        return "mdi:door-open"

    @property
    def state(self):
        return str(self.get_state())

    def get_state(self) -> DoorSecurityStates:
        lock_state = LockStates(self.last_state.get("state", LockStates.UNDEFINED.value))
        door_sensor_state = DoorSensorStates(
            self.last_state.get("doorsensorState"), DoorSensorStates.UNKNOWN.value)

        if lock_state == LockStates.LOCKED and door_sensor_state == DoorSensorStates.DOOR_CLOSED:
            return DoorSecurityStates.CLOSED_AND_LOCKED
        elif door_sensor_state == DoorSensorStates.DOOR_CLOSED:
            return DoorSecurityStates.CLOSED_AND_UNLOCKED
        return DoorSecurityStates.OPEN


class BridgeWifiVersion(NukiBridge, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.set_id("wifi_version")
        self.set_name("WiFi Firmware Version")

    @property
    def state(self):
        versions = self.data.get("versions", {})
        return versions.get("wifiFirmwareVersion")

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class BridgeVersion(NukiBridge, SensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.set_id("version")
        self.set_name("Firmware Version")

    @property
    def state(self):
        versions = self.data.get("versions", {})
        return versions.get("firmwareVersion")

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class LockVersion(NukiEntity, SensorEntity):

    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("sensor", "version")
        self.set_name("Firmware Version")

    @property
    def state(self):
        return self.data.get("firmwareVersion")

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

class LastLog(NukiEntity, SensorEntity):

    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("sensor", "last_log")
        self.set_name("Last Log")
        self._attr_icon = "mdi:history"

    @property
    def state(self):
        return self.coordinator.info_field(self.device_id, "Unknown", "last_log", "name")

    @property
    def extra_state_attributes(self):
        timestamp = self.coordinator.info_field(self.device_id, None, "last_log", "timestamp")
        action = self.coordinator.info_field(self.device_id, "unknown", "last_log", "action")
        return {
            "timestamp": datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else None,
            "action": action,
        }

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

class LastUnlockUser(NukiEntity, SensorEntity):

    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("sensor", "last_unlock_user")
        self.set_name("Last Unlock user")
        self._attr_icon = "mdi:account-lock-open"

    @property
    def state(self):
        return self.coordinator.info_field(self.device_id, "Unknown", "last_unlock_log", "name")

    @property
    def extra_state_attributes(self):
        timestamp = self.coordinator.info_field(self.device_id, None, "last_unlock_log", "timestamp")
        action = self.coordinator.info_field(self.device_id, "unknown", "last_unlock_log", "action")
        return {
            "timestamp": datetime.fromisoformat(timestamp) if isinstance(timestamp, str) else None,
            "action": action,
        }

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC