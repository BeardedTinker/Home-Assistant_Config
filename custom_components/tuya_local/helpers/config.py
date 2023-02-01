"""
Helper for general config
"""
import logging

from .. import DOMAIN
from ..const import CONF_DEVICE_ID, CONF_TYPE
from .device_config import get_config

_LOGGER = logging.getLogger(__name__)


async def async_tuya_setup_platform(
    hass, async_add_entities, discovery_info, platform, entity_class
):
    """Common functions for async_setup_platform for each entity platform."""
    data = hass.data[DOMAIN][discovery_info[CONF_DEVICE_ID]]
    device = data["device"]
    entities = []

    cfg = get_config(discovery_info[CONF_TYPE])
    if cfg is None:
        raise ValueError(f"No device config found for {discovery_info}")
    ecfg = cfg.primary_entity
    if ecfg.entity == platform and (
        discovery_info.get(ecfg.config_id, False) or not ecfg.deprecated
    ):
        data[ecfg.config_id] = entity_class(device, ecfg)
        entities.append(data[ecfg.config_id])
        if ecfg.deprecated:
            _LOGGER.warning(ecfg.deprecation_message)
        _LOGGER.debug(f"Adding {platform} for {ecfg.config_id}")

    for ecfg in cfg.secondary_entities():
        if ecfg.entity == platform and (
            discovery_info.get(ecfg.config_id, False) or not ecfg.deprecated
        ):
            data[ecfg.config_id] = entity_class(device, ecfg)
            entities.append(data[ecfg.config_id])
            if ecfg.deprecated:
                _LOGGER.warning(ecfg.deprecation_message)
            _LOGGER.debug(f"Adding {platform} for {ecfg.config_id}")
    if not entities:
        raise ValueError(f"{device.name} does not support use as a {platform} device.")
    async_add_entities(entities)
