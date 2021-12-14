"""Mikrotik Controller for Mikrotik Router."""

import asyncio
import ipaddress
import logging
import re
import pytz

from datetime import datetime, timedelta
from ipaddress import ip_address, IPv4Network
from mac_vendor_lookup import AsyncMacLookup

from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.util.dt import utcnow
from homeassistant.components.device_tracker import DOMAIN as DEVICE_TRACKER_DOMAIN

from homeassistant.const import (
    CONF_NAME,
    CONF_HOST,
    CONF_PORT,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_USERNAME,
    CONF_PASSWORD,
    CONF_SSL,
)

from .const import (
    DOMAIN,
    CONF_TRACK_IFACE_CLIENTS,
    DEFAULT_TRACK_IFACE_CLIENTS,
    CONF_TRACK_HOSTS,
    DEFAULT_TRACK_HOSTS,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_UNIT_OF_MEASUREMENT,
    CONF_SENSOR_PORT_TRAFFIC,
    DEFAULT_SENSOR_PORT_TRAFFIC,
    CONF_SENSOR_CLIENT_TRAFFIC,
    DEFAULT_SENSOR_CLIENT_TRAFFIC,
    CONF_SENSOR_SIMPLE_QUEUES,
    DEFAULT_SENSOR_SIMPLE_QUEUES,
    CONF_SENSOR_NAT,
    DEFAULT_SENSOR_NAT,
    CONF_SENSOR_MANGLE,
    DEFAULT_SENSOR_MANGLE,
    CONF_SENSOR_FILTER,
    DEFAULT_SENSOR_FILTER,
    CONF_SENSOR_KIDCONTROL,
    DEFAULT_SENSOR_KIDCONTROL,
    CONF_SENSOR_PPP,
    DEFAULT_SENSOR_PPP,
    CONF_SENSOR_SCRIPTS,
    DEFAULT_SENSOR_SCRIPTS,
    CONF_SENSOR_ENVIRONMENT,
    DEFAULT_SENSOR_ENVIRONMENT,
)
from .exceptions import ApiEntryNotFound
from .helper import parse_api
from .mikrotikapi import MikrotikAPI

_LOGGER = logging.getLogger(__name__)

DEFAULT_TIME_ZONE = None


def is_valid_ip(address):
    try:
        ipaddress.ip_address(address)
        return True
    except ValueError:
        return False


def utc_from_timestamp(timestamp: float) -> datetime:
    """Return a UTC time from a timestamp."""
    return pytz.utc.localize(datetime.utcfromtimestamp(timestamp))


def as_local(dattim: datetime) -> datetime:
    """Convert a UTC datetime object to local time zone."""
    if dattim.tzinfo == DEFAULT_TIME_ZONE:
        return dattim
    if dattim.tzinfo is None:
        dattim = pytz.utc.localize(dattim)

    return dattim.astimezone(DEFAULT_TIME_ZONE)


