"""Support for the Mikrotik Router switches."""

import logging
from typing import Any, Optional
from collections.abc import Mapping
from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_NAME, CONF_HOST, ATTR_ATTRIBUTION
from homeassistant.core import callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.restore_state import RestoreEntity
from .helper import format_attribute
from .const import DOMAIN, ATTRIBUTION
from .switch_types import (
    MikrotikSwitchEntityDescription,
    SWITCH_TYPES,
    DEVICE_ATTRIBUTES_IFACE_ETHER,
    DEVICE_ATTRIBUTES_IFACE_SFP,
)

_LOGGER = logging.getLogger(__name__)


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up switches for Mikrotik Router component."""
    inst = config_entry.data[CONF_NAME]
    mikrotik_controller = hass.data[DOMAIN][config_entry.entry_id]
    switches = {}

    @callback
    def update_controller():
        """Update the values of the controller."""
        update_items(inst, mikrotik_controller, async_add_entities, switches)

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
def update_items(inst, mikrotik_controller, async_add_entities, switches):
    """Update device switch state from the controller."""
    new_switches = []

    # Add switches
    for switch, sid_func in zip(
        # Switch type name
        [
            "interface",
            "nat",
            "mangle",
            "filter",
            "ppp_secret",
            "queue",
            "kidcontrol_enable",
            "kidcontrol_pause",
        ],
        # Entity function
        [
            MikrotikControllerPortSwitch,
            MikrotikControllerNATSwitch,
            MikrotikControllerMangleSwitch,
            MikrotikControllerFilterSwitch,
            MikrotikControllerSwitch,
            MikrotikControllerQueueSwitch,
            MikrotikControllerSwitch,
            MikrotikControllerKidcontrolPauseSwitch,
        ],
    ):
        uid_switch = SWITCH_TYPES[switch]
        for uid in mikrotik_controller.data[SWITCH_TYPES[switch].data_path]:
            uid_data = mikrotik_controller.data[SWITCH_TYPES[switch].data_path]
            item_id = f"{inst}-{switch}-{uid_data[uid][uid_switch.data_reference]}"
            _LOGGER.debug("Updating sensor %s", item_id)
            if item_id in switches:
                if switches[item_id].enabled:
                    switches[item_id].async_schedule_update_ha_state()
                continue

            switches[item_id] = sid_func(
                inst=inst,
                uid=uid,
                mikrotik_controller=mikrotik_controller,
                entity_description=uid_switch,
            )
            new_switches.append(switches[item_id])

    if new_switches:
        async_add_entities(new_switches)


# ---------------------------
#   MikrotikControllerSwitch
# ---------------------------
class MikrotikControllerSwitch(SwitchEntity, RestoreEntity):
    """Representation of a switch."""

    def __init__(
        self,
        inst,
        uid,
        mikrotik_controller,
        entity_description: MikrotikSwitchEntityDescription,
    ):
        self.entity_description = entity_description
        self._inst = inst
        self._ctrl = mikrotik_controller
        self._attr_extra_state_attributes = {ATTR_ATTRIBUTION: ATTRIBUTION}
        self._data = mikrotik_controller.data[self.entity_description.data_path][uid]

    @property
    def available(self) -> bool:
        """Return if controller is available."""
        return self._ctrl.connected()

    @property
    def name(self) -> str:
        """Return the name."""
        if self.entity_description.data_name_comment and self._data["comment"]:
            return (
                f"{self._inst} {self.entity_description.name} {self._data['comment']}"
            )

        return f"{self._inst} {self.entity_description.name} {self._data[self.entity_description.data_name]}"

    @property
    def unique_id(self) -> str:
        """Return a unique id for this entity."""
        return f"{self._inst.lower()}-{self.entity_description.key}-{self._data[self.entity_description.data_reference].lower()}"

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._data[self.entity_description.data_is_on]

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self._data[self.entity_description.data_is_on]:
            return self.entity_description.icon_enabled
        else:
            return self.entity_description.icon_disabled

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        attributes = super().extra_state_attributes
        for variable in self.entity_description.data_attributes_list:
            if variable in self._data:
                attributes[format_attribute(variable)] = self._data[variable]

        return attributes

    def turn_on(self, **kwargs: Any) -> None:
        """Required abstract method."""
        pass

    def turn_off(self, **kwargs: Any) -> None:
        """Required abstract method."""
        pass

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        path = self.entity_description.data_switch_path
        param = self.entity_description.data_reference
        value = self._data[self.entity_description.data_reference]
        mod_param = self.entity_description.data_switch_parameter
        self._ctrl.set_value(path, param, value, mod_param, False)
        await self._ctrl.force_update()

    async def async_turn_off(self) -> None:
        """Turn off the switch."""
        path = self.entity_description.data_switch_path
        param = self.entity_description.data_reference
        value = self._data[self.entity_description.data_reference]
        mod_param = self.entity_description.data_switch_parameter
        self._ctrl.set_value(path, param, value, mod_param, True)
        await self._ctrl.async_update()

    @property
    def device_info(self) -> DeviceInfo:
        """Return a description for device registry."""
        dev_connection = DOMAIN
        dev_connection_value = self.entity_description.data_reference
        dev_group = self.entity_description.ha_group
        if self.entity_description.ha_group.startswith("data__"):
            dev_group = self.entity_description.ha_group[6:]
            if dev_group in self._data:
                dev_group = self._data[dev_group]
                dev_connection_value = dev_group

        if self.entity_description.ha_connection:
            dev_connection = self.entity_description.ha_connection

        if self.entity_description.ha_connection_value:
            dev_connection_value = self.entity_description.ha_connection_value
            if dev_connection_value.startswith("data__"):
                dev_connection_value = dev_connection_value[6:]
                dev_connection_value = self._data[dev_connection_value]

        info = DeviceInfo(
            connections={(dev_connection, f"{dev_connection_value}")},
            identifiers={(dev_connection, f"{dev_connection_value}")},
            default_name=f"{self._inst} {dev_group}",
            model=f"{self._ctrl.data['resource']['board-name']}",
            manufacturer=f"{self._ctrl.data['resource']['platform']}",
            sw_version=f"{self._ctrl.data['resource']['version']}",
            configuration_url=f"http://{self._ctrl.config_entry.data[CONF_HOST]}",
            via_device=(DOMAIN, f"{self._ctrl.data['routerboard']['serial-number']}"),
        )

        return info

    async def async_added_to_hass(self):
        """Run when entity about to be added to hass."""
        _LOGGER.debug("New switch %s (%s)", self._inst, self.unique_id)


# ---------------------------
#   MikrotikControllerPortSwitch
# ---------------------------
class MikrotikControllerPortSwitch(MikrotikControllerSwitch):
    """Representation of a network port switch."""

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return the state attributes."""
        attributes = super().extra_state_attributes

        if self._data["type"] == "ether":
            for variable in DEVICE_ATTRIBUTES_IFACE_ETHER:
                if variable in self._data:
                    attributes[format_attribute(variable)] = self._data[variable]

            if "sfp-shutdown-temperature" in self._data:
                for variable in DEVICE_ATTRIBUTES_IFACE_SFP:
                    if variable in self._data:
                        attributes[format_attribute(variable)] = self._data[variable]

        return attributes

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self._data["running"]:
            icon = self.entity_description.icon_enabled
        else:
            icon = self.entity_description.icon_disabled

        if not self._data["enabled"]:
            icon = "mdi:lan-disconnect"

        return icon

    async def async_turn_on(self) -> Optional[str]:
        """Turn on the switch."""
        path = self.entity_description.data_switch_path
        param = self.entity_description.data_reference
        if self._data["about"] == "managed by CAPsMAN":
            _LOGGER.error("Unable to enable %s, managed by CAPsMAN", self._data[param])
            return "managed by CAPsMAN"
        if "-" in self._data["port-mac-address"]:
            param = "name"
        value = self._data[self.entity_description.data_reference]
        mod_param = self.entity_description.data_switch_parameter
        self._ctrl.set_value(path, param, value, mod_param, False)

        if "poe-out" in self._data and self._data["poe-out"] == "off":
            path = "/interface/ethernet"
            self._ctrl.set_value(path, param, value, "poe-out", "auto-on")

        await self._ctrl.force_update()

    async def async_turn_off(self) -> Optional[str]:
        """Turn off the switch."""
        path = self.entity_description.data_switch_path
        param = self.entity_description.data_reference
        if self._data["about"] == "managed by CAPsMAN":
            _LOGGER.error("Unable to disable %s, managed by CAPsMAN", self._data[param])
            return "managed by CAPsMAN"
        if "-" in self._data["port-mac-address"]:
            param = "name"
        value = self._data[self.entity_description.data_reference]
        mod_param = self.entity_description.data_switch_parameter
        self._ctrl.set_value(path, param, value, mod_param, True)

        if "poe-out" in self._data and self._data["poe-out"] == "auto-on":
            path = "/interface/ethernet"
            self._ctrl.set_value(path, param, value, "poe-out", "off")

        await self._ctrl.async_update()


