from homeassistant.components.lock import LockEntity, SUPPORT_OPEN

import logging

from . import NukiEntity
from .constants import DOMAIN
from .states import LockStates

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    entities = []
    coordinator = hass.data[DOMAIN][entry.entry_id]

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
        return SUPPORT_OPEN

    @property
    def lock_state(self):
        return self.last_state.get("state", 255)

    @property
    def is_locked(self):
        return LockStates(self.lock_state) == LockStates.LOCKED

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
        await self.coordinator.action(self.device_id, "lock")

    async def async_unlock(self, **kwargs):
        await self.coordinator.action(self.device_id, "unlock")

    async def async_open(self, **kwargs):
        await self.coordinator.action(self.device_id, "open")
