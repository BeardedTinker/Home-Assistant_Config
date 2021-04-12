"""Support for the Mikrotik Router switches."""

import logging
from typing import Any, Dict, Optional

from homeassistant.components.switch import SwitchEntity
from homeassistant.const import CONF_NAME, ATTR_ATTRIBUTION
from homeassistant.core import callback
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN, DATA_CLIENT, ATTRIBUTION

_LOGGER = logging.getLogger(__name__)

DEVICE_ATTRIBUTES_IFACE = [
    "running",
    "enabled",
    "comment",
    "client-ip-address",
    "client-mac-address",
    "port-mac-address",
    "last-link-down-time",
    "last-link-up-time",
    "link-downs",
    "actual-mtu",
    "type",
    "name",
    "default-name",
    "poe-out",
]

DEVICE_ATTRIBUTES_IFACE_SFP = [
    "status",
    "auto-negotiation",
    "advertising",
    "link-partner-advertising",
    "sfp-temperature",
    "sfp-supply-voltage",
    "sfp-module-present",
    "sfp-tx-bias-current",
    "sfp-tx-power",
    "sfp-rx-power",
    "sfp-rx-loss",
    "sfp-tx-fault",
    "sfp-type",
    "sfp-connector-type",
    "sfp-vendor-name",
    "sfp-vendor-part-number",
    "sfp-vendor-revision",
    "sfp-vendor-serial",
    "sfp-manufacturing-date",
    "eeprom-checksum",
]

DEVICE_ATTRIBUTES_NAT = [
    "protocol",
    "dst-port",
    "in-interface",
    "to-addresses",
    "to-ports",
    "comment",
]

DEVICE_ATTRIBUTES_MANGLE = [
    "chain",
    "action",
    "passthrough",
    "protocol",
    "src-address",
    "src-port",
    "dst-address",
    "dst-port",
    "comment",
]

DEVICE_ATTRIBUTES_FILTER = [
    "chain",
    "action",
    "address-list",
    "protocol",
    "layer7-protocol",
    "tcp-flags",
    "connection-state",
    "in-interface",
    "src-address",
    "src-port",
    "out-interface",
    "dst-address",
    "dst-port",
    "comment",
]

DEVICE_ATTRIBUTES_PPP_SECRET = [
    "connected",
    "service",
    "profile",
    "comment",
    "caller-id",
    "encoding",
]

DEVICE_ATTRIBUTES_KIDCONTROL = [
    "rate-limit",
    "mon",
    "tue",
    "wed",
    "thu",
    "fri",
    "sat",
    "sun",
]

DEVICE_ATTRIBUTES_SCRIPT = [
    "last-started",
    "run-count",
]

DEVICE_ATTRIBUTES_QUEUE = [
    "target",
    "download-rate",
    "upload-rate",
    "download-max-limit",
    "upload-max-limit",
    "upload-limit-at",
    "download-limit-at",
    "upload-burst-limit",
    "download-burst-limit",
    "upload-burst-threshold",
    "download-burst-threshold",
    "upload-burst-time",
    "download-burst-time",
    "packet-marks",
    "parent",
    "comment",
]