# ---------------------------
#   MikrotikControllerNATSwitch
# ---------------------------
class MikrotikControllerNATSwitch(MikrotikControllerSwitch):
    """Representation of a NAT switch."""

    @property
    def name(self) -> str:
        """Return the name."""
        if self._data["comment"]:
            return f"{self._inst} NAT {self._data['comment']}"

        return f"{self._inst} NAT {self._data['name']}"

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        path = self.entity_description.data_switch_path
        param = ".id"
        value = None
        for uid in self._ctrl.data["nat"]:
            if self._ctrl.data["nat"][uid]["uniq-id"] == (
                f"{self._data['chain']},{self._data['action']},{self._data['protocol']},"
                f"{self._data['in-interface']}:{self._data['dst-port']}-"
                f"{self._data['out-interface']}:{self._data['to-addresses']}:{self._data['to-ports']}"
            ):
                value = self._ctrl.data["nat"][uid][".id"]

        mod_param = self.entity_description.data_switch_parameter
        self._ctrl.set_value(path, param, value, mod_param, False)
        await self._ctrl.force_update()

    async def async_turn_off(self) -> None:
        """Turn off the switch."""
        path = self.entity_description.data_switch_path
        param = ".id"
        value = None
        for uid in self._ctrl.data["nat"]:
            if self._ctrl.data["nat"][uid]["uniq-id"] == (
                f"{self._data['chain']},{self._data['action']},{self._data['protocol']},"
                f"{self._data['in-interface']}:{self._data['dst-port']}-"
                f"{self._data['out-interface']}:{self._data['to-addresses']}:{self._data['to-ports']}"
            ):
                value = self._ctrl.data["nat"][uid][".id"]

        mod_param = self.entity_description.data_switch_parameter
        self._ctrl.set_value(path, param, value, mod_param, True)
        await self._ctrl.async_update()


