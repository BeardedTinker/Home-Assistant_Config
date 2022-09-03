"""Support for the Mikrotik Router switches."""

import logging
from typing import Any, Optional
from collections.abc import Mapping
from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.restore_state import RestoreEntity
from .helper import format_attribute
from .model import model_async_setup_entry, MikrotikEntity
from .switch_types import (
    SENSOR_TYPES,
    SENSOR_SERVICES,
    DEVICE_ATTRIBUTES_IFACE_ETHER,
    DEVICE_ATTRIBUTES_IFACE_SFP,
    DEVICE_ATTRIBUTES_IFACE_WIRELESS,
)

_LOGGER = logging.getLogger(__name__)


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up entry for component"""
    dispatcher = {
        "MikrotikSwitch": MikrotikSwitch,
        "MikrotikPortSwitch": MikrotikPortSwitch,
        "MikrotikNATSwitch": MikrotikNATSwitch,
        "MikrotikMangleSwitch": MikrotikMangleSwitch,
        "MikrotikFilterSwitch": MikrotikFilterSwitch,
        "MikrotikQueueSwitch": MikrotikQueueSwitch,
        "MikrotikKidcontrolPauseSwitch": MikrotikKidcontrolPauseSwitch,
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
#   MikrotikSwitch
# ---------------------------
class MikrotikSwitch(MikrotikEntity, SwitchEntity, RestoreEntity):
    """Representation of a switch."""

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._data[self.entity_description.data_attribute]

    @property
    def icon(self) -> str:
        """Return the icon."""
        if self._data[self.entity_description.data_attribute]:
            return self.entity_description.icon_enabled
        else:
            return self.entity_description.icon_disabled

    def turn_on(self, **kwargs: Any) -> None:
        """Required abstract method."""
        pass

    def turn_off(self, **kwargs: Any) -> None:
        """Required abstract method."""
        pass

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        if "write" not in self._ctrl.data["access"]:
            return

        path = self.entity_description.data_switch_path
        param = self.entity_description.data_reference
        value = self._data[self.entity_description.data_reference]
        mod_param = self.entity_description.data_switch_parameter
        self._ctrl.set_value(path, param, value, mod_param, False)
        await self._ctrl.force_update()

    async def async_turn_off(self) -> None:
        """Turn off the switch."""
        if "write" not in self._ctrl.data["access"]:
            return

        path = self.entity_description.data_switch_path
        param = self.entity_description.data_reference
        value = self._data[self.entity_description.data_reference]
        mod_param = self.entity_description.data_switch_parameter
        self._ctrl.set_value(path, param, value, mod_param, True)
        await self._ctrl.async_update()


# ---------------------------
#   MikrotikPortSwitch
# ---------------------------
class MikrotikPortSwitch(MikrotikSwitch):
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

        elif self._data["type"] == "wlan":
            for variable in DEVICE_ATTRIBUTES_IFACE_WIRELESS:
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
        if "write" not in self._ctrl.data["access"]:
            return

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
        if "write" not in self._ctrl.data["access"]:
            return

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
#   MikrotikNATSwitch
# ---------------------------
class MikrotikNATSwitch(MikrotikSwitch):
    """Representation of a NAT switch."""

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        if "write" not in self._ctrl.data["access"]:
            return

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
        if "write" not in self._ctrl.data["access"]:
            return

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
#   MikrotikMangleSwitch
# ---------------------------
class MikrotikMangleSwitch(MikrotikSwitch):
    """Representation of a Mangle switch."""

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        if "write" not in self._ctrl.data["access"]:
            return

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
        if "write" not in self._ctrl.data["access"]:
            return

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
#   MikrotikFilterSwitch
# ---------------------------
class MikrotikFilterSwitch(MikrotikSwitch):
    """Representation of a Filter switch."""

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        if "write" not in self._ctrl.data["access"]:
            return

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
        if "write" not in self._ctrl.data["access"]:
            return

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
#   MikrotikQueueSwitch
# ---------------------------
class MikrotikQueueSwitch(MikrotikSwitch):
    """Representation of a queue switch."""

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        if "write" not in self._ctrl.data["access"]:
            return

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
        if "write" not in self._ctrl.data["access"]:
            return

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
#   MikrotikKidcontrolPauseSwitch
# ---------------------------
class MikrotikKidcontrolPauseSwitch(MikrotikSwitch):
    """Representation of a queue switch."""

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        if "write" not in self._ctrl.data["access"]:
            return

        path = self.entity_description.data_switch_path
        param = self.entity_description.data_reference
        value = self._data[self.entity_description.data_reference]
        command = "resume"
        self._ctrl.execute(path, command, param, value)
        await self._ctrl.force_update()

    async def async_turn_off(self) -> None:
        """Turn off the switch."""
        if "write" not in self._ctrl.data["access"]:
            return

        path = self.entity_description.data_switch_path
        param = self.entity_description.data_reference
        value = self._data[self.entity_description.data_reference]
        command = "pause"
        self._ctrl.execute(path, command, param, value)
        await self._ctrl.async_update()