# ---------------------------
#   format_attribute
# ---------------------------
def format_attribute(attr):
    res = attr.replace("-", " ")
    res = res.capitalize()
    res = res.replace(" ip ", " IP ")
    res = res.replace(" mac ", " MAC ")
    res = res.replace(" mtu", " MTU")
    res = res.replace("Sfp", "SFP")
    res = res.replace("Poe", "POE")
    res = res.replace(" tx", " TX")
    res = res.replace(" rx", " RX")
    return res


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up switches for Mikrotik Router component."""
    inst = config_entry.data[CONF_NAME]
    mikrotik_controller = hass.data[DOMAIN][DATA_CLIENT][config_entry.entry_id]
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
    for sid, sid_uid, sid_name, sid_ref, sid_attr, sid_func in zip(
        # Data point name
        [
            "interface",
            "nat",
            "mangle",
            "filter",
            "ppp_secret",
            "script",
            "queue",
            "kid-control",
        ],
        # Data point unique id
        ["name", "uniq-id", "uniq-id", "uniq-id", "name", "name", "name", "name"],
        # Entry Name
        ["name", "name", "name", "name", "name", "name", "name", "name"],
        # Entry Unique id
        [
            "port-mac-address",
            "uniq-id",
            "uniq-id",
            "uniq-id",
            "name",
            "name",
            "name",
            "name",
        ],
        # Attr
        [
            DEVICE_ATTRIBUTES_IFACE,
            DEVICE_ATTRIBUTES_NAT,
            DEVICE_ATTRIBUTES_MANGLE,
            DEVICE_ATTRIBUTES_FILTER,
            DEVICE_ATTRIBUTES_PPP_SECRET,
            DEVICE_ATTRIBUTES_SCRIPT,
            DEVICE_ATTRIBUTES_QUEUE,
            DEVICE_ATTRIBUTES_KIDCONTROL,
        ],
        # Switch function
        [
            MikrotikControllerPortSwitch,
            MikrotikControllerNATSwitch,
            MikrotikControllerMangleSwitch,
            MikrotikControllerFilterSwitch,
            MikrotikControllerPPPSecretSwitch,
            MikrotikControllerScriptSwitch,
            MikrotikControllerQueueSwitch,
            MikrotikControllerKidcontrolSwitch,
        ],
    ):
        for uid in mikrotik_controller.data[sid]:
            item_id = f"{inst}-{sid}-{mikrotik_controller.data[sid][uid][sid_uid]}"
            _LOGGER.debug("Updating switch %s", item_id)
            if item_id in switches:
                if switches[item_id].enabled:
                    switches[item_id].async_schedule_update_ha_state()
                continue

            # Create new entity
            sid_data = {
                "sid": sid,
                "sid_uid": sid_uid,
                "sid_name": sid_name,
                "sid_ref": sid_ref,
                "sid_attr": sid_attr,
            }
            switches[item_id] = sid_func(inst, uid, mikrotik_controller, sid_data)
            new_switches.append(switches[item_id])

    if new_switches:
        async_add_entities(new_switches)


# ---------------------------
#   MikrotikControllerSwitch
# ---------------------------
class MikrotikControllerSwitch(SwitchEntity, RestoreEntity):
    """Representation of a switch."""

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
            "New switch %s (%s %s)",
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
        return f"{self._inst.lower()}-{self._sid_data['sid']}_switch-{self._data[self._sid_data['sid_ref']]}"

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._data["enabled"]

    @property
    def device_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        attributes = self._attrs

        for variable in self._sid_data["sid_attr"]:
            if variable in self._data:
                attributes[format_attribute(variable)] = self._data[variable]

        return attributes

    def turn_off(self, **kwargs: Any) -> None:
        """Required abstract method."""
        pass

    def turn_on(self, **kwargs: Any) -> None:
        """Required abstract method."""
        pass


# ---------------------------
#   MikrotikControllerPortSwitch
# ---------------------------
class MikrotikControllerPortSwitch(MikrotikControllerSwitch):
    """Representation of a network port switch."""

    def __init__(self, inst, uid, mikrotik_controller, sid_data):
        """Initialize."""
        super().__init__(inst, uid, mikrotik_controller, sid_data)

    @property
    def name(self) -> str:
        """Return the name."""
        return f"{self._inst} port {self._data[self._sid_data['sid_name']]}"

    @property
    def unique_id(self) -> str:
        """Return a unique id for this entity."""
        return f"{self._inst.lower()}-enable_switch-{self._data['port-mac-address']}_{self._data['default-name']}"

    @property
    def device_state_attributes(self) -> Dict[str, Any]:
        """Return the state attributes."""
        attributes = self._attrs

        for variable in self._sid_data["sid_attr"]:
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
            icon = "mdi:lan-connect"
        else:
            icon = "mdi:lan-pending"

        if not self._data["enabled"]:
            icon = "mdi:lan-disconnect"

        return icon

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return a description for device registry."""
        info = {
            "connections": {(CONNECTION_NETWORK_MAC, self._data["port-mac-address"])},
            "manufacturer": self._ctrl.data["resource"]["platform"],
            "model": self._ctrl.data["resource"]["board-name"],
            "name": f"{self._inst} {self._data['default-name']}",
        }
        return info

    async def async_turn_on(self) -> Optional[str]:
        """Turn on the switch."""
        path = "/interface"
        param = "default-name"
        if self._data["about"] == "managed by CAPsMAN":
            _LOGGER.error("Unable to enable %s, managed by CAPsMAN", self._data[param])
            return "managed by CAPsMAN"
        if "-" in self._data["port-mac-address"]:
            param = "name"
        value = self._data[param]
        mod_param = "disabled"
        mod_value = False
        self._ctrl.set_value(path, param, value, mod_param, mod_value)

        if "poe-out" in self._data and self._data["poe-out"] == "off":
            path = "/interface/ethernet"
            self._ctrl.set_value(path, param, value, "poe-out", "auto-on")

        await self._ctrl.force_update()

    async def async_turn_off(self) -> Optional[str]:
        """Turn off the switch."""
        path = "/interface"
        param = "default-name"
        if self._data["about"] == "managed by CAPsMAN":
            _LOGGER.error("Unable to disable %s, managed by CAPsMAN", self._data[param])
            return "managed by CAPsMAN"
        if "-" in self._data["port-mac-address"]:
            param = "name"
        value = self._data[param]
        mod_param = "disabled"
        mod_value = True
        self._ctrl.set_value(path, param, value, mod_param, mod_value)

        if "poe-out" in self._data and self._data["poe-out"] == "auto-on":
            path = "/interface/ethernet"
            self._ctrl.set_value(path, param, value, "poe-out", "off")

        await self._ctrl.async_update()


