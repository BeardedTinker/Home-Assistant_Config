"""Definitions for Mikrotik Router button entities."""
from dataclasses import dataclass, field
from typing import List
from homeassistant.components.sensor import (
    SensorEntityDescription,
)
from .const import DOMAIN


DEVICE_ATTRIBUTES_SCRIPT = [
    "last-started",
    "run-count",
]


@dataclass
class MikrotikButtonEntityDescription(SensorEntityDescription):
    """Class describing mikrotik entities."""

    ha_group: str = ""
    ha_connection: str = ""
    ha_connection_value: str = ""
    data_path: str = ""
    data_attribute: str = ""
    data_name: str = ""
    data_name_comment: bool = False
    data_uid: str = ""
    data_reference: str = ""
    data_attributes_list: List = field(default_factory=lambda: [])
    func: str = "MikrotikButton"


SENSOR_TYPES = {
    "script": MikrotikButtonEntityDescription(
        key="script",
        name="",
        icon="mdi:script-text-outline",
        device_class=None,
        entity_category=None,
        ha_group="Script",
        ha_connection=DOMAIN,
        ha_connection_value="Script",
        data_path="script",
        data_name="name",
        data_uid="name",
        data_reference="name",
        data_attributes_list=DEVICE_ATTRIBUTES_SCRIPT,
        func="MikrotikScriptButton",
    ),
}

SENSOR_SERVICES = {}
