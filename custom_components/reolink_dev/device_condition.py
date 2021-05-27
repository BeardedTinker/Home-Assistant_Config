""" Additional conditions for ReoLink Camera """

import logging
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_ENTITY_ID,
    CONF_FOR,
    CONF_TYPE,
    DEVICE_CLASS_TIMESTAMP,
)

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import condition, config_validation as cv
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.helpers.typing import ConfigType, TemplateVarsType

import voluptuous as vol

from .utils import async_get_device_entries
from .const import DOMAIN

NO_THUMBNAIL = "vod_no_thumbnail"
HAS_THUMBNAIL = "vod_has_thumbnail"

CONDITION_TYPES = {NO_THUMBNAIL, HAS_THUMBNAIL}

CONDITION_SCHEMA = cv.DEVICE_CONDITION_BASE_SCHEMA.extend(
    {
        vol.Required(CONF_TYPE): vol.In(CONDITION_TYPES),
        vol.Required(CONF_ENTITY_ID): cv.entity_domain(SENSOR_DOMAIN),
    }
)

_LOGGER = logging.getLogger(__name__)


async def async_get_conditions(hass: HomeAssistant, device_id: str):
    """List device conditions for devices."""

    conditions = []

    (device, device_entries) = await async_get_device_entries(hass, device_id)

    if not device or not device_entries or len(device_entries) < 1:
        return conditions

    for entry in device_entries:
        if (
            entry.domain != SENSOR_DOMAIN
            or entry.device_class != DEVICE_CLASS_TIMESTAMP
        ):
            continue

        conditions.append(
            {
                CONF_DOMAIN: DOMAIN,
                CONF_DEVICE_ID: device_id,
                CONF_ENTITY_ID: entry.entity_id,
                CONF_TYPE: NO_THUMBNAIL,
            }
        )
        conditions.append(
            {
                CONF_DOMAIN: DOMAIN,
                CONF_DEVICE_ID: device_id,
                CONF_ENTITY_ID: entry.entity_id,
                CONF_TYPE: HAS_THUMBNAIL,
            },
        )

    return conditions


@callback
def async_condition_from_config(
    config: ConfigType, config_validation: bool
) -> condition.ConditionCheckerType:
    """Create a function to test a device condition."""

    if config_validation:
        config = CONDITION_SCHEMA(config)

    config_type = config[CONF_TYPE]

    if config_type in {NO_THUMBNAIL, HAS_THUMBNAIL}:
        if config_type == NO_THUMBNAIL:
            state = "false"
        else:
            state = "true"

        entity_id: str = config[CONF_ENTITY_ID]
        for_period = config.get(CONF_FOR)
        attribute = "has_thumbnail"

        # @trace_condition_function
        def test_is_state(hass: HomeAssistant, variables: TemplateVarsType):
            """ Test thumbnail state """

            return condition.state(
                hass,
                entity_id,
                state,
                for_period,
                attribute,
            )

        return test_is_state