# ---------------------------
#   MikrotikControllerNATSwitch
# ---------------------------
class MikrotikControllerNATSwitch(MikrotikControllerSwitch):
    """Representation of a NAT switch."""

    def __init__(self, inst, uid, mikrotik_controller, sid_data):
        """Initialize."""
        super().__init__(inst, uid, mikrotik_controller, sid_data)

    @property
    def name(self) -> str:
        """Return the name."""
        if self._data["comment"]:
            return f"{self._inst} NAT {self._data['comment']}"

        return f"{self._inst} NAT {self._data['name']}"

    @property
    def unique_id(self) -> str:
        """Return a unique id for this entity."""
        return f"{self._inst.lower()}-enable_nat-{self._data['uniq-id']}"

    @property
    def icon(self) -> str:
        """Return the icon."""
        if not self._data["enabled"]:
            icon = "mdi:network-off-outline"
        else:
            icon = "mdi:network-outline"

        return icon

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return a description for device registry."""
        info = {
            "identifiers": {
                (
                    DOMAIN,
                    "serial-number",
                    self._ctrl.data["routerboard"]["serial-number"],
                    "switch",
                    "NAT",
                )
            },
            "manufacturer": self._ctrl.data["resource"]["platform"],
            "model": self._ctrl.data["resource"]["board-name"],
            "name": f"{self._inst} NAT",
        }
        return info

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        path = "/ip/firewall/nat"
        param = ".id"
        value = None
        for uid in self._ctrl.data["nat"]:
            if self._ctrl.data["nat"][uid]["uniq-id"] == (
                f"{self._data['chain']},{self._data['action']},{self._data['protocol']},"
                f"{self._data['in-interface']}:{self._data['dst-port']}-"
                f"{self._data['out-interface']}:{self._data['to-addresses']}:{self._data['to-ports']}"
            ):
                value = self._ctrl.data["nat"][uid][".id"]

        mod_param = "disabled"
        mod_value = False
        self._ctrl.set_value(path, param, value, mod_param, mod_value)
        await self._ctrl.force_update()

    async def async_turn_off(self) -> None:
        """Turn off the switch."""
        path = "/ip/firewall/nat"
        param = ".id"
        value = None
        for uid in self._ctrl.data["nat"]:
            if self._ctrl.data["nat"][uid]["uniq-id"] == (
                f"{self._data['chain']},{self._data['action']},{self._data['protocol']},"
                f"{self._data['in-interface']}:{self._data['dst-port']}-"
                f"{self._data['out-interface']}:{self._data['to-addresses']}:{self._data['to-ports']}"
            ):
                value = self._ctrl.data["nat"][uid][".id"]

        mod_param = "disabled"
        mod_value = True
        self._ctrl.set_value(path, param, value, mod_param, mod_value)
        await self._ctrl.async_update()


# ---------------------------
#   MikrotikControllerMangleSwitch
# ---------------------------
class MikrotikControllerMangleSwitch(MikrotikControllerSwitch):
    """Representation of a Mangle switch."""

    def __init__(self, inst, uid, mikrotik_controller, sid_data):
        """Initialize."""
        super().__init__(inst, uid, mikrotik_controller, sid_data)

    @property
    def name(self) -> str:
        """Return the name."""
        if self._data["comment"]:
            return f"{self._inst} Mangle {self._data['comment']}"

        return f"{self._inst} Mangle {self._data['name']}"

    @property
    def unique_id(self) -> str:
        """Return a unique id for this entity."""
        return f"{self._inst.lower()}-enable_mangle-{self._data['uniq-id']}"

    @property
    def icon(self) -> str:
        """Return the icon."""
        if not self._data["enabled"]:
            icon = "mdi:bookmark-off-outline"
        else:
            icon = "mdi:bookmark-outline"

        return icon

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return a description for device registry."""
        info = {
            "identifiers": {
                (
                    DOMAIN,
                    "serial-number",
                    self._ctrl.data["routerboard"]["serial-number"],
                    "switch",
                    "Mangle",
                )
            },
            "manufacturer": self._ctrl.data["resource"]["platform"],
            "model": self._ctrl.data["resource"]["board-name"],
            "name": f"{self._inst} Mangle",
        }
        return info

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        path = "/ip/firewall/mangle"
        param = ".id"
        value = None
        for uid in self._ctrl.data["mangle"]:
            if self._ctrl.data["mangle"][uid]["uniq-id"] == (
                f"{self._data['chain']},{self._data['action']},{self._data['protocol']},"
                f"{self._data['src-address']}:{self._data['src-port']}-"
                f"{self._data['dst-address']}:{self._data['dst-port']}"
            ):
                value = self._ctrl.data["mangle"][uid][".id"]

        mod_param = "disabled"
        mod_value = False
        self._ctrl.set_value(path, param, value, mod_param, mod_value)
        await self._ctrl.force_update()

    async def async_turn_off(self) -> None:
        """Turn off the switch."""
        path = "/ip/firewall/mangle"
        param = ".id"
        value = None
        for uid in self._ctrl.data["mangle"]:
            if self._ctrl.data["mangle"][uid]["uniq-id"] == (
                f"{self._data['chain']},{self._data['action']},{self._data['protocol']},"
                f"{self._data['src-address']}:{self._data['src-port']}-"
                f"{self._data['dst-address']}:{self._data['dst-port']}"
            ):
                value = self._ctrl.data["mangle"][uid][".id"]

        mod_param = "disabled"
        mod_value = True
        self._ctrl.set_value(path, param, value, mod_param, mod_value)
        await self._ctrl.async_update()


