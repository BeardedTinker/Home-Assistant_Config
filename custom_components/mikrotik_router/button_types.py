"""Definitions for Mikrotik Router button entities."""
from __future__ import annotations

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

    ha_group: str | None = None
    ha_connection: str | None = None
    ha_connection_value: str | None = None
    data_path: str | None = None
    data_attribute: str | None = None
    data_name: str | None = None
    data_name_comment: bool = False
    data_uid: str | None = None
    data_reference: str | None = None
    data_attributes_list: List = field(default_factory=lambda: [])
    func: str = "MikrotikButton"


SENSOR_TYPES: tuple[MikrotikButtonEntityDescription, ...] = (
    MikrotikButtonEntityDescription(
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
)

SENSOR_SERVICES = {}
