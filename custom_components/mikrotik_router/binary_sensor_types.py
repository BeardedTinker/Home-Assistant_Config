"""Definitions for Mikrotik Router sensor entities."""
from dataclasses import dataclass, field
from typing import List
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.helpers.entity import EntityCategory
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntityDescription,
)

from .const import DOMAIN

DEVICE_ATTRIBUTES_PPP_SECRET = [
    "connected",
    "service",
    "profile",
    "comment",
    "caller-id",
    "encoding",
]

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
]

DEVICE_ATTRIBUTES_IFACE_ETHER = [
    "status",
    "auto-negotiation",
    "rate",
    "full-duplex",
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


@dataclass
class MikrotikBinarySensorEntityDescription(BinarySensorEntityDescription):
    """Class describing mikrotik entities."""

    icon_enabled: str = ""
    icon_disabled: str = ""
    ha_group: str = ""
    ha_connection: str = ""
    ha_connection_value: str = ""
    data_path: str = ""
    data_is_on: str = "available"
    data_name: str = ""
    data_uid: str = ""
    data_reference: str = ""
    data_attributes_list: List = field(default_factory=lambda: [])


SENSOR_TYPES = {
    "system_fwupdate": MikrotikBinarySensorEntityDescription(
        key="system_fwupdate",
        name="Firmware update",
        icon_enabled="",
        icon_disabled="",
        device_class=BinarySensorDeviceClass.UPDATE,
        entity_category=EntityCategory.DIAGNOSTIC,
        ha_group="System",
        data_path="fw-update",
        data_name="",
        data_uid="",
        data_reference="",
    ),
    "ppp_tracker": MikrotikBinarySensorEntityDescription(
        key="ppp_tracker",
        name="PPP",
        icon_enabled="mdi:account-network-outline",
        icon_disabled="mdi:account-off-outline",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        ha_group="PPP",
        ha_connection=DOMAIN,
        ha_connection_value="PPP",
        data_path="ppp_secret",
        data_is_on="connected",
        data_name="name",
        data_uid="name",
        data_reference="name",
        data_attributes_list=DEVICE_ATTRIBUTES_PPP_SECRET,
    ),
    "interface": MikrotikBinarySensorEntityDescription(
        key="interface",
        name="",
        icon_enabled="mdi:lan-connect",
        icon_disabled="mdi:lan-pending",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
        ha_group="data__default-name",
        ha_connection=CONNECTION_NETWORK_MAC,
        ha_connection_value="data__port-mac-address",
        data_path="interface",
        data_is_on="running",
        data_name="name",
        data_uid="default-name",
        data_reference="default-name",
        data_attributes_list=DEVICE_ATTRIBUTES_IFACE,
    ),
}