# ---------------------------
#   MikrotikControllerFilterSwitch
# ---------------------------
class MikrotikControllerFilterSwitch(MikrotikControllerSwitch):
    """Representation of a Filter switch."""

    def __init__(self, inst, uid, mikrotik_controller, sid_data):
        """Initialize."""
        super().__init__(inst, uid, mikrotik_controller, sid_data)

    @property
    def name(self) -> str:
        """Return the name."""
        if self._data["comment"]:
            return f"{self._inst} Filter {self._data['comment']}"

        return f"{self._inst} Filter {self._data['name']}"

    @property
    def unique_id(self) -> str:
        """Return a unique id for this entity."""
        return f"{self._inst.lower()}-enable_filter-{self._data['uniq-id']}"

    @property
    def icon(self) -> str:
        """Return the icon."""
        if not self._data["enabled"]:
            icon = "mdi:filter-variant-remove"
        else:
            icon = "mdi:filter-variant"

        return icon

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return a description for device registry."""
        info = {
            "identifiers": {
                (
                    DOMAIN,
                    "serial-number",
                    self._ctrl.data["routerboard"]["serial-number"],
                    "switch",
                    "Filter",
                )
            },
            "manufacturer": self._ctrl.data["resource"]["platform"],
            "model": self._ctrl.data["resource"]["board-name"],
            "name": f"{self._inst} Filter",
        }
        return info

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        path = "/ip/firewall/filter"
        param = ".id"
        value = None
        for uid in self._ctrl.data["filter"]:
            if self._ctrl.data["filter"][uid]["uniq-id"] == (
                f"{self._data['chain']},{self._data['action']},{self._data['protocol']},{self._data['layer7-protocol']},"
                f"{self._data['in-interface']}:{self._data['src-address']}:{self._data['src-port']}-"
                f"{self._data['out-interface']}:{self._data['dst-address']}:{self._data['dst-port']}"
            ):
                value = self._ctrl.data["filter"][uid][".id"]

        mod_param = "disabled"
        mod_value = False
        self._ctrl.set_value(path, param, value, mod_param, mod_value)
        await self._ctrl.force_update()

    async def async_turn_off(self) -> None:
        """Turn off the switch."""
        path = "/ip/firewall/filter"
        param = ".id"
        value = None
        for uid in self._ctrl.data["filter"]:
            if self._ctrl.data["filter"][uid]["uniq-id"] == (
                f"{self._data['chain']},{self._data['action']},{self._data['protocol']},{self._data['layer7-protocol']},"
                f"{self._data['in-interface']}:{self._data['src-address']}:{self._data['src-port']}-"
                f"{self._data['out-interface']}:{self._data['dst-address']}:{self._data['dst-port']}"
            ):
                value = self._ctrl.data["filter"][uid][".id"]

        mod_param = "disabled"
        mod_value = True
        self._ctrl.set_value(path, param, value, mod_param, mod_value)
        await self._ctrl.async_update()


# ---------------------------
#   MikrotikControllerPPPSecretSwitch
# ---------------------------
class MikrotikControllerPPPSecretSwitch(MikrotikControllerSwitch):
    """Representation of a PPP Secret switch."""

    def __init__(self, inst, uid, mikrotik_controller, sid_data):
        """Initialize."""
        super().__init__(inst, uid, mikrotik_controller, sid_data)

    @property
    def name(self) -> str:
        """Return the name."""
        return f"{self._inst} PPP Secret {self._data['name']}"

    @property
    def unique_id(self) -> str:
        """Return a unique id for this entity."""
        return f"{self._inst.lower()}-enable_ppp_secret-{self._data['name']}"

    @property
    def icon(self) -> str:
        """Return the icon."""
        if not self._data["enabled"]:
            icon = "mdi:account-off-outline"
        else:
            icon = "mdi:account-outline"

        return icon

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return a description for device registry."""
        info = {
            "identifiers": {
                (
                    DOMAIN,
                    "serial-number",
                    self._ctrl.data["routerboard"]["serial-number"],
                    "switch",
                    "PPP",
                )
            },
            "manufacturer": self._ctrl.data["resource"]["platform"],
            "model": self._ctrl.data["resource"]["board-name"],
            "name": f"{self._inst} PPP",
        }
        return info

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        path = "/ppp/secret"
        param = "name"
        value = self._data["name"]
        mod_param = "disabled"
        mod_value = False
        self._ctrl.set_value(path, param, value, mod_param, mod_value)
        await self._ctrl.force_update()

    async def async_turn_off(self) -> None:
        """Turn off the switch."""
        path = "/ppp/secret"
        param = "name"
        value = self._data["name"]
        mod_param = "disabled"
        mod_value = True
        self._ctrl.set_value(path, param, value, mod_param, mod_value)
        await self._ctrl.async_update()


