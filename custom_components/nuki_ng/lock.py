from homeassistant.components.lock import LockEntity, LockEntityFeature

import logging

from . import NukiEntity
from .constants import DOMAIN
from .states import LockStates, LockModes

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    entities = []
    coordinator = entry.runtime_data

    for dev_id in coordinator.data.get("devices", {}):
        entities.append(Lock(coordinator, dev_id))
    async_add_entities(entities)
    return True


class Lock(NukiEntity, LockEntity):
    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("lock", "lock")
        self.set_name("Lock")

    @property
    def supported_features(self):
        return LockEntityFeature.OPEN

    @property
    def lock_mode(self):
        return self.last_state.get("mode", LockModes.DOOR_MODE.value)

    @property
    def lock_state(self):
        return self.last_state.get("state", 255)

    @property
    def is_locked(self):
        return LockStates(self.lock_state) == LockStates.LOCKED and LockModes(self.lock_mode) == LockModes.DOOR_MODE

    @property
    def is_locking(self):
        return LockStates(self.lock_state) == LockStates.LOCKING

    @property
    def is_unlocking(self):
        return LockStates(self.lock_state) == LockStates.UNLOCKING

    @property
    def is_jammed(self):
        return LockStates(self.lock_state) == LockStates.MOTOR_BLOCKED

    async def async_lock(self, **kwargs):
        """Lock the opener also disable Continuos Mode"""
        if self.coordinator.is_opener(self.device_id) and LockModes(self.last_state.get("mode", LockModes.DOOR_MODE.value)) == LockModes.CONTINUOUS_MODE:
            await self.coordinator.action(self.device_id, "deactivate_continuous_mode")
        await self.coordinator.action(self.device_id, "lock")

    async def async_unlock(self, **kwargs):
        await self.coordinator.action(self.device_id, "unlock")

    async def async_open(self, **kwargs):
        await self.coordinator.action(self.device_id, "open")
