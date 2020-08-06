"""Support for the Mikrotik Router switches."""
import logging

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
]

DEVICE_ATTRIBUTES_NAT = [
    "protocol",
    "dst-port",
    "in-interface",
    "to-addresses",
    "to-ports",
    "comment",
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
        ["interface", "nat", "script", "queue"],
        # Data point unique id
        ["name", "name", "name", "name"],
        # Entry Name
        ["name", "name", "name", "name"],
        # Entry Unique id
        ["port-mac-address", "name", "name", "name"],
        # Attr
        [
            DEVICE_ATTRIBUTES_IFACE,
            DEVICE_ATTRIBUTES_NAT,
            DEVICE_ATTRIBUTES_SCRIPT,
            DEVICE_ATTRIBUTES_QUEUE,
        ],
        # Switch function
        [
            MikrotikControllerPortSwitch,
            MikrotikControllerNATSwitch,
            MikrotikControllerScriptSwitch,
            MikrotikControllerQueueSwitch,
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
        """Set up switch."""
        self._sid_data = sid_data
        self._inst = inst
        self._ctrl = mikrotik_controller
        self._data = mikrotik_controller.data[self._sid_data["sid"]][uid]

        self._attrs = {
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }

    async def async_added_to_hass(self):
        """Device tracker entity created."""
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
        """Return the name of the port."""
        return f"{self._inst} {self._sid_data['sid']} {self._data[self._sid_data['sid_name']]}"

    @property
    def unique_id(self) -> str:
        """Return a unique identifier for this port."""
        return f"{self._inst.lower()}-{self._sid_data['sid']}_switch-{self._data[self._sid_data['sid_ref']]}"

    @property
    def is_on(self):
        """Return true if the queue is on."""
        return self._data["enabled"]

    @property
    def device_state_attributes(self):
        """Return the port state attributes."""
        attributes = self._attrs

        for variable in self._sid_data["sid_attr"]:
            if variable in self._data:
                attributes[format_attribute(variable)] = self._data[variable]

        return attributes


# ---------------------------
#   MikrotikControllerPortSwitch
# ---------------------------
class MikrotikControllerPortSwitch(MikrotikControllerSwitch):
    """Representation of a network port switch."""

    def __init__(self, inst, uid, mikrotik_controller, sid_data):
        """Set up tracked port."""
        super().__init__(inst, uid, mikrotik_controller, sid_data)

    @property
    def name(self) -> str:
        """Return the name of the port."""
        return f"{self._inst} port {self._data[self._sid_data['sid_name']]}"

    @property
    def unique_id(self) -> str:
        """Return a unique identifier for this port."""
        return f"{self._inst.lower()}-enable_switch-{self._data['port-mac-address']}"

    @property
    def icon(self):
        """Return the icon."""
        if self._data["running"]:
            icon = "mdi:lan-connect"
        else:
            icon = "mdi:lan-pending"

        if not self._data["enabled"]:
            icon = "mdi:lan-disconnect"

        return icon

    @property
    def device_info(self):
        """Return a port description for device registry."""
        info = {
            "connections": {(CONNECTION_NETWORK_MAC, self._data["port-mac-address"])},
            "manufacturer": self._ctrl.data["resource"]["platform"],
            "model": self._ctrl.data["resource"]["board-name"],
            "name": f"{self._inst} {self._data['default-name']}",
        }
        return info

    async def async_turn_on(self):
        """Turn on the switch."""
        path = "/interface"
        param = "default-name"
        if "-" in self._data["port-mac-address"]:
            param = "name"
        value = self._data[param]
        mod_param = "disabled"
        mod_value = False
        self._ctrl.set_value(path, param, value, mod_param, mod_value)
        await self._ctrl.force_update()

    async def async_turn_off(self):
        """Turn on the switch."""
        path = "/interface"
        param = "default-name"
        if "-" in self._data["port-mac-address"]:
            param = "name"
        value = self._data[param]
        mod_param = "disabled"
        mod_value = True
        self._ctrl.set_value(path, param, value, mod_param, mod_value)
        await self._ctrl.async_update()


# ---------------------------
#   MikrotikControllerNATSwitch
# ---------------------------
class MikrotikControllerNATSwitch(MikrotikControllerSwitch):
    """Representation of a NAT switch."""

    def __init__(self, inst, uid, mikrotik_controller, sid_data):
        """Set up NAT switch."""
        super().__init__(inst, uid, mikrotik_controller, sid_data)

    @property
    def name(self) -> str:
        """Return the name of the NAT switch."""
        return f"{self._inst} NAT {self._data['name']}"

    @property
    def icon(self):
        """Return the icon."""
        if not self._data["enabled"]:
            icon = "mdi:network-off-outline"
        else:
            icon = "mdi:network-outline"

        return icon

    @property
    def device_info(self):
        """Return a NAT switch description for device registry."""
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

    async def async_turn_on(self):
        """Turn on the switch."""
        path = "/ip/firewall/nat"
        param = ".id"
        value = None
        for uid in self._ctrl.data["nat"]:
            if (
                self._ctrl.data["nat"][uid]["name"]
                == f"{self._data['protocol']}:{self._data['dst-port']}"
            ):
                value = self._ctrl.data["nat"][uid][".id"]

        mod_param = "disabled"
        mod_value = False
        self._ctrl.set_value(path, param, value, mod_param, mod_value)
        await self._ctrl.force_update()

    async def async_turn_off(self):
        """Turn on the switch."""
        path = "/ip/firewall/nat"
        param = ".id"
        value = None
        for uid in self._ctrl.data["nat"]:
            if (
                self._ctrl.data["nat"][uid]["name"]
                == f"{self._data['protocol']}:{self._data['dst-port']}"
            ):
                value = self._ctrl.data["nat"][uid][".id"]

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
        """Set up script switch."""
        super().__init__(inst, uid, mikrotik_controller, sid_data)

    @property
    def icon(self):
        """Return the icon."""
        return "mdi:script-text-outline"

    @property
    def device_info(self):
        """Return a script switch description for device registry."""
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

    async def async_turn_on(self):
        """Turn on the switch."""
        self._ctrl.run_script(self._data["name"])
        await self._ctrl.force_update()

    async def async_turn_off(self):
        """Turn off the switch."""

    @property
    def is_on(self):
        """Return true if device is on."""
        return False


# ---------------------------
#   MikrotikControllerQueueSwitch
# ---------------------------
class MikrotikControllerQueueSwitch(MikrotikControllerSwitch):
    """Representation of a queue switch."""

    def __init__(self, inst, uid, mikrotik_controller, sid_data):
        """Set up queue switch."""
        super().__init__(inst, uid, mikrotik_controller, sid_data)

    @property
    def icon(self):
        """Return the icon."""
        if not self._data["enabled"]:
            icon = "mdi:leaf-off"
        else:
            icon = "mdi:leaf"

        return icon

    @property
    def device_info(self):
        """Return a queue switch description for device registry."""
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

    async def async_turn_on(self):
        """Turn on the queue switch."""
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

    async def async_turn_off(self):
        """Turn on the queue switch."""
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
