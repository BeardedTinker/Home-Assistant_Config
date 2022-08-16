"""Definitions for Mikrotik Router update entities."""
from dataclasses import dataclass, field
from typing import List
from homeassistant.components.update import UpdateEntityDescription


@dataclass
class MikrotikUpdateEntityDescription(UpdateEntityDescription):
    """Class describing mikrotik entities."""

    ha_group: str = ""
    ha_connection: str = ""
    ha_connection_value: str = ""
    data_path: str = ""
    data_attribute: str = "available"
    data_name: str = ""
    data_name_comment: bool = False
    data_uid: str = ""
    data_reference: str = ""
    data_attributes_list: List = field(default_factory=lambda: [])
    func: str = "MikrotikRouterOSUpdate"


SENSOR_TYPES = {
    "system_rosupdate": MikrotikUpdateEntityDescription(
        key="system_rosupdate",
        name="RouterOS update",
        ha_group="System",
        data_path="fw-update",
        data_name="",
        data_uid="",
        data_reference="",
        func="MikrotikRouterOSUpdate",
    ),
    "system_rbfwupdate": MikrotikUpdateEntityDescription(
        key="system_rbfwupdate",
        name="RouterBoard firmware update",
        ha_group="System",
        data_path="routerboard",
        data_attribute="current-firmware",
        data_name="",
        data_uid="",
        data_reference="",
        func="MikrotikRouterBoardFWUpdate",
    ),
}


SENSOR_SERVICES = {}
