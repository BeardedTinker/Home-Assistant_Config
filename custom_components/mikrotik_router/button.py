"""Support for the Mikrotik Router buttons."""

import logging
from homeassistant.components.button import ButtonEntity
from .model import model_async_setup_entry, MikrotikEntity
from .button_types import (
    SENSOR_TYPES,
    SENSOR_SERVICES,
)

_LOGGER = logging.getLogger(__name__)


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up entry for component"""
    dispatcher = {
        "MikrotikButton": MikrotikButton,
        "MikrotikScriptButton": MikrotikScriptButton,
    }
    await model_async_setup_entry(
        hass,
        config_entry,
        async_add_entities,
        SENSOR_SERVICES,
        SENSOR_TYPES,
        dispatcher,
    )


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
        """Process the button press."""
        self._ctrl.run_script(self._data["name"])
        await self._ctrl.force_update()
