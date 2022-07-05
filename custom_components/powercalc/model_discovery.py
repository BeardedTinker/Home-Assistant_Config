"""Utilities for auto discovery of light models."""

from __future__ import annotations

import logging
import os
import re
from typing import NamedTuple, Optional

import homeassistant.helpers.device_registry as dr
import homeassistant.helpers.entity_registry as er
from homeassistant.helpers.typing import HomeAssistantType

from .aliases import MANUFACTURER_ALIASES
from .const import CONF_CUSTOM_MODEL_DIRECTORY, CONF_MANUFACTURER, CONF_MODEL
from .errors import ModelNotSupported
from .light_model import LightModel

_LOGGER = logging.getLogger(__name__)


async def get_light_model(
    hass: HomeAssistantType,
    config: dict,
    entity_entry: Optional[er.RegistryEntry] = None,
) -> Optional[LightModel]:
    manufacturer = config.get(CONF_MANUFACTURER)
    model = config.get(CONF_MODEL)
    if (manufacturer is None or model is None) and entity_entry:
        model_info = await autodiscover_model(hass, entity_entry)
        if model_info:
            manufacturer = config.get(CONF_MANUFACTURER) or model_info.manufacturer
            model = config.get(CONF_MODEL) or model_info.model

    if manufacturer is None or model is None:
        return None

    custom_model_directory = config.get(CONF_CUSTOM_MODEL_DIRECTORY)
    if custom_model_directory:
        custom_model_directory = os.path.join(
            hass.config.config_dir, custom_model_directory
        )

    return LightModel(hass, manufacturer, model, custom_model_directory)


async def is_autoconfigurable(
    hass: HomeAssistantType, entry: er.RegistryEntry, sensor_config: dict = {}
) -> bool:
    try:
        light_model = await get_light_model(hass, sensor_config, entry)
        return bool(
            light_model and not light_model.is_additional_configuration_required
        )
    except ModelNotSupported:
        return False


async def autodiscover_model(
    hass: HomeAssistantType, entity_entry: er.RegistryEntry
) -> Optional[ModelInfo]:
    """Try to auto discover manufacturer and model from the known device information"""

    if not await has_manufacturer_and_model_information(hass, entity_entry):
        _LOGGER.debug(
            "%s: Cannot autodiscover model, manufacturer or model unknown from device registry",
            entity_entry.entity_id,
        )
        return None

    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get(entity_entry.device_id)
    model_id = device_entry.model
    if match := re.search("\(([^\(\)]+)\)$", str(device_entry.model)):
        model_id = match.group(1)

    manufacturer = device_entry.manufacturer
    if MANUFACTURER_ALIASES.get(manufacturer):
        manufacturer = MANUFACTURER_ALIASES.get(manufacturer)

    # Make sure we don't have a literal / in model_id, so we don't get issues with sublut directory matching down the road
    # See github #658
    model_id = model_id.replace("/", "#slash#")

    model_info = ModelInfo(manufacturer, model_id)

    _LOGGER.debug(
        "%s: Auto discovered model (manufacturer=%s, model=%s)",
        entity_entry.entity_id,
        model_info.manufacturer,
        model_info.model,
    )
    return model_info


async def has_manufacturer_and_model_information(
    hass: HomeAssistantType, entity_entry: er.RegistryEntry | None
):
    """See if we have enough information in device registry to automatically setup the power sensor"""

    if entity_entry is None:
        return False

    device_registry = dr.async_get(hass)
    device_entry = device_registry.async_get(entity_entry.device_id)
    if device_entry is None:
        return False

    if device_entry.manufacturer is None or device_entry.model is None:
        return False

    return True


class ModelInfo(NamedTuple):
    manufacturer: str
    model: str