# ---------------------------
#   MikrotikControllerMangleSwitch
# ---------------------------
class MikrotikControllerMangleSwitch(MikrotikControllerSwitch):
    """Representation of a Mangle switch."""

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        path = self.entity_description.data_switch_path
        param = ".id"
        value = None
        for uid in self._ctrl.data["mangle"]:
            if self._ctrl.data["mangle"][uid]["uniq-id"] == (
                f"{self._data['chain']},{self._data['action']},{self._data['protocol']},"
                f"{self._data['src-address']}:{self._data['src-port']}-"
                f"{self._data['dst-address']}:{self._data['dst-port']},"
                f"{self._data['src-address-list']}-{self._data['dst-address-list']}"
            ):
                value = self._ctrl.data["mangle"][uid][".id"]

        mod_param = self.entity_description.data_switch_parameter
        self._ctrl.set_value(path, param, value, mod_param, False)
        await self._ctrl.force_update()

    async def async_turn_off(self) -> None:
        """Turn off the switch."""
        path = self.entity_description.data_switch_path
        param = ".id"
        value = None
        for uid in self._ctrl.data["mangle"]:
            if self._ctrl.data["mangle"][uid]["uniq-id"] == (
                f"{self._data['chain']},{self._data['action']},{self._data['protocol']},"
                f"{self._data['src-address']}:{self._data['src-port']}-"
                f"{self._data['dst-address']}:{self._data['dst-port']},"
                f"{self._data['src-address-list']}-{self._data['dst-address-list']}"
            ):
                value = self._ctrl.data["mangle"][uid][".id"]

        mod_param = self.entity_description.data_switch_parameter
        self._ctrl.set_value(path, param, value, mod_param, True)
        await self._ctrl.async_update()


