from homeassistant.components.button import ButtonEntity

import logging

from . import NukiBridge
from .constants import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    entities = []
    data = entry.as_dict()
    coordinator = hass.data[DOMAIN][entry.entry_id]

    if coordinator.api.can_bridge():
        entities.append(RebootBridge(coordinator))
        entities.append(FWUpdateBridge(coordinator))
    async_add_entities(entities)
    return True

class RebootBridge(NukiBridge, ButtonEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.set_id("reboot")
        self.set_name("Reboot")
        self._attr_device_class = "restart"
        self._attr_entity_category = "config"

    async def async_press(self) -> None:
        await self.coordinator.do_reboot()

class FWUpdateBridge(NukiBridge, ButtonEntity):

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.set_id("fw_update")
        self.set_name("Firmware Update")
        self._attr_device_class = "update"
        self._attr_entity_category = "config"

    async def async_press(self) -> None:
        await self.coordinator.do_fwupdate()
