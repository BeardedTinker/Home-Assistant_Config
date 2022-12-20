"""Provides device triggers for HASS.Agent."""
from __future__ import annotations
from typing import Any

import voluptuous as vol

from homeassistant.helpers.trigger import (
    TriggerActionType,
    TriggerInfo,
)
from homeassistant.components.device_automation import DEVICE_TRIGGER_BASE_SCHEMA
from homeassistant.components.homeassistant.triggers import event as event_trigger
from homeassistant.components.mqtt.device_trigger import mqtt_trigger

from homeassistant.components.mqtt.const import (
    CONF_ENCODING,
    CONF_QOS,
    CONF_TOPIC,
    CONF_PAYLOAD,
)
from homeassistant.components.mqtt.device_trigger import DEFAULT_ENCODING
from homeassistant.const import (
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_EVENT,
    CONF_PLATFORM,
    CONF_TYPE,
    CONF_VALUE_TEMPLATE,
)
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, CONF_ACTION, CONF_DEVICE_NAME


TRIGGER_TYPES = {"notifications_mqtt", "notifications_event"}

TRIGGER_SCHEMA = DEVICE_TRIGGER_BASE_SCHEMA.extend(
    {vol.Required(CONF_TYPE): vol.In(TRIGGER_TYPES), vol.Required(CONF_ACTION): str}
)


async def async_get_triggers(
    hass: HomeAssistant, device_id: str
) -> list[dict[str, Any]]:
    """List device triggers for HASS.Agent devices."""

    triggers = [
        {
            CONF_PLATFORM: "device",
            CONF_DOMAIN: DOMAIN,
            CONF_DEVICE_ID: device_id,
            CONF_TYPE: t,
        }
        for t in TRIGGER_TYPES
    ]

    return triggers


async def async_attach_trigger(
    hass: HomeAssistant,
    config: ConfigType,
    action: TriggerActionType,
    trigger_info: TriggerInfo,
) -> CALLBACK_TYPE:
    """Attach a trigger."""

    device_registry = dr.async_get(hass)

    device = device_registry.async_get(config[CONF_DEVICE_ID])

    if device is None:
        return None

    device_name = device.name

    if config[CONF_TYPE] == "notifications_mqtt":
        mqtt_config = {
            CONF_PLATFORM: "mqtt",
            CONF_TOPIC: f"hass.agent/notifications/{device_name}/actions",
            CONF_ENCODING: DEFAULT_ENCODING,
            CONF_QOS: 0,
            CONF_PAYLOAD: config[CONF_ACTION],
            CONF_VALUE_TEMPLATE: "{{ value_json.action }}",
        }

        mqtt_config = mqtt_trigger.TRIGGER_SCHEMA(mqtt_config)

        return await mqtt_trigger.async_attach_trigger(
            hass,
            mqtt_config,
            action,
            trigger_info,
        )

    event_config = event_trigger.TRIGGER_SCHEMA(
        {
            event_trigger.CONF_PLATFORM: CONF_EVENT,
            event_trigger.CONF_EVENT_TYPE: "hass_agent_notifications",
            event_trigger.CONF_EVENT_DATA: {
                CONF_DEVICE_NAME: device_name,
                CONF_ACTION: config[CONF_ACTION],
            },
        }
    )

    return await event_trigger.async_attach_trigger(
        hass, event_config, action, trigger_info, platform_type="device"
    )


async def async_get_trigger_capabilities(
    hass: HomeAssistant, config: ConfigType
) -> dict[str, vol.Schema]:
    """List trigger capabilities."""
    return {"extra_fields": vol.Schema({vol.Required(CONF_ACTION): str})}
