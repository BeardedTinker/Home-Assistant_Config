"""Support for the Mikrotik Router buttons."""

import logging
from typing import Any, Dict
from homeassistant.components.button import ButtonEntity
from homeassistant.const import CONF_NAME, ATTR_ATTRIBUTION
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.restore_state import RestoreEntity
from .helper import format_attribute
from .const import DOMAIN, ATTRIBUTION

_LOGGER = logging.getLogger(__name__)

DEVICE_ATTRIBUTES_SCRIPT = [
    "last-started",
    "run-count",
]


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up buttons for Mikrotik Router component."""
    inst = config_entry.data[CONF_NAME]
    mikrotik_controller = hass.data[DOMAIN][config_entry.entry_id]
    buttons = {}

    @callback
    def update_controller():
        """Update the values of the controller."""
        update_items(inst, mikrotik_controller, async_add_entities, buttons)

    mikrotik_controller.listeners.append(
        async_dispatcher_connect(
            hass, mikrotik_controller.signal_update, update_controller
        )
    )

    update_controller()


# ---------------------------
#   update_items
# ---------------------------
@callback
def update_items(inst, mikrotik_controller, async_add_entities, buttons):
    """Update device button state from the controller."""
    new_buttons = []

    # Add buttons
    for sid, sid_uid, sid_name, sid_ref, sid_attr, sid_func in zip(
        # Data point name
        [
            "script",
        ],
        # Data point unique id
        [
            "name",
        ],
        # Entry Name
        [
            "name",
        ],
        # Entry Unique id
        [
            "name",
        ],
        # Attr
        [
            DEVICE_ATTRIBUTES_SCRIPT,
        ],
        # Button function
        [
            MikrotikControllerScriptButton,
        ],
    ):
        for uid in mikrotik_controller.data[sid]:
            item_id = f"{inst}-{sid}-{mikrotik_controller.data[sid][uid][sid_uid]}"

            _LOGGER.debug("Updating button %s", item_id)
            if item_id in buttons:
                if buttons[item_id].enabled:
                    buttons[item_id].async_schedule_update_ha_state()
                continue

            # Create new entity
            sid_data = {
                "sid": sid,
                "sid_uid": sid_uid,
                "sid_name": sid_name,
                "sid_ref": sid_ref,
                "sid_attr": sid_attr,
            }
            buttons[item_id] = sid_func(inst, uid, mikrotik_controller, sid_data)
            new_buttons.append(buttons[item_id])

    if new_buttons:
        async_add_entities(new_buttons)


# ---------------------------
#   MikrotikControllerButton
# ---------------------------
class MikrotikControllerButton(ButtonEntity, RestoreEntity):
    """Representation of a button."""

    def __init__(self, inst, uid, mikrotik_controller, sid_data):
        """Initialize."""
        self._sid_data = sid_data
        self._inst = inst
        self._ctrl = mikrotik_controller
        self._data = mikrotik_controller.data[self._sid_data["sid"]][uid]

        self._attrs = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }

    async def async_added_to_hass(self):
        """Run when entity about to be added to hass."""
        _LOGGER.debug(
            "New button %s (%s %s)",
            self._inst,
            self._sid_data["sid"],
            self._data[self._sid_data["sid_uid"]],
        )

    async def async_update(self):
        """Synchronize state with controller."""

    @property
    def available(self) -> bool:
        """Return if controller is available."""
        return self._ctrl.connected()

    @property
    def name(self) -> str:
        """Return the name."""
        return f"{self._inst} {self._sid_data['sid']} {self._data[self._sid_data['sid_name']]}"

    @property
    def unique_id(self) -> str:
        """Return a unique id for this entity."""
        return f"{self._inst.lower()}-{self._sid_data['sid']}_button-{self._data[self._sid_data['sid_ref']]}"

    @property
    def extra_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        attributes = self._attrs

        for variable in self._sid_data["sid_attr"]:
            if variable in self._data:
                attributes[format_attribute(variable)] = self._data[variable]

        return attributes

    async def async_press(self) -> None:
        pass


# ---------------------------
#   MikrotikControllerScriptButton
# ---------------------------
class MikrotikControllerScriptButton(MikrotikControllerButton):
    """Representation of a script button."""

    def __init__(self, inst, uid, mikrotik_controller, sid_data):
        """Initialize."""
        super().__init__(inst, uid, mikrotik_controller, sid_data)

    @property
    def icon(self) -> str:
        """Return the icon."""
        return "mdi:script-text-outline"

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return a description for device registry."""
        info = {
            "identifiers": {
                (
                    DOMAIN,
                    "serial-number",
                    f"{self._ctrl.data['routerboard']['serial-number']}",
                    "button",
                    "Scripts",
                )
            },
            "manufacturer": self._ctrl.data["resource"]["platform"],
            "model": self._ctrl.data["resource"]["board-name"],
            "name": f"{self._inst} Scripts",
        }
        return info

    async def async_press(self) -> None:
        """Process the button press."""
        self._ctrl.run_script(self._data["name"])
        await self._ctrl.force_update()
