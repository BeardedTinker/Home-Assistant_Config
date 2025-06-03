"""Support for the Mikrotik Router buttons."""

from __future__ import annotations

from logging import getLogger

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .entity import MikrotikEntity, async_add_entities
from .button_types import (
    SENSOR_TYPES,
    SENSOR_SERVICES,
)
from .exceptions import ApiEntryNotFound

_LOGGER = getLogger(__name__)


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    _async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up entry for component"""
    dispatcher = {
        "MikrotikButton": MikrotikButton,
        "MikrotikScriptButton": MikrotikScriptButton,
    }
    await async_add_entities(hass, config_entry, dispatcher)


# ---------------------------
#   MikrotikButton
# ---------------------------
class MikrotikButton(MikrotikEntity, ButtonEntity):
    """Representation of a button."""

    async def async_update(self):
        """Synchronize state with controller."""

    async def async_press(self) -> None:
        pass


# ---------------------------
#   MikrotikScriptButton
# ---------------------------
class MikrotikScriptButton(MikrotikButton):
    """Representation of a script button."""

    async def async_press(self) -> None:
        """Run script using Mikrotik API"""
        try:
            self.coordinator.api.run_script(self._data["name"])
        except ApiEntryNotFound as error:
            _LOGGER.error("Failed to run script: %s", error)
