""" custom helper actions """

import logging

from typing import List, Optional
import voluptuous as vol

from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_TYPE,
    DEVICE_CLASS_TIMESTAMP,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers import config_validation as cv

from homeassistant.components.camera import DOMAIN as CAMERA_DOMAIN, SERVICE_SNAPSHOT
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN

from .utils import async_get_device_entries
from .const import DOMAIN

VOD_THUMB_CAP = "capture_vod_thumbnail"

ACTION_TYPES = {VOD_THUMB_CAP}

ACTION_SCHEMA = cv.DEVICE_ACTION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(ACTION_TYPES),
        vol.Optional(CONF_ENTITY_ID): cv.entities_domain(
            [CAMERA_DOMAIN, SENSOR_DOMAIN]
        ),
    }
)

_LOGGER = logging.getLogger(__name__)


async def async_get_actions(hass: HomeAssistant, device_id: str):
    """List device actions for devices."""

    actions = []

    (device, device_entries) = await async_get_device_entries(hass, device_id)

    if not device or not device_entries or len(device_entries) < 2:
        return actions

    sensor = None
    camera = None
    for entry in device_entries:
        if (
            entry.domain == SENSOR_DOMAIN
            and entry.device_class == DEVICE_CLASS_TIMESTAMP
        ):
            sensor = entry
        if entry.domain == CAMERA_DOMAIN:
            camera = entry
        if sensor and camera:
            actions.append(
                {
                    CONF_DOMAIN: DOMAIN,
                    CONF_DEVICE_ID: device_id,
                    CONF_ENTITY_ID: [camera.entity_id, sensor.cv.entity_id],
                    CONF_TYPE: VOD_THUMB_CAP,
                }
            )
            sensor = None
            camera = None

    _LOGGER.debug("actions: %s", actions)
    return actions


async def async_call_action_from_config(
    hass: HomeAssistant, config: dict, variables: dict, context: Optional[Context]
):
    """Execute a device action."""

    if config[CONF_TYPE] == VOD_THUMB_CAP:
        entity_ids: List[str] = config.get(CONF_ENTITY_ID)
        camera_entity_id: str = None
        thumbnail_path: str = None
        if entity_ids and len(entity_ids) > 0:
            for entity_id in entity_ids:
                state = hass.states.get(entity_id)
                if state and state.domain == CAMERA_DOMAIN:
                    camera_entity_id = entity_id
                elif state and state.domain == SENSOR_DOMAIN:
                    thumbnail_path = state.attributes.get("thumbnail_path")

        if not camera_entity_id or not thumbnail_path:
            (_, device_entries) = await async_get_device_entries(
                hass, config[CONF_DEVICE_ID]
            )
            for entry in device_entries:
                if not camera_entity_id and entry.domain == CAMERA_DOMAIN:
                    camera_entity_id = entry.entity_id
                if (
                    not thumbnail_path
                    and entry.domain == SENSOR_DOMAIN
                    and entry.device_class == DEVICE_CLASS_TIMESTAMP
                ):
                    state = hass.states.get(entry.entity_id)
                    thumbnail_path = (
                        state.attributes.get("thumbnail_path") if state else None
                    )

        service_data = {
            ATTR_ENTITY_ID: camera_entity_id,
            "filename": thumbnail_path,
        }
        _LOGGER.debug("service_data: %s", service_data)
        _LOGGER.debug("variables: %s", variables)
        return await hass.services.async_call(
            CAMERA_DOMAIN,
            SERVICE_SNAPSHOT,
            service_data,
            blocking=True,
            context=context,
        )
