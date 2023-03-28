from email.policy import default
from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import EntityCategory

import logging

from . import NukiEntity, NukiOpenerRingSuppressionEntity
from .constants import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass,
    entry,
    async_add_entities
):
    entities = []
    coordinator = hass.data[DOMAIN][entry.entry_id]

    for dev_id in coordinator.data.get("devices", {}):
        if coordinator.info_field(dev_id, -1, "openerAdvancedConfig", "doorbellSuppression")  >= 0:
            entities.append(NukiOpenerRingSuppressionSelect(coordinator, dev_id))
    async_add_entities(entities)
    return True


class NukiOpenerRingSuppressionSelect(NukiOpenerRingSuppressionEntity, SelectEntity):

    SUP_OFF = 0
    SUP_RING = NukiOpenerRingSuppressionEntity.SUP_RING
    SUP_RTO = NukiOpenerRingSuppressionEntity.SUP_RTO
    SUP_CM = NukiOpenerRingSuppressionEntity.SUP_CM

    VALUES_TO_NAMES = {
      # 0
      SUP_OFF: 'Off',
      # 4
      SUP_RING: 'Ring',
      # 2
      SUP_RTO: 'Ring to Open',
      # 1
      SUP_CM: 'Continuous Mode',
      # 4 + 2 == 6
      SUP_RING | SUP_RTO: 'Ring & Ring to Open',
      # 4 + 1 == 5
      SUP_RING | SUP_CM: 'Ring & Continuous Mode',
      # 2 + 1 == 3
      SUP_RTO | SUP_CM: 'Ring to Open & Continuous Mode',
      # 4 + 2 + 1 == 7
      SUP_RING | SUP_RTO | SUP_CM: 'On (suppress all)',
    }
    NAMES_TO_VALUES = {v: k for k, v in VALUES_TO_NAMES.items()}

    def __init__(self, coordinator, device_id):
        super().__init__(coordinator, device_id)
        self.set_id("select", "ring_suppression")
        self.set_name("Ring suppression")
        self._attr_icon = "mdi:bell-cancel"

    @property
    def current_option(self) -> str | None:
        return self.VALUES_TO_NAMES[self.doorbellSuppression]

    @property
    def options(self) -> list[str]:
        return list(self.NAMES_TO_VALUES.keys())

    async def async_select_option(self, option: str) -> None:
        await self.update_doorbell_suppression(self.NAMES_TO_VALUES[option])