# ---------------------------
#   MikrotikControllerFilterSwitch
# ---------------------------
class MikrotikControllerFilterSwitch(MikrotikControllerSwitch):
    """Representation of a Filter switch."""

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        path = self.entity_description.data_switch_path
        param = ".id"
        value = None
        for uid in self._ctrl.data["filter"]:
            if self._ctrl.data["filter"][uid]["uniq-id"] == (
                f"{self._data['chain']},{self._data['action']},{self._data['protocol']},{self._data['layer7-protocol']},"
                f"{self._data['in-interface']},{self._data['in-interface-list']}:{self._data['src-address']},{self._data['src-address-list']}:{self._data['src-port']}-"
                f"{self._data['out-interface']},{self._data['out-interface-list']}:{self._data['dst-address']},{self._data['dst-address-list']}:{self._data['dst-port']}"
            ):
                value = self._ctrl.data["filter"][uid][".id"]

        mod_param = self.entity_description.data_switch_parameter
        self._ctrl.set_value(path, param, value, mod_param, False)
        await self._ctrl.force_update()

    async def async_turn_off(self) -> None:
        """Turn off the switch."""
        path = self.entity_description.data_switch_path
        param = ".id"
        value = None
        for uid in self._ctrl.data["filter"]:
            if self._ctrl.data["filter"][uid]["uniq-id"] == (
                f"{self._data['chain']},{self._data['action']},{self._data['protocol']},{self._data['layer7-protocol']},"
                f"{self._data['in-interface']},{self._data['in-interface-list']}:{self._data['src-address']},{self._data['src-address-list']}:{self._data['src-port']}-"
                f"{self._data['out-interface']},{self._data['out-interface-list']}:{self._data['dst-address']},{self._data['dst-address-list']}:{self._data['dst-port']}"
            ):
                value = self._ctrl.data["filter"][uid][".id"]

        mod_param = self.entity_description.data_switch_parameter
        self._ctrl.set_value(path, param, value, mod_param, True)
        await self._ctrl.async_update()


# ---------------------------
#   MikrotikControllerQueueSwitch
# ---------------------------
class MikrotikControllerQueueSwitch(MikrotikControllerSwitch):
    """Representation of a queue switch."""

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        path = self.entity_description.data_switch_path
        param = ".id"
        value = None
        for uid in self._ctrl.data["queue"]:
            if self._ctrl.data["queue"][uid]["name"] == f"{self._data['name']}":
                value = self._ctrl.data["queue"][uid][".id"]

        mod_param = self.entity_description.data_switch_parameter
        self._ctrl.set_value(path, param, value, mod_param, False)
        await self._ctrl.force_update()

    async def async_turn_off(self) -> None:
        """Turn off the switch."""
        path = self.entity_description.data_switch_path
        param = ".id"
        value = None
        for uid in self._ctrl.data["queue"]:
            if self._ctrl.data["queue"][uid]["name"] == f"{self._data['name']}":
                value = self._ctrl.data["queue"][uid][".id"]

        mod_param = self.entity_description.data_switch_parameter
        self._ctrl.set_value(path, param, value, mod_param, True)
        await self._ctrl.async_update()


# ---------------------------
#   MikrotikControllerKidcontrolPauseSwitch
# ---------------------------
class MikrotikControllerKidcontrolPauseSwitch(MikrotikControllerSwitch):
    """Representation of a queue switch."""

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        path = self.entity_description.data_switch_path
        param = self.entity_description.data_reference
        value = self._data[self.entity_description.data_reference]
        command = "resume"
        self._ctrl.execute(path, command, param, value)
        await self._ctrl.force_update()

    async def async_turn_off(self) -> None:
        """Turn off the switch."""
        path = self.entity_description.data_switch_path
        param = self.entity_description.data_reference
        value = self._data[self.entity_description.data_reference]
        command = "pause"
        self._ctrl.execute(path, command, param, value)
        await self._ctrl.async_update()
