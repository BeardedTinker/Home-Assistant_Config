from typing import Mapping, Any
import voluptuous as vol
import homeassistant.helpers.config_validation as cv

from growcube_client import Channel, WateringMode

from homeassistant.const import ATTR_DEVICE_ID
from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr

from . import GrowcubeDataCoordinator
from .const import DOMAIN, CHANNEL_NAME, SERVICE_WATER_PLANT, SERVICE_SET_SMART_WATERING, \
    SERVICE_SET_SCHEDULED_WATERING, SERVICE_DELETE_WATERING, \
    ARGS_CHANNEL, ARGS_DURATION, ARGS_MIN_MOISTURE, ARGS_MAX_MOISTURE, ARGS_ALL_DAY, ARGS_INTERVAL
import logging

_LOGGER = logging.getLogger(__name__)

@callback
async def async_setup_services(hass):

    async def async_call_water_plant_service(service_call: ServiceCall) -> None:
        await _async_handle_water_plant(hass, service_call.data)

    async def async_call_set_smart_watering_service(service_call: ServiceCall) -> None:
        await _async_handle_set_smart_watering(hass, service_call.data)

    async def async_call_set_scheduled_watering_service(service_call: ServiceCall) -> None:
        await _async_handle_set_scheduled_watering(hass, service_call.data)

    async def async_call_delete_watering_service(service_call: ServiceCall) -> None:
        await _async_handle_delete_watering(hass, service_call.data)

    hass.services.async_register(DOMAIN,
                                 SERVICE_WATER_PLANT,
                                 async_call_water_plant_service,
                                 schema=vol.Schema(
                                     {
                                         vol.Required(ATTR_DEVICE_ID): cv.string,
                                         vol.Required(ARGS_CHANNEL, default='A'): cv.string,
                                         vol.Required(ARGS_DURATION, default=5): cv.positive_int,
                                     }
                                 ))
    hass.services.async_register(DOMAIN,
                                 SERVICE_SET_SMART_WATERING,
                                 async_call_set_smart_watering_service,
                                 schema=vol.Schema(
                                     {
                                         vol.Required(ATTR_DEVICE_ID): cv.string,
                                         vol.Required(ARGS_CHANNEL, default='A'): cv.string,
                                         vol.Required(ARGS_ALL_DAY, default=True): cv.boolean,
                                         vol.Required(ARGS_MIN_MOISTURE, default=15): cv.positive_int,
                                         vol.Required(ARGS_MAX_MOISTURE, default=40): cv.positive_int,
                                     }
                                 ))
    hass.services.async_register(DOMAIN,
                                 SERVICE_SET_SCHEDULED_WATERING,
                                 async_call_set_scheduled_watering_service,
                                 schema=vol.Schema(
                                     {
                                         vol.Required(ATTR_DEVICE_ID): cv.string,
                                         vol.Required(ARGS_CHANNEL, default='A'): cv.string,
                                         vol.Required(ARGS_DURATION, default=6): cv.positive_int,
                                         vol.Required(ARGS_INTERVAL, default=3): cv.positive_int,
                                     }
                                 ))
    hass.services.async_register(DOMAIN,
                                 SERVICE_DELETE_WATERING,
                                 async_call_delete_watering_service,
                                 schema=vol.Schema(
                                     {
                                         vol.Required(ATTR_DEVICE_ID): cv.string,
                                         vol.Required(ARGS_CHANNEL, default='A'): cv.string,
                                     }
                                 ))


async def _async_handle_water_plant(hass: HomeAssistant, data: Mapping[str, Any]) -> None:

    coordinator, device = _get_coordinator(hass, data)

    if coordinator is None:
        _LOGGER.warning(f"Unable to find coordinator for {data[ATTR_DEVICE_ID]}")
        return

    channel_str = data["channel"]
    duration_str = data["duration"]

    # Validate data
    if channel_str not in CHANNEL_NAME:
        _LOGGER.error(
            "%s: %s - Invalid channel specified: %s",
            id,
            SERVICE_WATER_PLANT,
            channel_str
        )
        raise HomeAssistantError(f"Invalid channel '{channel_str}' specified")

    try:
        duration = int(duration_str)
    except ValueError:
        _LOGGER.error(
            "%s: %s - Invalid duration '%s'",
            id,
            SERVICE_WATER_PLANT,
            duration_str
        )
        raise HomeAssistantError(f"Invalid duration '{duration_str} specified'")

    if duration < 1 or duration > 60:
        _LOGGER.error(
            "%s: %s - Invalid duration '%s', should be 1-60",
            id,
            SERVICE_WATER_PLANT,
            duration
        )
        raise HomeAssistantError(f"Invalid duration '{duration}' specified, should be 1-60")

    channel = Channel(CHANNEL_NAME.index(channel_str))

    await coordinator.handle_water_plant(channel, duration)


