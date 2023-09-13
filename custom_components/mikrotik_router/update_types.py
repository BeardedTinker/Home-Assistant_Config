"""Definitions for Mikrotik Router update entities."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from homeassistant.components.update import UpdateEntityDescription


@dataclass
class MikrotikUpdateEntityDescription(UpdateEntityDescription):
    """Class describing mikrotik entities."""

    ha_group: str | None = None
    ha_connection: str | None = None
    ha_connection_value: str | None = None
    title: str | None = None
    data_path: str | None = None
    data_attribute: str = "available"
    data_name: str | None = None
    data_name_comment: bool = False
    data_uid: str | None = None
    data_reference: str | None = None
    data_attributes_list: List = field(default_factory=lambda: [])
    func: str = "MikrotikRouterOSUpdate"


SENSOR_TYPES: tuple[MikrotikUpdateEntityDescription, ...] = (
    MikrotikUpdateEntityDescription(
        key="system_rosupdate",
        name="RouterOS update",
        ha_group="System",
        title="Mikrotik RouterOS",
        data_path="fw-update",
        data_name="",
        data_uid="",
        data_reference="",
        func="MikrotikRouterOSUpdate",
    ),
    MikrotikUpdateEntityDescription(
        key="system_rbfwupdate",
        name="RouterBOARD firmware update",
        ha_group="System",
        title="Mikrotik RouterBOARD",
        data_path="routerboard",
        data_attribute="current-firmware",
        data_name="",
        data_uid="",
        data_reference="",
        func="MikrotikRouterBoardFWUpdate",
    ),
)


SENSOR_SERVICES = {}