# ---------------------------
#   MikrotikControllerData
# ---------------------------
class MikrotikControllerData:
    """MikrotikController Class"""

    def __init__(self, hass, config_entry):
        """Initialize MikrotikController."""
        self.hass = hass
        self.config_entry = config_entry
        self.name = config_entry.data[CONF_NAME]
        self.host = config_entry.data[CONF_HOST]

        self.data = {
            "routerboard": {},
            "resource": {},
            "health": {},
            "interface": {},
            "bridge": {},
            "bridge_host": {},
            "arp": {},
            "nat": {},
            "kid-control": {},
            "mangle": {},
            "filter": {},
            "ppp_secret": {},
            "ppp_active": {},
            "fw-update": {},
            "script": {},
            "queue": {},
            "dns": {},
            "dhcp-server": {},
            "dhcp-network": {},
            "dhcp": {},
            "capsman_hosts": {},
            "wireless_hosts": {},
            "host": {},
            "host_hass": {},
            "accounting": {},
            "environment": {},
        }

        self.listeners = []
        self.lock = asyncio.Lock()
        self.lock_ping = asyncio.Lock()

        self.api = MikrotikAPI(
            config_entry.data[CONF_HOST],
            config_entry.data[CONF_USERNAME],
            config_entry.data[CONF_PASSWORD],
            config_entry.data[CONF_PORT],
            config_entry.data[CONF_SSL],
        )

        self.api_ping = MikrotikAPI(
            config_entry.data[CONF_HOST],
            config_entry.data[CONF_USERNAME],
            config_entry.data[CONF_PASSWORD],
            config_entry.data[CONF_PORT],
            config_entry.data[CONF_SSL],
        )

        self.nat_removed = {}
        self.mangle_removed = {}
        self.filter_removed = {}
        self.host_hass_recovered = False
        self.host_tracking_initialized = False

        self.support_capsman = False
        self.support_wireless = False
        self.support_ppp = False

        self.major_fw_version = 0

        self._force_update_callback = None
        self._force_fwupdate_check_callback = None
        self._async_ping_tracked_hosts_callback = None

        self.async_mac_lookup = AsyncMacLookup()
        # self.async_mac_lookup.update_vendors()

    async def async_init(self):
        self._force_update_callback = async_track_time_interval(
            self.hass, self.force_update, self.option_scan_interval
        )
        self._force_fwupdate_check_callback = async_track_time_interval(
            self.hass, self.force_fwupdate_check, timedelta(hours=1)
        )
        self._async_ping_tracked_hosts_callback = async_track_time_interval(
            self.hass, self.async_ping_tracked_hosts, timedelta(seconds=15)
        )

    # ---------------------------
    #   option_track_iface_clients
    # ---------------------------
    @property
    def option_track_iface_clients(self):
        """Config entry option to not track ARP."""
        return self.config_entry.options.get(
            CONF_TRACK_IFACE_CLIENTS, DEFAULT_TRACK_IFACE_CLIENTS
        )

    # ---------------------------
    #   option_track_network_hosts
    # ---------------------------
    @property
    def option_track_network_hosts(self):
        """Config entry option to not track ARP."""
        return self.config_entry.options.get(CONF_TRACK_HOSTS, DEFAULT_TRACK_HOSTS)

    # ---------------------------
    #   option_sensor_port_traffic
    # ---------------------------
    @property
    def option_sensor_port_traffic(self):
        """Config entry option to not track ARP."""
        return self.config_entry.options.get(
            CONF_SENSOR_PORT_TRAFFIC, DEFAULT_SENSOR_PORT_TRAFFIC
        )

    # ---------------------------
    #   option_sensor_client_traffic
    # ---------------------------
    @property
    def option_sensor_client_traffic(self):
        """Config entry option to not track ARP."""
        return self.config_entry.options.get(
            CONF_SENSOR_CLIENT_TRAFFIC, DEFAULT_SENSOR_CLIENT_TRAFFIC
        )

    # ---------------------------
    #   option_sensor_simple_queues
    # ---------------------------
    @property
    def option_sensor_simple_queues(self):
        """Config entry option to not track ARP."""
        return self.config_entry.options.get(
            CONF_SENSOR_SIMPLE_QUEUES, DEFAULT_SENSOR_SIMPLE_QUEUES
        )

    # ---------------------------
    #   option_sensor_nat
    # ---------------------------
    @property
    def option_sensor_nat(self):
        """Config entry option to not track ARP."""
        return self.config_entry.options.get(CONF_SENSOR_NAT, DEFAULT_SENSOR_NAT)

    # ---------------------------
    #   option_sensor_mangle
    # ---------------------------
    @property
    def option_sensor_mangle(self):
        """Config entry option to not track ARP."""
        return self.config_entry.options.get(CONF_SENSOR_MANGLE, DEFAULT_SENSOR_MANGLE)

    # ---------------------------
    #   option_sensor_filter
    # ---------------------------
    @property
    def option_sensor_filter(self):
        """Config entry option to not track ARP."""
        return self.config_entry.options.get(CONF_SENSOR_FILTER, DEFAULT_SENSOR_FILTER)

    # ---------------------------
    #   option_sensor_kidcontrol
    # ---------------------------
    @property
    def option_sensor_kidcontrol(self):
        """Config entry option to not track ARP."""
        return self.config_entry.options.get(
            CONF_SENSOR_KIDCONTROL, DEFAULT_SENSOR_KIDCONTROL
        )

    # ---------------------------
    #   option_sensor_ppp
    # ---------------------------
    @property
    def option_sensor_ppp(self):
        """Config entry option to not track ARP."""
        return self.config_entry.options.get(CONF_SENSOR_PPP, DEFAULT_SENSOR_PPP)

    # ---------------------------
    #   option_sensor_scripts
    # ---------------------------
    @property
    def option_sensor_scripts(self):
        """Config entry option to not track ARP."""
        return self.config_entry.options.get(
            CONF_SENSOR_SCRIPTS, DEFAULT_SENSOR_SCRIPTS
        )

    # ---------------------------
    #   option_sensor_environment
    # ---------------------------
    @property
    def option_sensor_environment(self):
        """Config entry option to not track ARP."""
        return self.config_entry.options.get(
            CONF_SENSOR_ENVIRONMENT, DEFAULT_SENSOR_ENVIRONMENT
        )

    # ---------------------------
    #   option_scan_interval
    # ---------------------------
    @property
    def option_scan_interval(self):
        """Config entry option scan interval."""
        scan_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )
        return timedelta(seconds=scan_interval)

    # ---------------------------
    #   option_unit_of_measurement
    # ---------------------------
    @property
    def option_unit_of_measurement(self):
        """Config entry option to not track ARP."""
        return self.config_entry.options.get(
            CONF_UNIT_OF_MEASUREMENT, DEFAULT_UNIT_OF_MEASUREMENT
        )

    # ---------------------------
    #   signal_update
    # ---------------------------
    @property
    def signal_update(self):
        """Event to signal new data."""
        return f"{DOMAIN}-update-{self.name}"

    # ---------------------------
    #   async_reset
    # ---------------------------
    async def async_reset(self):
        """Reset dispatchers"""
        for unsub_dispatcher in self.listeners:
            unsub_dispatcher()

        self.listeners = []
        return True

    # ---------------------------
    #   connected
    # ---------------------------
    def connected(self):
        """Return connected state"""
        return self.api.connected()

    # ---------------------------
    #   set_value
    # ---------------------------
    def set_value(self, path, param, value, mod_param, mod_value):
        """Change value using Mikrotik API"""
        return self.api.update(path, param, value, mod_param, mod_value)

    # ---------------------------
    #   execute
    # ---------------------------
    def execute(self, path, command, param, value):
        """Change value using Mikrotik API"""
        return self.api.execute(path, command, param, value)

    # ---------------------------
    #   run_script
    # ---------------------------
    def run_script(self, name):
        """Run script using Mikrotik API"""
        if type(name) != str:
            if "router" not in name.data:
                return

            if self.config_entry.data["name"] != name.data.get("router"):
                return

            if "script" in name.data:
                name = name.data.get("script")
            else:
                return

        try:
            self.api.run_script(name)
        except ApiEntryNotFound as error:
            _LOGGER.error("Failed to run script: %s", error)

    # ---------------------------
    #   get_capabilities
    # ---------------------------
    def get_capabilities(self):
        """Update Mikrotik data"""
        packages = parse_api(
            data={},
            source=self.api.path("/system/package"),
            key="name",
            vals=[
                {"name": "name"},
                {
                    "name": "enabled",
                    "source": "disabled",
                    "type": "bool",
                    "reverse": True,
                },
            ],
        )

        if "ppp" in packages:
            self.support_ppp = packages["ppp"]["enabled"]

        if "wireless" in packages:
            self.support_capsman = packages["wireless"]["enabled"]
            self.support_wireless = packages["wireless"]["enabled"]
        else:
            self.support_capsman = False
            self.support_wireless = False

        if self.major_fw_version >= 7:
            self.support_capsman = True
            self.support_wireless = True
            self.support_ppp = True

    # ---------------------------
    #   async_get_host_hass
    # ---------------------------
    async def async_get_host_hass(self):
        """Get host data from HA entity registry"""
        registry = await self.hass.helpers.entity_registry.async_get_registry()
        for entity in registry.entities.values():
            if (
                entity.config_entry_id == self.config_entry.entry_id
                and entity.domain == DEVICE_TRACKER_DOMAIN
                and "-host-" in entity.unique_id
            ):
                _, mac = entity.unique_id.split("-host-", 2)
                self.data["host_hass"][mac] = entity.original_name

    # ---------------------------
    #   async_hwinfo_update
    # ---------------------------
    async def async_hwinfo_update(self):
        """Update Mikrotik hardware info"""
        try:
            await asyncio.wait_for(self.lock.acquire(), timeout=30)
        except:
            return

        await self.hass.async_add_executor_job(self.get_firmware_update)

        if self.api.connected():
            await self.hass.async_add_executor_job(self.get_capabilities)

        if self.api.connected():
            await self.hass.async_add_executor_job(self.get_system_routerboard)

        if self.api.connected():
            await self.hass.async_add_executor_job(self.get_system_resource)

        if self.api.connected() and self.option_sensor_scripts:
            await self.hass.async_add_executor_job(self.get_script)

        if self.api.connected():
            await self.hass.async_add_executor_job(self.get_dhcp_network)

        if self.api.connected():
            await self.hass.async_add_executor_job(self.get_dns)

        self.lock.release()

    # ---------------------------
    #   force_fwupdate_check
    # ---------------------------
    @callback
    async def force_fwupdate_check(self, _now=None):
        """Trigger hourly update by timer"""
        await self.async_fwupdate_check()

    # ---------------------------
    #   async_fwupdate_check
    # ---------------------------
    async def async_fwupdate_check(self):
        """Update Mikrotik data"""
        await self.hass.async_add_executor_job(self.get_firmware_update)
        async_dispatcher_send(self.hass, self.signal_update)

    # ---------------------------
    #   async_ping_tracked_hosts
    # ---------------------------
    @callback
    async def async_ping_tracked_hosts(self, _now=None):
        """Trigger update by timer"""
        if not self.option_track_network_hosts:
            return

        try:
            await asyncio.wait_for(self.lock_ping.acquire(), timeout=3)
        except:
            return

        for uid in list(self.data["host"]):
            if not self.host_tracking_initialized:
                # Add missing default values
                for key, default in zip(
                    [
                        "address",
                        "mac-address",
                        "interface",
                        "host-name",
                        "last-seen",
                        "available",
                    ],
                    ["unknown", "unknown", "unknown", "unknown", False, False],
                ):
                    if key not in self.data["host"][uid]:
                        self.data["host"][uid][key] = default

            # Check host availability
            if (
                self.data["host"][uid]["source"] not in ["capsman", "wireless"]
                and self.data["host"][uid]["address"] != "unknown"
                and self.data["host"][uid]["interface"] != "unknown"
            ):
                tmp_interface = self.data["host"][uid]["interface"]
                if uid in self.data["arp"] and self.data["arp"][uid]["bridge"] != "":
                    tmp_interface = self.data["arp"][uid]["bridge"]

                _LOGGER.debug(
                    "Ping host: %s (%s)", uid, self.data["host"][uid]["address"]
                )
                self.data["host"][uid][
                    "available"
                ] = await self.hass.async_add_executor_job(
                    self.api_ping.arp_ping,
                    self.data["host"][uid]["address"],
                    tmp_interface,
                )

            # Update last seen
            if self.data["host"][uid]["available"]:
                self.data["host"][uid]["last-seen"] = utcnow()

        self.host_tracking_initialized = True
        self.lock_ping.release()

    # ---------------------------
    #   force_update
    # ---------------------------
    @callback
    async def force_update(self, _now=None):
        """Trigger update by timer"""
        await self.async_update()

    # ---------------------------
    #   async_update
    # ---------------------------
    async def async_update(self):
        """Update Mikrotik data"""
        if self.api.has_reconnected():
            await self.async_hwinfo_update()

        try:
            await asyncio.wait_for(self.lock.acquire(), timeout=10)
        except:
            return

        await self.hass.async_add_executor_job(self.get_interface)

        if self.api.connected() and "available" not in self.data["fw-update"]:
            await self.async_fwupdate_check()

        if self.api.connected() and not self.data["host_hass"]:
            await self.async_get_host_hass()

        if self.api.connected() and self.support_capsman:
            await self.hass.async_add_executor_job(self.get_capsman_hosts)

        if self.api.connected() and self.support_wireless:
            await self.hass.async_add_executor_job(self.get_wireless_hosts)

        if self.api.connected():
            await self.hass.async_add_executor_job(self.get_bridge)

        if self.api.connected():
            await self.hass.async_add_executor_job(self.get_arp)

        if self.api.connected():
            await self.hass.async_add_executor_job(self.get_dhcp)

        if self.api.connected():
            await self.async_process_host()

        if self.api.connected() and self.option_sensor_port_traffic:
            await self.hass.async_add_executor_job(self.get_interface_traffic)

        if self.api.connected():
            await self.hass.async_add_executor_job(self.process_interface_client)

        if self.api.connected() and self.option_sensor_nat:
            await self.hass.async_add_executor_job(self.get_nat)

        if self.api.connected() and self.option_sensor_kidcontrol:
            await self.hass.async_add_executor_job(self.get_kidcontrol)

        if self.api.connected() and self.option_sensor_mangle:
            await self.hass.async_add_executor_job(self.get_mangle)

        if self.api.connected() and self.option_sensor_filter:
            await self.hass.async_add_executor_job(self.get_filter)

        if self.api.connected() and self.support_ppp and self.option_sensor_ppp:
            await self.hass.async_add_executor_job(self.get_ppp)

        if self.api.connected():
            await self.hass.async_add_executor_job(self.get_system_resource)

        if (
            self.api.connected()
            and self.option_sensor_client_traffic
            and 0 < self.major_fw_version < 7
        ):
            await self.hass.async_add_executor_job(self.process_accounting)

        if self.api.connected() and self.option_sensor_simple_queues:
            await self.hass.async_add_executor_job(self.get_queue)

        if self.api.connected() and self.option_sensor_environment:
            await self.hass.async_add_executor_job(self.get_environment)

        if self.api.connected():
            await self.hass.async_add_executor_job(self.get_system_health)

        async_dispatcher_send(self.hass, self.signal_update)
        self.lock.release()

    # ---------------------------
    #   get_interface
    # ---------------------------
    def get_interface(self):
        """Get all interfaces data from Mikrotik"""
        self.data["interface"] = parse_api(
            data=self.data["interface"],
            source=self.api.path("/interface"),
            key="default-name",
            key_secondary="name",
            vals=[
                {"name": "default-name"},
                {"name": ".id"},
                {"name": "name", "default_val": "default-name"},
                {"name": "type", "default": "unknown"},
                {"name": "running", "type": "bool"},
                {
                    "name": "enabled",
                    "source": "disabled",
                    "type": "bool",
                    "reverse": True,
                },
                {"name": "port-mac-address", "source": "mac-address"},
                {"name": "comment"},
                {"name": "last-link-down-time"},
                {"name": "last-link-up-time"},
                {"name": "link-downs"},
                {"name": "tx-queue-drop"},
                {"name": "actual-mtu"},
                {"name": "about", "source": ".about", "default": ""},
            ],
            ensure_vals=[
                {"name": "client-ip-address"},
                {"name": "client-mac-address"},
                {"name": "rx-bits-per-second", "default": 0},
                {"name": "tx-bits-per-second", "default": 0},
            ],
            skip=[
                {"name": "type", "value": "bridge"},
                {"name": "type", "value": "ppp-in"},
                {"name": "type", "value": "pptp-in"},
                {"name": "type", "value": "sstp-in"},
                {"name": "type", "value": "l2tp-in"},
                {"name": "type", "value": "pppoe-in"},
                {"name": "type", "value": "ovpn-in"},
            ],
        )

        self.data["interface"] = parse_api(
            data=self.data["interface"],
            source=self.api.path("/interface/ethernet"),
            key="default-name",
            key_secondary="name",
            vals=[
                {"name": "default-name"},
                {"name": "name", "default_val": "default-name"},
                {"name": "poe-out", "default": "N/A"},
                {"name": "sfp-shutdown-temperature", "default": ""},
            ],
            skip=[
                {"name": "type", "value": "bridge"},
                {"name": "type", "value": "ppp-in"},
                {"name": "type", "value": "pptp-in"},
                {"name": "type", "value": "sstp-in"},
                {"name": "type", "value": "l2tp-in"},
                {"name": "type", "value": "pppoe-in"},
                {"name": "type", "value": "ovpn-in"},
            ],
        )

        # Udpate virtual interfaces
        for uid, vals in self.data["interface"].items():
            if vals["default-name"] == "":
                self.data["interface"][uid]["default-name"] = vals["name"]
                self.data["interface"][uid][
                    "port-mac-address"
                ] = f"{vals['port-mac-address']}-{vals['name']}"

            if (
                "sfp-shutdown-temperature" in vals
                and vals["sfp-shutdown-temperature"] != ""
            ):
                self.data["interface"] = parse_api(
                    data=self.data["interface"],
                    source=self.api.get_sfp(vals[".id"]),
                    key_search="name",
                    vals=[
                        {"name": "status", "default": "unknown"},
                        {"name": "auto-negotiation", "default": "unknown"},
                        {"name": "advertising", "default": "unknown"},
                        {"name": "link-partner-advertising", "default": "unknown"},
                        {"name": "sfp-temperature", "default": "unknown"},
                        {"name": "sfp-supply-voltage", "default": "unknown"},
                        {"name": "sfp-module-present", "default": "unknown"},
                        {"name": "sfp-tx-bias-current", "default": "unknown"},
                        {"name": "sfp-tx-power", "default": "unknown"},
                        {"name": "sfp-rx-power", "default": "unknown"},
                        {"name": "sfp-rx-loss", "default": "unknown"},
                        {"name": "sfp-tx-fault", "default": "unknown"},
                        {"name": "sfp-type", "default": "unknown"},
                        {"name": "sfp-connector-type", "default": "unknown"},
                        {"name": "sfp-vendor-name", "default": "unknown"},
                        {"name": "sfp-vendor-part-number", "default": "unknown"},
                        {"name": "sfp-vendor-revision", "default": "unknown"},
                        {"name": "sfp-vendor-serial", "default": "unknown"},
                        {"name": "sfp-manufacturing-date", "default": "unknown"},
                        {"name": "eeprom-checksum", "default": "unknown"},
                    ],
                )

    # ---------------------------
    #   get_interface_traffic
    # ---------------------------
    def get_interface_traffic(self):
        """Get traffic for all interfaces from Mikrotik"""
        interface_list = ""
        for uid in self.data["interface"]:
            interface_list += self.data["interface"][uid]["name"] + ","

        interface_list = interface_list[:-1]

        self.data["interface"] = parse_api(
            data=self.data["interface"],
            source=self.api.get_traffic(interface_list),
            key_search="name",
            vals=[
                {"name": "rx-bits-per-second", "default": 0},
                {"name": "tx-bits-per-second", "default": 0},
            ],
        )

        uom_type, uom_div = self._get_unit_of_measurement()

        for uid in self.data["interface"]:
            self.data["interface"][uid]["rx-bits-per-second-attr"] = uom_type
            self.data["interface"][uid]["tx-bits-per-second-attr"] = uom_type
            self.data["interface"][uid]["rx-bits-per-second"] = round(
                self.data["interface"][uid]["rx-bits-per-second"] * uom_div
            )
            self.data["interface"][uid]["tx-bits-per-second"] = round(
                self.data["interface"][uid]["tx-bits-per-second"] * uom_div
            )

    # ---------------------------
    #   get_bridge
    # ---------------------------
    def get_bridge(self):
        """Get system resources data from Mikrotik"""
        self.data["bridge_host"] = parse_api(
            data=self.data["bridge_host"],
            source=self.api.path("/interface/bridge/host"),
            key="mac-address",
            vals=[
                {"name": "mac-address"},
                {"name": "interface", "default": "unknown"},
                {"name": "bridge", "default": "unknown"},
                {
                    "name": "enabled",
                    "source": "disabled",
                    "type": "bool",
                    "reverse": True,
                },
            ],
            only=[{"key": "local", "value": False}],
        )

        for uid, vals in self.data["bridge_host"].items():
            self.data["bridge"][vals["bridge"]] = True

    # ---------------------------
    #   process_interface_client
    # ---------------------------
    def process_interface_client(self):
        # Remove data if disabled
        if not self.option_track_iface_clients:
            for uid in self.data["interface"]:
                self.data["interface"][uid]["client-ip-address"] = "disabled"
                self.data["interface"][uid]["client-mac-address"] = "disabled"
            return

        for uid, vals in self.data["interface"].items():
            self.data["interface"][uid]["client-ip-address"] = ""
            self.data["interface"][uid]["client-mac-address"] = ""
            for arp_uid, arp_vals in self.data["arp"].items():
                if arp_vals["interface"] != vals["name"]:
                    continue

                if self.data["interface"][uid]["client-ip-address"] == "":
                    self.data["interface"][uid]["client-ip-address"] = arp_vals[
                        "address"
                    ]
                else:
                    self.data["interface"][uid]["client-ip-address"] = "multiple"

                if self.data["interface"][uid]["client-mac-address"] == "":
                    self.data["interface"][uid]["client-mac-address"] = arp_vals[
                        "mac-address"
                    ]
                else:
                    self.data["interface"][uid]["client-mac-address"] = "multiple"

            if self.data["interface"][uid]["client-ip-address"] == "":
                self.data["interface"][uid]["client-ip-address"] = "none"

            if self.data["interface"][uid]["client-mac-address"] == "":
                self.data["interface"][uid]["client-mac-address"] = "none"

    # ---------------------------
    #   get_nat
    # ---------------------------
    def get_nat(self):
        """Get NAT data from Mikrotik"""
        self.data["nat"] = parse_api(
            data=self.data["nat"],
            source=self.api.path("/ip/firewall/nat"),
            key=".id",
            vals=[
                {"name": ".id"},
                {"name": "chain", "default": "unknown"},
                {"name": "action", "default": "unknown"},
                {"name": "protocol", "default": "any"},
                {"name": "dst-port", "default": "any"},
                {"name": "in-interface", "default": "any"},
                {"name": "out-interface", "default": "any"},
                {"name": "to-addresses"},
                {"name": "to-ports", "default": "any"},
                {"name": "comment"},
                {
                    "name": "enabled",
                    "source": "disabled",
                    "type": "bool",
                    "reverse": True,
                },
            ],
            val_proc=[
                [
                    {"name": "uniq-id"},
                    {"action": "combine"},
                    {"key": "chain"},
                    {"text": ","},
                    {"key": "action"},
                    {"text": ","},
                    {"key": "protocol"},
                    {"text": ","},
                    {"key": "in-interface"},
                    {"text": ":"},
                    {"key": "dst-port"},
                    {"text": "-"},
                    {"key": "out-interface"},
                    {"text": ":"},
                    {"key": "to-addresses"},
                    {"text": ":"},
                    {"key": "to-ports"},
                ],
                [
                    {"name": "name"},
                    {"action": "combine"},
                    {"key": "protocol"},
                    {"text": ":"},
                    {"key": "dst-port"},
                ],
            ],
            only=[{"key": "action", "value": "dst-nat"}],
        )

        # Remove duplicate NAT entries to prevent crash
        nat_uniq = {}
        nat_del = {}
        for uid in self.data["nat"]:
            tmp_name = self.data["nat"][uid]["uniq-id"]
            if tmp_name not in nat_uniq:
                nat_uniq[tmp_name] = uid
            else:
                nat_del[uid] = 1
                nat_del[nat_uniq[tmp_name]] = 1

        for uid in nat_del:
            if self.data["nat"][uid]["uniq-id"] not in self.nat_removed:
                self.nat_removed[self.data["nat"][uid]["uniq-id"]] = 1
                _LOGGER.error(
                    "Mikrotik %s duplicate NAT rule %s, entity will be unavailable.",
                    self.host,
                    self.data["nat"][uid]["name"],
                )

            del self.data["nat"][uid]

    # ---------------------------
    #   get_mangle
    # ---------------------------
    def get_mangle(self):
        """Get Mangle data from Mikrotik"""
        self.data["mangle"] = parse_api(
            data=self.data["mangle"],
            source=self.api.path("/ip/firewall/mangle"),
            key=".id",
            vals=[
                {"name": ".id"},
                {"name": "chain"},
                {"name": "action"},
                {"name": "comment"},
                {"name": "address-list"},
                {"name": "passthrough", "type": "bool", "default": False},
                {"name": "protocol", "default": "any"},
                {"name": "src-address", "default": "any"},
                {"name": "src-port", "default": "any"},
                {"name": "dst-address", "default": "any"},
                {"name": "dst-port", "default": "any"},
                {
                    "name": "enabled",
                    "source": "disabled",
                    "type": "bool",
                    "reverse": True,
                },
            ],
            val_proc=[
                [
                    {"name": "uniq-id"},
                    {"action": "combine"},
                    {"key": "chain"},
                    {"text": ","},
                    {"key": "action"},
                    {"text": ","},
                    {"key": "protocol"},
                    {"text": ","},
                    {"key": "src-address"},
                    {"text": ":"},
                    {"key": "src-port"},
                    {"text": "-"},
                    {"key": "dst-address"},
                    {"text": ":"},
                    {"key": "dst-port"},
                ],
                [
                    {"name": "name"},
                    {"action": "combine"},
                    {"key": "action"},
                    {"text": ","},
                    {"key": "protocol"},
                    {"text": ":"},
                    {"key": "dst-port"},
                ],
            ],
            skip=[
                {"name": "dynamic", "value": True},
                {"name": "action", "value": "jump"},
            ],
        )

        # Remove duplicate Mangle entries to prevent crash
        mangle_uniq = {}
        mangle_del = {}
        for uid in self.data["mangle"]:
            tmp_name = self.data["mangle"][uid]["uniq-id"]
            if tmp_name not in mangle_uniq:
                mangle_uniq[tmp_name] = uid
            else:
                mangle_del[uid] = 1
                mangle_del[mangle_uniq[tmp_name]] = 1

        for uid in mangle_del:
            if self.data["mangle"][uid]["uniq-id"] not in self.mangle_removed:
                self.mangle_removed[self.data["mangle"][uid]["uniq-id"]] = 1
                _LOGGER.error(
                    "Mikrotik %s duplicate Mangle rule %s, entity will be unavailable.",
                    self.host,
                    self.data["mangle"][uid]["name"],
                )

            del self.data["mangle"][uid]

    # ---------------------------
    #   get_filter
    # ---------------------------
    def get_filter(self):
        """Get Filter data from Mikrotik"""
        self.data["filter"] = parse_api(
            data=self.data["filter"],
            source=self.api.path("/ip/firewall/filter"),
            key=".id",
            vals=[
                {"name": ".id"},
                {"name": "chain"},
                {"name": "action"},
                {"name": "comment"},
                {"name": "address-list"},
                {"name": "protocol", "default": "any"},
                {"name": "in-interface", "default": "any"},
                {"name": "out-interface", "default": "any"},
                {"name": "src-address", "default": "any"},
                {"name": "src-port", "default": "any"},
                {"name": "dst-address", "default": "any"},
                {"name": "dst-port", "default": "any"},
                {"name": "layer7-protocol", "default": "any"},
                {"name": "connection-state", "default": "any"},
                {"name": "tcp-flags", "default": "any"},
                {
                    "name": "enabled",
                    "source": "disabled",
                    "type": "bool",
                    "reverse": True,
                    "default": True,
                },
            ],
            val_proc=[
                [
                    {"name": "uniq-id"},
                    {"action": "combine"},
                    {"key": "chain"},
                    {"text": ","},
                    {"key": "action"},
                    {"text": ","},
                    {"key": "protocol"},
                    {"text": ","},
                    {"key": "layer7-protocol"},
                    {"text": ","},
                    {"key": "in-interface"},
                    {"text": ":"},
                    {"key": "src-address"},
                    {"text": ":"},
                    {"key": "src-port"},
                    {"text": "-"},
                    {"key": "out-interface"},
                    {"text": ":"},
                    {"key": "dst-address"},
                    {"text": ":"},
                    {"key": "dst-port"},
                ],
                [
                    {"name": "name"},
                    {"action": "combine"},
                    {"key": "action"},
                    {"text": ","},
                    {"key": "protocol"},
                    {"text": ":"},
                    {"key": "dst-port"},
                ],
            ],
            skip=[
                {"name": "dynamic", "value": True},
                {"name": "action", "value": "jump"},
            ],
        )

        # Remove duplicate filter entries to prevent crash
        filter_uniq = {}
        filter_del = {}
        for uid in self.data["filter"]:
            tmp_name = self.data["filter"][uid]["uniq-id"]
            if tmp_name not in filter_uniq:
                filter_uniq[tmp_name] = uid
            else:
                filter_del[uid] = 1
                filter_del[filter_uniq[tmp_name]] = 1

        for uid in filter_del:
            if self.data["filter"][uid]["uniq-id"] not in self.filter_removed:
                self.filter_removed[self.data["filter"][uid]["uniq-id"]] = 1
                _LOGGER.error(
                    "Mikrotik %s duplicate Filter rule %s, entity will be unavailable.",
                    self.host,
                    self.data["filter"][uid]["name"],
                )

            del self.data["filter"][uid]

    # ---------------------------
    #   get_kidcontrol
    # ---------------------------
    def get_kidcontrol(self):
        """Get Kid-control data from Mikrotik"""
        self.data["kid-control"] = parse_api(
            data=self.data["kid-control"],
            source=self.api.path("/ip/kid-control"),
            key="name",
            vals=[
                {"name": "name"},
                {"name": "rate-limit"},
                {"name": "mon", "default": "None"},
                {"name": "tue", "default": "None"},
                {"name": "wed", "default": "None"},
                {"name": "thu", "default": "None"},
                {"name": "fri", "default": "None"},
                {"name": "sat", "default": "None"},
                {"name": "sun", "default": "None"},
                {"name": "comment"},
                {"name": "paused", "type": "bool", "reverse": True},
                {
                    "name": "enabled",
                    "source": "disabled",
                    "type": "bool",
                    "reverse": True,
                },
            ],
        )

    # ---------------------------
    #   get_ppp
    # ---------------------------
    def get_ppp(self):
        """Get PPP data from Mikrotik"""
        self.data["ppp_secret"] = parse_api(
            data=self.data["ppp_secret"],
            source=self.api.path("/ppp/secret"),
            key="name",
            vals=[
                {"name": "name"},
                {"name": "service"},
                {"name": "profile"},
                {"name": "comment"},
                {
                    "name": "enabled",
                    "source": "disabled",
                    "type": "bool",
                    "reverse": True,
                },
            ],
            ensure_vals=[
                {"name": "caller-id", "default": ""},
                {"name": "encoding", "default": ""},
                {"name": "connected", "default": False},
            ],
        )

        self.data["ppp_active"] = parse_api(
            data={},
            source=self.api.path("/ppp/active"),
            key="name",
            vals=[
                {"name": "name"},
                {"name": "service"},
                {"name": "caller-id"},
                {"name": "encoding"},
            ],
        )

        for uid in self.data["ppp_secret"]:
            if self.data["ppp_secret"][uid]["name"] in self.data["ppp_active"]:
                self.data["ppp_secret"][uid]["connected"] = True
                self.data["ppp_secret"][uid]["caller-id"] = self.data["ppp_active"][
                    uid
                ]["caller-id"]
                self.data["ppp_secret"][uid]["encoding"] = self.data["ppp_active"][uid][
                    "encoding"
                ]
            else:
                self.data["ppp_secret"][uid]["connected"] = False
                self.data["ppp_secret"][uid]["caller-id"] = "not connected"
                self.data["ppp_secret"][uid]["encoding"] = "not connected"

    # ---------------------------
    #   get_system_routerboard
    # ---------------------------
    def get_system_routerboard(self):
        """Get routerboard data from Mikrotik"""
        self.data["routerboard"] = parse_api(
            data=self.data["routerboard"],
            source=self.api.path("/system/routerboard"),
            vals=[
                {"name": "routerboard", "type": "bool"},
                {"name": "model", "default": "unknown"},
                {"name": "serial-number", "default": "unknown"},
                {
                    "name": "firmware",
                    "source": "current-firmware",
                    "default": "unknown",
                },
            ],
        )

    # ---------------------------
    #   get_system_health
    # ---------------------------
    def get_system_health(self):
        """Get routerboard data from Mikrotik"""
        self.data["health"] = parse_api(
            data=self.data["health"],
            source=self.api.path("/system/health"),
            vals=[
                {"name": "temperature", "default": "unknown"},
                {"name": "cpu-temperature", "default": "unknown"},
                {"name": "power-consumption", "default": "unknown"},
                {"name": "board-temperature1", "default": "unknown"},
                {"name": "fan1-speed", "default": "unknown"},
                {"name": "fan2-speed", "default": "unknown"},
            ],
        )

    # ---------------------------
    #   get_system_resource
    # ---------------------------
    def get_system_resource(self):
        """Get system resources data from Mikrotik"""
        self.data["resource"] = parse_api(
            data=self.data["resource"],
            source=self.api.path("/system/resource"),
            vals=[
                {"name": "platform", "default": "unknown"},
                {"name": "board-name", "default": "unknown"},
                {"name": "version", "default": "unknown"},
                {"name": "uptime_str", "source": "uptime", "default": "unknown"},
                {"name": "cpu-load", "default": "unknown"},
                {"name": "free-memory", "default": 0},
                {"name": "total-memory", "default": 0},
                {"name": "free-hdd-space", "default": 0},
                {"name": "total-hdd-space", "default": 0},
            ],
            ensure_vals=[
                {"name": "uptime", "default": 0},
            ],
        )

        tmp_uptime = 0
        tmp = re.split(r"(\d+)[s]", self.data["resource"]["uptime_str"])
        if len(tmp) > 1:
            tmp_uptime += int(tmp[1])
        tmp = re.split(r"(\d+)[m]", self.data["resource"]["uptime_str"])
        if len(tmp) > 1:
            tmp_uptime += int(tmp[1]) * 60
        tmp = re.split(r"(\d+)[h]", self.data["resource"]["uptime_str"])
        if len(tmp) > 1:
            tmp_uptime += int(tmp[1]) * 3600
        tmp = re.split(r"(\d+)[d]", self.data["resource"]["uptime_str"])
        if len(tmp) > 1:
            tmp_uptime += int(tmp[1]) * 86400
        tmp = re.split(r"(\d+)[w]", self.data["resource"]["uptime_str"])
        if len(tmp) > 1:
            tmp_uptime += int(tmp[1]) * 604800

        now = datetime.now().replace(microsecond=0)
        uptime_tm = datetime.timestamp(now - timedelta(seconds=tmp_uptime))
        update_uptime = False
        if not self.data["resource"]["uptime"]:
            update_uptime = True
        else:
            uptime_old = datetime.timestamp(
                datetime.fromisoformat(self.data["resource"]["uptime"])
            )
            if uptime_tm > uptime_old + 10:
                update_uptime = True

        if update_uptime:
            self.data["resource"]["uptime"] = str(
                as_local(utc_from_timestamp(uptime_tm)).isoformat()
            )

        if self.data["resource"]["total-memory"] > 0:
            self.data["resource"]["memory-usage"] = round(
                (
                    (
                        self.data["resource"]["total-memory"]
                        - self.data["resource"]["free-memory"]
                    )
                    / self.data["resource"]["total-memory"]
                )
                * 100
            )
        else:
            self.data["resource"]["memory-usage"] = "unknown"

        if self.data["resource"]["total-hdd-space"] > 0:
            self.data["resource"]["hdd-usage"] = round(
                (
                    (
                        self.data["resource"]["total-hdd-space"]
                        - self.data["resource"]["free-hdd-space"]
                    )
                    / self.data["resource"]["total-hdd-space"]
                )
                * 100
            )
        else:
            self.data["resource"]["hdd-usage"] = "unknown"

    # ---------------------------
    #   get_firmware_update
    # ---------------------------
    def get_firmware_update(self):
        """Check for firmware update on Mikrotik"""
        self.data["fw-update"] = parse_api(
            data=self.data["fw-update"],
            source=self.api.path("/system/package/update"),
            vals=[
                {"name": "status"},
                {"name": "channel", "default": "unknown"},
                {"name": "installed-version", "default": "unknown"},
                {"name": "latest-version", "default": "unknown"},
            ],
        )

        if "status" in self.data["fw-update"]:
            self.data["fw-update"]["available"] = (
                True
                if self.data["fw-update"]["status"] == "New version is available"
                else False
            )
        else:
            self.data["fw-update"]["available"] = False

        if self.data["fw-update"]["installed-version"] != "unknown":
            try:
                self.major_fw_version = int(
                    self.data["fw-update"].get("installed-version").split(".")[0]
                )
            except:
                _LOGGER.error(
                    "Mikrotik %s unable to determine major FW version (%s).",
                    self.host,
                    self.data["fw-update"].get("installed-version"),
                )

    # ---------------------------
    #   get_script
    # ---------------------------
    def get_script(self):
        """Get list of all scripts from Mikrotik"""
        self.data["script"] = parse_api(
            data=self.data["script"],
            source=self.api.path("/system/script"),
            key="name",
            vals=[
                {"name": "name"},
                {"name": "last-started", "default": "unknown"},
                {"name": "run-count", "default": "unknown"},
            ],
        )

    # ---------------------------
    #   get_environment
    # ---------------------------
    def get_environment(self):
        """Get list of all environment variables from Mikrotik"""
        self.data["environment"] = parse_api(
            data=self.data["environment"],
            source=self.api.path("/system/script/environment"),
            key="name",
            vals=[
                {"name": "name"},
                {"name": "value"},
            ],
        )

    # ---------------------------
    #   get_queue
    # ---------------------------
    def get_queue(self):
        """Get Queue data from Mikrotik"""
        self.data["queue"] = parse_api(
            data=self.data["queue"],
            source=self.api.path("/queue/simple"),
            key="name",
            vals=[
                {"name": ".id"},
                {"name": "name", "default": "unknown"},
                {"name": "target", "default": "unknown"},
                {"name": "rate", "default": "0/0"},
                {"name": "max-limit", "default": "0/0"},
                {"name": "limit-at", "default": "0/0"},
                {"name": "burst-limit", "default": "0/0"},
                {"name": "burst-threshold", "default": "0/0"},
                {"name": "burst-time", "default": "0s/0s"},
                {"name": "packet-marks", "default": "none"},
                {"name": "parent", "default": "none"},
                {"name": "comment"},
                {
                    "name": "enabled",
                    "source": "disabled",
                    "type": "bool",
                    "reverse": True,
                },
            ],
        )

        uom_type, uom_div = self._get_unit_of_measurement()
        for uid, vals in self.data["queue"].items():
            upload_max_limit_bps, download_max_limit_bps = [
                int(x) for x in vals["max-limit"].split("/")
            ]
            self.data["queue"][uid][
                "upload-max-limit"
            ] = f"{round(upload_max_limit_bps * uom_div)} {uom_type}"
            self.data["queue"][uid][
                "download-max-limit"
            ] = f"{round(download_max_limit_bps * uom_div)} {uom_type}"

            upload_rate_bps, download_rate_bps = [
                int(x) for x in vals["rate"].split("/")
            ]
            self.data["queue"][uid][
                "upload-rate"
            ] = f"{round(upload_rate_bps * uom_div)} {uom_type}"
            self.data["queue"][uid][
                "download-rate"
            ] = f"{round(download_rate_bps * uom_div)} {uom_type}"

            upload_limit_at_bps, download_limit_at_bps = [
                int(x) for x in vals["limit-at"].split("/")
            ]
            self.data["queue"][uid][
                "upload-limit-at"
            ] = f"{round(upload_limit_at_bps * uom_div)} {uom_type}"
            self.data["queue"][uid][
                "download-limit-at"
            ] = f"{round(download_limit_at_bps * uom_div)} {uom_type}"

            upload_burst_limit_bps, download_burst_limit_bps = [
                int(x) for x in vals["burst-limit"].split("/")
            ]
            self.data["queue"][uid][
                "upload-burst-limit"
            ] = f"{round(upload_burst_limit_bps * uom_div)} {uom_type}"
            self.data["queue"][uid][
                "download-burst-limit"
            ] = f"{round(download_burst_limit_bps * uom_div)} {uom_type}"

            upload_burst_threshold_bps, download_burst_threshold_bps = [
                int(x) for x in vals["burst-threshold"].split("/")
            ]
            self.data["queue"][uid][
                "upload-burst-threshold"
            ] = f"{round(upload_burst_threshold_bps * uom_div)} {uom_type}"
            self.data["queue"][uid][
                "download-burst-threshold"
            ] = f"{round(download_burst_threshold_bps * uom_div)} {uom_type}"

            upload_burst_time, download_burst_time = vals["burst-time"].split("/")
            self.data["queue"][uid]["upload-burst-time"] = upload_burst_time
            self.data["queue"][uid]["download-burst-time"] = download_burst_time

    # ---------------------------
    #   get_arp
    # ---------------------------
    def get_arp(self):
        """Get ARP data from Mikrotik"""
        self.data["arp"] = parse_api(
            data=self.data["arp"],
            source=self.api.path("/ip/arp"),
            key="mac-address",
            vals=[{"name": "mac-address"}, {"name": "address"}, {"name": "interface"}],
            ensure_vals=[{"name": "bridge", "default": ""}],
        )

        for uid, vals in self.data["arp"].items():
            if (
                vals["interface"] in self.data["bridge"]
                and uid in self.data["bridge_host"]
            ):
                self.data["arp"][uid]["bridge"] = vals["interface"]
                self.data["arp"][uid]["interface"] = self.data["bridge_host"][uid][
                    "interface"
                ]

    # ---------------------------
    #   get_dns
    # ---------------------------
    def get_dns(self):
        """Get static DNS data from Mikrotik"""
        self.data["dns"] = parse_api(
            data=self.data["dns"],
            source=self.api.path("/ip/dns/static"),
            key="name",
            vals=[{"name": "name"}, {"name": "address"}, {"name": "comment"}],
        )

    # ---------------------------
    #   get_dhcp
    # ---------------------------
    def get_dhcp(self):
        """Get DHCP data from Mikrotik"""
        self.data["dhcp"] = parse_api(
            data=self.data["dhcp"],
            source=self.api.path("/ip/dhcp-server/lease"),
            key="mac-address",
            vals=[
                {"name": "mac-address"},
                {"name": "active-mac-address", "default": "unknown"},
                {"name": "address", "default": "unknown"},
                {"name": "active-address", "default": "unknown"},
                {"name": "host-name", "default": "unknown"},
                {"name": "status", "default": "unknown"},
                {"name": "last-seen", "default": "unknown"},
                {"name": "server", "default": "unknown"},
                {"name": "comment", "default": ""},
            ],
            ensure_vals=[{"name": "interface", "default": "unknown"}],
        )

        dhcpserver_query = False
        for uid in self.data["dhcp"]:
            # is_valid_ip
            if self.data["dhcp"][uid]["address"] != "unknown":
                if not is_valid_ip(self.data["dhcp"][uid]["address"]):
                    self.data["dhcp"][uid]["address"] = "unknown"

                if (
                    self.data["dhcp"][uid]["active-address"]
                    != self.data["dhcp"][uid]["address"]
                    and self.data["dhcp"][uid]["active-address"] != "unknown"
                ):
                    self.data["dhcp"][uid]["address"] = self.data["dhcp"][uid][
                        "active-address"
                    ]

                if (
                    self.data["dhcp"][uid]["mac-address"]
                    != self.data["dhcp"][uid]["active-mac-address"]
                    and self.data["dhcp"][uid]["active-mac-address"] != "unknown"
                ):
                    self.data["dhcp"][uid]["mac-address"] = self.data["dhcp"][uid][
                        "active-mac-address"
                    ]

            if (
                not dhcpserver_query
                and self.data["dhcp"][uid]["server"] not in self.data["dhcp-server"]
            ):
                self.get_dhcp_server()
                dhcpserver_query = True

            if self.data["dhcp"][uid]["server"] in self.data["dhcp-server"]:
                self.data["dhcp"][uid]["interface"] = self.data["dhcp-server"][
                    self.data["dhcp"][uid]["server"]
                ]["interface"]
            elif uid in self.data["arp"]:
                if self.data["arp"][uid]["bridge"] != "unknown":
                    self.data["dhcp"][uid]["interface"] = self.data["arp"][uid][
                        "bridge"
                    ]
                else:
                    self.data["dhcp"][uid]["interface"] = self.data["arp"][uid][
                        "interface"
                    ]

    # ---------------------------
    #   get_dhcp_server
    # ---------------------------
    def get_dhcp_server(self):
        """Get DHCP server data from Mikrotik"""
        self.data["dhcp-server"] = parse_api(
            data=self.data["dhcp-server"],
            source=self.api.path("/ip/dhcp-server"),
            key="name",
            vals=[{"name": "name"}, {"name": "interface", "default": "unknown"}],
        )

    # ---------------------------
    #   get_dhcp_network
    # ---------------------------
    def get_dhcp_network(self):
        """Get DHCP network data from Mikrotik"""
        self.data["dhcp-network"] = parse_api(
            data=self.data["dhcp-network"],
            source=self.api.path("/ip/dhcp-server/network"),
            key="address",
            vals=[
                {"name": "address"},
                {"name": "gateway", "default": ""},
                {"name": "netmask", "default": ""},
                {"name": "dns-server", "default": ""},
                {"name": "domain", "default": ""},
            ],
            ensure_vals=[{"name": "address"}, {"name": "IPv4Network", "default": ""}],
        )

        for uid, vals in self.data["dhcp-network"].items():
            if vals["IPv4Network"] == "":
                self.data["dhcp-network"][uid]["IPv4Network"] = IPv4Network(
                    vals["address"]
                )

    # ---------------------------
    #   get_capsman_hosts
    # ---------------------------
    def get_capsman_hosts(self):
        """Get CAPS-MAN hosts data from Mikrotik"""
        self.data["capsman_hosts"] = parse_api(
            data={},
            source=self.api.path("/caps-man/registration-table"),
            key="mac-address",
            vals=[
                {"name": "mac-address"},
                {"name": "interface", "default": "unknown"},
                {"name": "ssid", "default": "unknown"},
            ],
        )

    # ---------------------------
    #   get_wireless_hosts
    # ---------------------------
    def get_wireless_hosts(self):
        """Get wireless hosts data from Mikrotik"""
        self.data["wireless_hosts"] = parse_api(
            data={},
            source=self.api.path("/interface/wireless/registration-table"),
            key="mac-address",
            vals=[
                {"name": "mac-address"},
                {"name": "interface", "default": "unknown"},
                {"name": "ap", "type": "bool"},
                {"name": "uptime"},
            ],
        )

    # ---------------------------
    #   async_process_host
    # ---------------------------
    async def async_process_host(self):
        """Get host tracking data"""
        # Add hosts from CAPS-MAN
        capsman_detected = {}
        if self.support_capsman:
            for uid, vals in self.data["capsman_hosts"].items():
                if uid not in self.data["host"]:
                    self.data["host"][uid] = {}

                self.data["host"][uid]["source"] = "capsman"
                capsman_detected[uid] = True
                self.data["host"][uid]["available"] = True
                self.data["host"][uid]["last-seen"] = utcnow()
                for key in ["mac-address", "interface"]:
                    if (
                        key not in self.data["host"][uid]
                        or self.data["host"][uid][key] == "unknown"
                    ):
                        self.data["host"][uid][key] = vals[key]

        # Add hosts from wireless
        wireless_detected = {}
        if self.support_wireless:
            for uid, vals in self.data["wireless_hosts"].items():
                if vals["ap"]:
                    continue

                if uid not in self.data["host"]:
                    self.data["host"][uid] = {}

                self.data["host"][uid]["source"] = "wireless"
                wireless_detected[uid] = True
                self.data["host"][uid]["available"] = True
                self.data["host"][uid]["last-seen"] = utcnow()
                for key in ["mac-address", "interface"]:
                    if (
                        key not in self.data["host"][uid]
                        or self.data["host"][uid][key] == "unknown"
                    ):
                        self.data["host"][uid][key] = vals[key]

        # Add hosts from DHCP
        for uid, vals in self.data["dhcp"].items():
            if uid not in self.data["host"]:
                self.data["host"][uid] = {}
                self.data["host"][uid]["source"] = "dhcp"
                for key in ["address", "mac-address", "interface"]:
                    if (
                        key not in self.data["host"][uid]
                        or self.data["host"][uid][key] == "unknown"
                    ):
                        self.data["host"][uid][key] = vals[key]

        # Add hosts from ARP
        for uid, vals in self.data["arp"].items():
            if uid not in self.data["host"]:
                self.data["host"][uid] = {}
                self.data["host"][uid]["source"] = "arp"
                for key in ["address", "mac-address", "interface"]:
                    if (
                        key not in self.data["host"][uid]
                        or self.data["host"][uid][key] == "unknown"
                    ):
                        self.data["host"][uid][key] = vals[key]

        # Add restored hosts from hass registry
        if not self.host_hass_recovered:
            self.host_hass_recovered = True
            for uid in self.data["host_hass"]:
                if uid not in self.data["host"]:
                    self.data["host"][uid] = {}
                    self.data["host"][uid]["source"] = "restored"
                    self.data["host"][uid]["mac-address"] = uid
                    self.data["host"][uid]["host-name"] = self.data["host_hass"][uid]

        for uid, vals in self.data["host"].items():
            # Add missing default values
            for key, default in zip(
                [
                    "address",
                    "mac-address",
                    "interface",
                    "host-name",
                    "manufacturer",
                    "last-seen",
                    "available",
                ],
                ["unknown", "unknown", "unknown", "unknown", "detect", False, False],
            ):
                if key not in self.data["host"][uid]:
                    self.data["host"][uid][key] = default

        if not self.host_tracking_initialized:
            await self.async_ping_tracked_hosts(utcnow())

        # Process hosts
        for uid, vals in self.data["host"].items():
            # CAPS-MAN availability
            if vals["source"] == "capsman" and uid not in capsman_detected:
                self.data["host"][uid]["available"] = False

            # Wireless availability
            if vals["source"] == "wireless" and uid not in wireless_detected:
                self.data["host"][uid]["available"] = False

            # Update IP and interface (DHCP/returned host)
            if uid in self.data["dhcp"] and "." in self.data["dhcp"][uid]["address"]:
                if (
                    self.data["dhcp"][uid]["address"]
                    != self.data["host"][uid]["address"]
                ):
                    self.data["host"][uid]["address"] = self.data["dhcp"][uid][
                        "address"
                    ]
                    if vals["source"] not in ["capsman", "wireless"]:
                        self.data["host"][uid]["source"] = "dhcp"
                        self.data["host"][uid]["interface"] = self.data["dhcp"][uid][
                            "interface"
                        ]

            elif (
                uid in self.data["arp"]
                and "." in self.data["arp"][uid]["address"]
                and self.data["arp"][uid]["address"]
                != self.data["host"][uid]["address"]
            ):
                self.data["host"][uid]["address"] = self.data["arp"][uid]["address"]
                if vals["source"] not in ["capsman", "wireless"]:
                    self.data["host"][uid]["source"] = "arp"
                    self.data["host"][uid]["interface"] = self.data["arp"][uid][
                        "interface"
                    ]

            if vals["host-name"] == "unknown":
                # Resolve hostname from static DNS
                if vals["address"] != "unknown":
                    for dns_uid, dns_vals in self.data["dns"].items():
                        if dns_vals["address"] == vals["address"]:
                            if dns_vals["comment"].split("#", 1)[0] != "":
                                self.data["host"][uid]["host-name"] = dns_vals[
                                    "comment"
                                ].split("#", 1)[0]
                            elif (
                                uid in self.data["dhcp"]
                                and self.data["dhcp"][uid]["comment"].split("#", 1)[0]
                                != ""
                            ):
                                # Override name if DHCP comment exists
                                self.data["host"][uid]["host-name"] = self.data["dhcp"][
                                    uid
                                ]["comment"].split("#", 1)[0]
                            else:
                                self.data["host"][uid]["host-name"] = dns_vals[
                                    "name"
                                ].split(".")[0]
                            break

                # Resolve hostname from DHCP comment
                if (
                    self.data["host"][uid]["host-name"] == "unknown"
                    and uid in self.data["dhcp"]
                    and self.data["dhcp"][uid]["comment"].split("#", 1)[0] != ""
                ):
                    self.data["host"][uid]["host-name"] = self.data["dhcp"][uid][
                        "comment"
                    ].split("#", 1)[0]
                # Resolve hostname from DHCP hostname
                elif (
                    self.data["host"][uid]["host-name"] == "unknown"
                    and uid in self.data["dhcp"]
                    and self.data["dhcp"][uid]["host-name"] != "unknown"
                ):
                    self.data["host"][uid]["host-name"] = self.data["dhcp"][uid][
                        "host-name"
                    ]
                # Fallback to mac address for hostname
                elif self.data["host"][uid]["host-name"] == "unknown":
                    self.data["host"][uid]["host-name"] = uid

            # Resolve manufacturer
            if vals["manufacturer"] == "detect" and vals["mac-address"] != "unknown":
                try:
                    self.data["host"][uid][
                        "manufacturer"
                    ] = await self.async_mac_lookup.lookup(vals["mac-address"])
                except:
                    self.data["host"][uid]["manufacturer"] = ""

            if vals["manufacturer"] == "detect":
                self.data["host"][uid]["manufacturer"] = ""

    # ---------------------------
    #   process_accounting
    # ---------------------------
    def process_accounting(self):
        """Get Accounting data from Mikrotik"""
        # Check if accounting and account-local-traffic is enabled
        (
            accounting_enabled,
            local_traffic_enabled,
        ) = self.api.is_accounting_and_local_traffic_enabled()
        uom_type, uom_div = self._get_unit_of_measurement()

        # Build missing hosts from main hosts dict
        for uid, vals in self.data["host"].items():
            if uid not in self.data["accounting"]:
                self.data["accounting"][uid] = {
                    "address": vals["address"],
                    "mac-address": vals["mac-address"],
                    "host-name": vals["host-name"],
                    "tx-rx-attr": uom_type,
                    "available": False,
                    "local_accounting": False,
                }

        _LOGGER.debug(f"Working with {len(self.data['accounting'])} accounting devices")

        # Build temp accounting values dict with ip address as key
        tmp_accounting_values = {}
        for uid, vals in self.data["accounting"].items():
            tmp_accounting_values[vals["address"]] = {
                "wan-tx": 0,
                "wan-rx": 0,
                "lan-tx": 0,
                "lan-rx": 0,
            }

        time_diff = self.api.take_accounting_snapshot()
        if time_diff:
            accounting_data = parse_api(
                data={},
                source=self.api.path("/ip/accounting/snapshot"),
                key=".id",
                vals=[
                    {"name": ".id"},
                    {"name": "src-address"},
                    {"name": "dst-address"},
                    {"name": "bytes", "default": 0},
                ],
            )

            threshold = self.api.path("/ip/accounting")[0].get("threshold")
            entry_count = len(accounting_data)

            if entry_count is threshold:
                _LOGGER.warning(
                    f"Accounting entries count reached the threshold of {threshold}!"
                    " Some entries were not saved by Mikrotik so accounting calculation won't be correct."
                    " Consider shortening update interval or"
                    " increasing the accounting threshold value in Mikrotik."
                )
            elif entry_count > threshold * 0.9:
                _LOGGER.info(
                    f"Accounting entries count ({entry_count} reached 90% of the threshold,"
                    f" currently set to {threshold}! Consider shortening update interval or"
                    " increasing the accounting threshold value in Mikrotik."
                )

            for item in accounting_data.values():
                source_ip = str(item.get("src-address")).strip()
                destination_ip = str(item.get("dst-address")).strip()
                bits_count = int(str(item.get("bytes")).strip()) * 8

                if self._address_part_of_local_network(
                    source_ip
                ) and self._address_part_of_local_network(destination_ip):
                    # LAN TX/RX
                    if source_ip in tmp_accounting_values:
                        tmp_accounting_values[source_ip]["lan-tx"] += bits_count
                    if destination_ip in tmp_accounting_values:
                        tmp_accounting_values[destination_ip]["lan-rx"] += bits_count
                elif self._address_part_of_local_network(
                    source_ip
                ) and not self._address_part_of_local_network(destination_ip):
                    # WAN TX
                    if source_ip in tmp_accounting_values:
                        tmp_accounting_values[source_ip]["wan-tx"] += bits_count
                elif (
                    not self._address_part_of_local_network(source_ip)
                    and self._address_part_of_local_network(destination_ip)
                    and destination_ip in tmp_accounting_values
                ):
                    # WAN RX
                    tmp_accounting_values[destination_ip]["wan-rx"] += bits_count

        # Calculate real throughput and transform it to appropriate unit
        # Also handle availability of accounting and local_accounting from Mikrotik
        for addr, vals in tmp_accounting_values.items():
            uid = self._get_accounting_uid_by_ip(addr)
            if not uid:
                _LOGGER.warning(
                    f"Address {addr} not found in accounting data, skipping update"
                )
                continue

            self.data["accounting"][uid]["tx-rx-attr"] = uom_type
            self.data["accounting"][uid]["available"] = accounting_enabled
            self.data["accounting"][uid]["local_accounting"] = local_traffic_enabled

            if not accounting_enabled:
                # Skip calculation for WAN and LAN if accounting is disabled
                continue

            self.data["accounting"][uid]["wan-tx"] = (
                round(vals["wan-tx"] / time_diff * uom_div, 2)
                if vals["wan-tx"]
                else 0.0
            )
            self.data["accounting"][uid]["wan-rx"] = (
                round(vals["wan-rx"] / time_diff * uom_div, 2)
                if vals["wan-rx"]
                else 0.0
            )

            if not local_traffic_enabled:
                # Skip calculation for LAN if LAN accounting is disabled
                continue

            self.data["accounting"][uid]["lan-tx"] = (
                round(vals["lan-tx"] / time_diff * uom_div, 2)
                if vals["lan-tx"]
                else 0.0
            )
            self.data["accounting"][uid]["lan-rx"] = (
                round(vals["lan-rx"] / time_diff * uom_div, 2)
                if vals["lan-rx"]
                else 0.0
            )

    # ---------------------------
    #   _get_unit_of_measurement
    # ---------------------------
    def _get_unit_of_measurement(self):
        uom_type = self.option_unit_of_measurement
        if uom_type == "Kbps":
            uom_div = 0.001
        elif uom_type == "Mbps":
            uom_div = 0.000001
        elif uom_type == "B/s":
            uom_div = 0.125
        elif uom_type == "KB/s":
            uom_div = 0.000125
        elif uom_type == "MB/s":
            uom_div = 0.000000125
        else:
            uom_type = "bps"
            uom_div = 1
        return uom_type, uom_div

    # ---------------------------
    #   _address_part_of_local_network
    # ---------------------------
    def _address_part_of_local_network(self, address):
        address = ip_address(address)
        for vals in self.data["dhcp-network"].values():
            if address in vals["IPv4Network"]:
                return True
        return False

    # ---------------------------
    #   _get_accounting_uid_by_ip
    # ---------------------------
    def _get_accounting_uid_by_ip(self, requested_ip):
        for mac, vals in self.data["accounting"].items():
            if vals.get("address") is requested_ip:
                return mac
        return None

    # ---------------------------
    #   _get_iface_from_entry
    # ---------------------------
    def _get_iface_from_entry(self, entry):
        """Get interface default-name using name from interface dict"""
        uid = None
        for ifacename in self.data["interface"]:
            if self.data["interface"][ifacename]["name"] == entry["interface"]:
                uid = ifacename
                break

        return uid
