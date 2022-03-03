"""Definitions for Mikrotik Router device tracker entities."""
from dataclasses import dataclass, field
from typing import List
from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.components.switch import (
    SwitchEntityDescription,
)

DEVICE_ATTRIBUTES_HOST = [
    "interface",
    "source",
    "last-seen",
]


@dataclass
class MikrotikDeviceTrackerEntityDescription(SwitchEntityDescription):
    """Class describing mikrotik entities."""

    key: str = ""
    name: str = ""
    device_class = None
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
    "host": MikrotikDeviceTrackerEntityDescription(
        key="host",
        name="",
        icon_enabled="mdi:lan-connect",
        icon_disabled="mdi:lan-disconnect",
        ha_group="",
        ha_connection=CONNECTION_NETWORK_MAC,
        ha_connection_value="data__mac-address",
        data_path="host",
        data_name="host-name",
        data_uid="mac-address",
        data_reference="mac-address",
        data_attributes_list=DEVICE_ATTRIBUTES_HOST,
    ),
}