# ---------------------------
#   MikrotikControllerScriptSwitch
# ---------------------------
class MikrotikControllerScriptSwitch(MikrotikControllerSwitch):
    """Representation of a script switch."""

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
                    self._ctrl.data["routerboard"]["serial-number"],
                    "switch",
                    "Scripts",
                )
            },
            "manufacturer": self._ctrl.data["resource"]["platform"],
            "model": self._ctrl.data["resource"]["board-name"],
            "name": f"{self._inst} Scripts",
        }
        return info

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        self._ctrl.run_script(self._data["name"])
        await self._ctrl.force_update()

    async def async_turn_off(self) -> None:
        """Turn off the switch."""

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return False


# ---------------------------
#   MikrotikControllerQueueSwitch
# ---------------------------
class MikrotikControllerQueueSwitch(MikrotikControllerSwitch):
    """Representation of a queue switch."""

    def __init__(self, inst, uid, mikrotik_controller, sid_data):
        """Initialize."""
        super().__init__(inst, uid, mikrotik_controller, sid_data)

    @property
    def icon(self) -> str:
        """Return the icon."""
        if not self._data["enabled"]:
            icon = "mdi:leaf-off"
        else:
            icon = "mdi:leaf"

        return icon

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return a description for device registry."""
        info = {
            "identifiers": {
                (
                    DOMAIN,
                    "serial-number",
                    self._ctrl.data["routerboard"]["serial-number"],
                    "switch",
                    "Queue",
                )
            },
            "manufacturer": self._ctrl.data["resource"]["platform"],
            "model": self._ctrl.data["resource"]["board-name"],
            "name": f"{self._inst} Queue",
        }
        return info

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        path = "/queue/simple"
        param = ".id"
        value = None
        for uid in self._ctrl.data["queue"]:
            if self._ctrl.data["queue"][uid]["name"] == f"{self._data['name']}":
                value = self._ctrl.data["queue"][uid][".id"]

        mod_param = "disabled"
        mod_value = False
        self._ctrl.set_value(path, param, value, mod_param, mod_value)
        await self._ctrl.force_update()

    async def async_turn_off(self) -> None:
        """Turn off the switch."""
        path = "/queue/simple"
        param = ".id"
        value = None
        for uid in self._ctrl.data["queue"]:
            if self._ctrl.data["queue"][uid]["name"] == f"{self._data['name']}":
                value = self._ctrl.data["queue"][uid][".id"]

        mod_param = "disabled"
        mod_value = True
        self._ctrl.set_value(path, param, value, mod_param, mod_value)
        await self._ctrl.async_update()


# ---------------------------
#   MikrotikControllerKidcontrolSwitch
# ---------------------------
class MikrotikControllerKidcontrolSwitch(MikrotikControllerSwitch):
    """Representation of a queue switch."""

    def __init__(self, inst, uid, mikrotik_controller, sid_data):
        """Initialize."""
        super().__init__(inst, uid, mikrotik_controller, sid_data)

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._data["paused"]

    @property
    def icon(self) -> str:
        """Return the icon."""
        if not self._data["enabled"]:
            icon = "mdi:account-off-outline"
        else:
            icon = "mdi:account-outline"

        return icon

    @property
    def device_info(self) -> Dict[str, Any]:
        """Return a description for device registry."""
        info = {
            "identifiers": {
                (
                    DOMAIN,
                    "serial-number",
                    self._ctrl.data["routerboard"]["serial-number"],
                    "switch",
                    "Kidcontrol",
                )
            },
            "manufacturer": self._ctrl.data["resource"]["platform"],
            "model": self._ctrl.data["resource"]["board-name"],
            "name": f"{self._inst} Kidcontrol",
        }
        return info

    async def async_turn_on(self) -> None:
        """Turn on the switch."""
        path = "/ip/kid-control"
        param = "name"
        value = self._data["name"]
        command = "resume"
        self._ctrl.execute(path, command, param, value)
        await self._ctrl.force_update()

    async def async_turn_off(self) -> None:
        """Turn off the switch."""
        path = "/ip/kid-control"
        param = "name"
        value = self._data["name"]
        command = "pause"
        self._ctrl.execute(path, command, param, value)
        await self._ctrl.async_update()
