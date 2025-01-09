from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
from homeassistant.helpers.entity import EntityCategory

import logging

from . import NukiBridge
from .constants import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    entities = []
    coordinator = entry.runtime_data

    if coordinator.api.can_bridge():
        entities.append(NukiBridgeRestartButton(coordinator))
        entities.append(NukiBridgeFWUpdateButton(coordinator))
    async_add_entities(entities)
    return True

class NukiBridgeRestartButton(NukiBridge, ButtonEntity):
    """Defines a Bridge restart button."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.set_id("reboot")
        self.set_name("Reboot")
        self._attr_device_class = ButtonDeviceClass.RESTART
        self._attr_entity_category = EntityCategory.CONFIG

    async def async_press(self) -> None:
        await self.coordinator.do_reboot()

class NukiBridgeFWUpdateButton(NukiBridge, ButtonEntity):
    """Defines a Bridge update button."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self.set_id("fw_update")
        self.set_name("Firmware Update")
        self._attr_device_class = ButtonDeviceClass.UPDATE
        self._attr_entity_category = EntityCategory.CONFIG

    async def async_press(self) -> None:
        await self.coordinator.do_fwupdate()
