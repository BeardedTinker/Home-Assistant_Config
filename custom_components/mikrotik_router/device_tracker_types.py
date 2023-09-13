"""Definitions for Mikrotik Router device tracker entities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from homeassistant.helpers.device_registry import CONNECTION_NETWORK_MAC
from homeassistant.components.switch import (
    SwitchEntityDescription,
)

DEVICE_ATTRIBUTES_HOST = [
    "interface",
    "source",
    "authorized",
    "bypassed",
    "last-seen",
]


@dataclass
class MikrotikDeviceTrackerEntityDescription(SwitchEntityDescription):
    """Class describing mikrotik entities."""

    key: str | None = None
    name: str | None = None
    device_class = None
    icon_enabled: str | None = None
    icon_disabled: str | None = None
    ha_group: str | None = None
    ha_connection: str | None = None
    ha_connection_value: str | None = None
    data_path: str | None = None
    data_attribute: str = "available"
    data_name: str | None = None
    data_uid: str | None = None
    data_reference: str | None = None
    data_attributes_list: List = field(default_factory=lambda: [])
    func: str = "MikrotikDeviceTracker"


SENSOR_TYPES: tuple[MikrotikDeviceTrackerEntityDescription, ...] = (
    MikrotikDeviceTrackerEntityDescription(
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
        func="MikrotikHostDeviceTracker",
    ),
)

SENSOR_SERVICES = {}
