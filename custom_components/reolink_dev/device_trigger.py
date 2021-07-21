""" Additional triggers for ReoLink Camera """

import logging

import voluptuous as vol

from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_PLATFORM,
    CONF_TYPE,
    DEVICE_CLASS_TIMESTAMP,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

from homeassistant.components.automation import AutomationActionType
from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import state as state_trigger
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN

from .utils import async_get_device_entries
from .const import DOMAIN

NEW_VOD = "new_vod"

TRIGGER_TYPES = {NEW_VOD}

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES),
        vol.Optional(CONF_ENTITY_ID): cv.entity_domain(SENSOR_DOMAIN),
    }
)

_LOGGER = logging.getLogger(__name__)


async def async_get_triggers(hass: HomeAssistant, device_id: str):
    """ List of device triggers """

    (device, device_entries) = await async_get_device_entries(hass, device_id)

    triggers = []

    if not device or not device_entries or len(device_entries) < 1:
        return triggers

    for entry in device_entries:
        if (
            entry.domain != SENSOR_DOMAIN
            or entry.device_class != DEVICE_CLASS_TIMESTAMP
        ):
            continue

        triggers.append(
            {
                CONF_PLATFORM: "device",
                CONF_DOMAIN: DOMAIN,
                CONF_DEVICE_ID: device_id,
                CONF_ENTITY_ID: entry.entity_id,
                CONF_TYPE: NEW_VOD,
            }
        )

    return triggers


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: AutomationActionType,
    automation_info: dict,
):
    """ Attach a trigger """

    if config[CONF_TYPE] == NEW_VOD:
        if CONF_ENTITY_ID not in config:
            (_, device_entries) = await async_get_device_entries(
                hass, config[CONF_DEVICE_ID]
            )
            config[CONF_ENTITY_ID] = (
                next(
                    (
                        entry.entity_id
                        for entry in device_entries
                        if entry.domain == SENSOR_DOMAIN
                        and entry.device_class == DEVICE_CLASS_TIMESTAMP
                    )
                )
                if device_entries
                else None
            )

        state_config = state_trigger.TRIGGER_SCHEMA(
            {
                CONF_PLATFORM: "state",
                CONF_ENTITY_ID: config[CONF_ENTITY_ID],
            }
        )

        return await state_trigger.async_attach_trigger(
            hass,
            state_config,
            action,
            automation_info,
            platform_type=config[CONF_PLATFORM],
        )
