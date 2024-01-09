from email.policy import default
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory

import logging

from . import NukiEntity, NukiOpenerRingSuppressionEntity
from .constants import DOMAIN
from .states import LockModes

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass,
    entry,
    async_add_entities
):
    entities = []
    data = entry.as_dict()
    coordinator = hass.data[DOMAIN][entry.entry_id]

    for dev_id in coordinator.data.get("devices", {}):
        for auth_id in coordinator.device_data(dev_id).get("web_auth", {}):
            entities.append(AuthEntry(coordinator, dev_id, auth_id))
        if coordinator.info_field(dev_id, None, "advancedConfig", "autoLock") != None:
            entities.append(LockAutoLock(coordinator, dev_id))
        if coordinator.info_field(dev_id, -1, "openerAdvancedConfig", "doorbellSuppression")  >= 0:
            entities.append(OpenerRingSuppression(coordinator, dev_id))
            entities.append(OpenerRingSuppressionRTO(coordinator, dev_id))
            entities.append(OpenerRingSuppressionCM(coordinator, dev_id))
        if coordinator.is_opener(dev_id):
            entities.append(OpenerContinuousMode(coordinator, dev_id))
    async_add_entities(entities)
    return True


class AuthEntry(NukiEntity, SwitchEntity):

    def __init__(self, coordinator, device_id, auth_id):
        super().__init__(coordinator, device_id)
        self.auth_id = auth_id
        self.set_id("switch", f"{auth_id}_auth_entry")

    @property
    def name_suffix(self):
        name = self.auth_data.get("name", "undefined")
        return f"authorization: {name}"

    @property
    def auth_data(self):
        return self.data.get("web_auth", {}).get(self.auth_id, {})

    @property
    def is_on(self):
        return self.auth_data.get("enabled") == True

    @property
    def icon(self):
        mapping = {
            0: "mdi:devices",
            1: "mdi:network",
            2: "mdi:remote",
            3: "mdi:focus-field",
            13: "mdi:form-textbox-password"
        }
        return mapping.get(self.auth_data.get("type", -1), "mdi:account-question")

    @property
    def available(self):
        if "id" not in self.auth_data:
            return False
        return super().available

    async def async_turn_on(self, **kwargs):
        await self.coordinator.update_web_auth(self.device_id, self.auth_data, dict(enabled=True))

    async def async_turn_off(self, **kwargs):
        await self.coordinator.update_web_auth(self.device_id, self.auth_data, dict(enabled=False))

    @property
    def extra_state_attributes(self):
        return {
            "Remote allowed": self.auth_data.get("remoteAllowed"),
            "Lock count": self.auth_data.get("lockCount"),
            "Last active date": self.auth_data.get("lastActiveDate")
        }

    @property
    def device_info(self):
        return {
            "identifiers": {("web_id", self.device_id)},
            "name": "Nuki Web API",
            "manufacturer": "Nuki",
            "via_device": ("id", self.device_id)
        }

    @property
    def entity_category(self):
        return EntityCategory.CONFIG

class LockAutoLock(NukiEntity, SwitchEntity):

    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("switch", "auto_lock")
        self.set_name("Auto lock")
        self._attr_icon = "mdi:lock-clock"

    @property
    def is_on(self):
        return self.coordinator.info_field(self.device_id, False, "advancedConfig", "autoLock")

    @property
    def entity_category(self):
        return EntityCategory.CONFIG

    async def async_turn_on(self, **kwargs):
        await self.coordinator.update_config(self.device_id, "advancedConfig", dict(autoLock=True))

    async def async_turn_off(self, **kwargs):
        await self.coordinator.update_config(self.device_id, "advancedConfig", dict(autoLock=False))


class OpenerRingSuppressionSwitch(NukiOpenerRingSuppressionEntity, SwitchEntity):
    
    def __init__(self, coordinator, device_id, suppression):
        super().__init__(coordinator, device_id)
        self._suppression = suppression
    
    @property
    def entity_registry_enabled_default(self):
        return False

    @property
    def is_on(self):
        return (self.doorbellSuppression & self._suppression) != 0

    async def async_turn_on(self, **kwargs):
        await self.update_doorbell_suppression(self.doorbellSuppression | self._suppression)

    async def async_turn_off(self, **kwargs):
        await self.update_doorbell_suppression(self.doorbellSuppression & (~self._suppression))


class OpenerRingSuppression(OpenerRingSuppressionSwitch):

    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id, NukiOpenerRingSuppressionEntity.SUP_RING)
        self.set_id("switch", "ring_suppression")
        self.set_name("Ring suppression")
        self._attr_icon = "mdi:bell-cancel"


class OpenerRingSuppressionRTO(OpenerRingSuppressionSwitch):

    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id, NukiOpenerRingSuppressionEntity.SUP_RTO)
        self.set_id("switch", "ring_suppression_rto")
        self.set_name("Ring suppression (Ring to Open)")
        self._attr_icon = "mdi:bell-cancel"


class OpenerRingSuppressionCM(OpenerRingSuppressionSwitch):

    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id, NukiOpenerRingSuppressionEntity.SUP_CM)
        self.set_id("switch", "ring_suppression_cm")
        self.set_name("Ring suppression (Continuous Mode)")
        self._attr_icon = "mdi:bell-cancel"


class OpenerContinuousMode(NukiEntity, SwitchEntity):

    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("switch", "continuous_mode")
        self.set_name("Continuous Mode")

    @property
    def icon(self) -> str | None:
        return "mdi:lock-open-check" if self.is_on else "mdi:lock-check"

    @property
    def is_on(self):
        return LockModes(self.last_state.get("mode", LockModes.DOOR_MODE.value)) == LockModes.CONTINUOUS_MODE

    @property
    def entity_category(self):
        return EntityCategory.CONFIG

    async def async_turn_on(self, **kwargs):
        await self.coordinator.action(self.device_id, "activate_continuous_mode")

    async def async_turn_off(self, **kwargs):
        await self.coordinator.action(self.device_id, "deactivate_continuous_mode")