async def _async_handle_set_smart_watering(hass: HomeAssistant, data: Mapping[str, Any]) -> None:

    coordinator, device = _get_coordinator(hass, data)

    if coordinator is None:
        _LOGGER.error(f"Unable to find coordinator for {device}")
        return

    channel_str = data[ARGS_CHANNEL]
    min_moisture = data[ARGS_MIN_MOISTURE]
    max_moisture = data[ARGS_MAX_MOISTURE]
    all_day = data[ARGS_ALL_DAY]

    # Validate data
    if channel_str not in CHANNEL_NAME:
        _LOGGER.error(
            "%s: %s - Invalid channel specified: %s",
            device,
            SERVICE_SET_SMART_WATERING,
            channel_str
        )
        raise HomeAssistantError(f"Invalid channel '{channel_str}' specified")

    if min_moisture <= 0 or min_moisture > 100:
        _LOGGER.error(
            "%s: %s - Invalid min_moisture specified: %s",
            device,
            SERVICE_SET_SMART_WATERING,
            min_moisture
        )
        raise HomeAssistantError(f"Invalid min_moisture '{min_moisture}' specified")

    if max_moisture <= 0 or max_moisture > 100:
        _LOGGER.error(
            "%s: %s - Invalid max_moisture specified: %s",
            device,
            SERVICE_SET_SMART_WATERING,
            max_moisture
        )
        raise HomeAssistantError(f"Invalid max_moisture '{max_moisture}' specified")

    if max_moisture <= min_moisture:
        _LOGGER.error(
            "%s: %s - Invalid values specified, max_moisture %s must be bigger than min_moisture %s",
            device,
            SERVICE_SET_SMART_WATERING,
            min_moisture,
            max_moisture
        )
        raise HomeAssistantError(
            f"Invalid values specified, max_moisture {max_moisture} must be bigger than min_moisture {min_moisture}")

    channel = Channel(CHANNEL_NAME.index(channel_str))
    await coordinator.handle_set_smart_watering(channel, all_day, min_moisture, max_moisture)


async def _async_handle_set_scheduled_watering(hass: HomeAssistant, data: Mapping[str, Any]) -> None:

    coordinator, device = _get_coordinator(hass, data)

    if coordinator is None:
        _LOGGER.error(f"Unable to find coordinator for {device}")
        return

    channel_str = data[ARGS_CHANNEL]
    duration = data[ARGS_DURATION]
    interval = data[ARGS_INTERVAL]

    # Validate data
    if channel_str not in CHANNEL_NAME:
        _LOGGER.error(
            "%s: %s - Invalid channel specified: %s",
            device,
            SERVICE_SET_SMART_WATERING,
            channel_str
        )
        raise HomeAssistantError(f"Invalid channel '{channel_str}' specified")

    if duration <= 0 or duration > 100:
        _LOGGER.error(
            "%s: %s - Invalid duration specified: %s",
            device,
            SERVICE_SET_SMART_WATERING,
            duration
        )
        raise HomeAssistantError(f"Invalid duration '{duration}' specified")

    if interval <= 0 or interval > 240:
        _LOGGER.error(
            "%s: %s - Invalid interval specified: %s",
            device,
            SERVICE_SET_SMART_WATERING,
            interval
        )
        raise HomeAssistantError(f"Invalid interval '{interval}' specified")

    channel = Channel(CHANNEL_NAME.index(channel_str))
    await coordinator.handle_set_manual_watering(channel, duration, interval)


async def _async_handle_delete_watering(hass: HomeAssistant, data: Mapping[str, Any]) -> None:

    coordinator, device = _get_coordinator(hass, data)

    if coordinator is None:
        raise HomeAssistantError(f"Unable to find coordinator for {device}")

    channel_str = data["channel"]

    # Validate data
    if channel_str not in CHANNEL_NAME:
        _LOGGER.error(
            "%s: %s - Invalid channel specified: %s",
            id,
            SERVICE_DELETE_WATERING,
            channel_str
        )
        raise HomeAssistantError(f"Invalid channel '{channel_str}' specified")

    channel = Channel(CHANNEL_NAME.index(channel_str))
    await coordinator.handle_delete_watering(channel)


def _get_coordinator(hass: HomeAssistant, data: Mapping[str, Any]) -> { GrowcubeDataCoordinator, str }:
    device_registry = dr.async_get(hass)
    device_id = data[ATTR_DEVICE_ID]
    device_entry = device_registry.async_get(device_id)
    device = list(device_entry.identifiers)[0][1]

    for key in hass.data[DOMAIN]:
        coordinator = hass.data[DOMAIN][key]
        if coordinator.data.device_id == device:
            return coordinator, device_id

    _LOGGER.error("No coordinator found for %s", device)
    return None, device_id
