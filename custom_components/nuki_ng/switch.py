from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.entity import EntityCategory

import logging

from . import NukiEntity
from .constants import DOMAIN

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
