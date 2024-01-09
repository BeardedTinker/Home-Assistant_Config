from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.entity import EntityCategory

import logging

from . import NukiEntity, NukiBridge
from .constants import DOMAIN
from .states import DoorSensorStates, LockStates, LockModes

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    entities = []
    data = entry.as_dict()
    coordinator = hass.data[DOMAIN][entry.entry_id]

    for dev_id in coordinator.data.get("devices", {}):
        entities.append(BatteryLow(coordinator, dev_id))
        if coordinator.device_supports(dev_id, "batteryCharging"):
            entities.append(BatteryCharging(coordinator, dev_id))
        entities.append(LockState(coordinator, dev_id))
        if coordinator.device_supports(dev_id, "keypadBatteryCritical"):
            entities.append(KeypadBatteryLow(coordinator, dev_id))
        if coordinator.is_opener(dev_id):
            entities.append(RingAction(coordinator, dev_id))
        if coordinator.device_supports(dev_id, "doorsensorStateName"):
            entities.append(DoorState(coordinator, dev_id))
    if coordinator.api.can_bridge():
        entities.append(BridgeServerConnection(coordinator))
        entities.append(BridgeCallbackSet(coordinator))
    async_add_entities(entities)
    return True


class BatteryLow(NukiEntity, BinarySensorEntity):
    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("binary_sensor", "battery_low")
        self.set_name("Battery Critical")

    @property
    def is_on(self) -> bool:
        return self.last_state.get("batteryCritical", False)

    @property
    def device_class(self) -> str:
        return "battery"

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class BatteryCharging(NukiEntity, BinarySensorEntity):
    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("binary_sensor", "battery_charging")
        self.set_name("Battery Charging")
        self._attr_device_class = "battery_charging"

    @property
    def is_on(self) -> bool:
        return self.last_state.get("batteryCharging", False)

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class KeypadBatteryLow(NukiEntity, BinarySensorEntity):
    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("binary_sensor", "keypad_battery_low")
        self.set_name("Keypad Battery Critical")

    @property
    def is_on(self) -> bool:
        return self.last_state.get("keypadBatteryCritical", False)

    @property
    def device_class(self) -> str:
        return "battery"

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class RingAction(NukiEntity, BinarySensorEntity):
    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("binary_sensor", "ring_action")
        self.set_name("Ring Action")

    @property
    def is_on(self) -> bool:
        return self.last_state.get("ringactionState", False)

    @property
    def extra_state_attributes(self):
        return {
            "timestamp": self.last_state.get("ringactionTimestamp")
        }

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class LockState(NukiEntity, BinarySensorEntity):
    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("binary_sensor", "state")
        self.set_name("Locked")
        self._attr_device_class = "lock"

    @property
    def is_on(self) -> bool:
        currentMode = LockModes(self.last_state.get("mode", LockModes.DOOR_MODE.value))
        currentState = LockStates(self.last_state.get("state", LockStates.UNDEFINED.value))
        return currentState != LockStates.LOCKED or currentMode != LockModes.DOOR_MODE

    @property
    def extra_state_attributes(self):
        return {
            "timestamp": self.last_state.get("timestamp")
        }


class DoorState(NukiEntity, BinarySensorEntity):
    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("binary_sensor", "door_state")
        self.set_name("Door Open")
        self._attr_device_class = "door"

    @property
    def is_on(self) -> bool:
        current = DoorSensorStates(self.last_state.get(
            "doorsensorState", DoorSensorStates.UNKNOWN.value))
        return current != DoorSensorStates.DOOR_CLOSED


class BridgeServerConnection(NukiBridge, BinarySensorEntity):
    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.set_id("connected")
        self.set_name("Connected")
        self._attr_device_class = "connectivity"

    @property
    def is_on(self) -> bool:
        return self.data.get("serverConnected", False)

    @property
    def extra_state_attributes(self):
        versions = self.data.get("versions", {})
        return {
            "wifiFirmwareVersion": versions.get("wifiFirmwareVersion")
        }

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC


class BridgeCallbackSet(NukiBridge, BinarySensorEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.set_id("callback_set")
        self.set_name("Bridge Callback Set")

    @property
    def is_on(self) -> bool:
        return self.data.get("callbacks_list") != None

    @property
    def extra_state_attributes(self):
        result = {}
        callbacks = self.data.get("callbacks_list")
        if callbacks:
            for item in callbacks:
                result["callback#%s" % (item["id"])] = item["url"]
        return result

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC
