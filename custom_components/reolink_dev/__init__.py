"""Reolink integration for HomeAssistant."""
import asyncio
from datetime import timedelta
import logging
import re

import async_timeout

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_TIMEOUT,
    CONF_USERNAME,
    EVENT_HOMEASSISTANT_STOP,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.network import get_url
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .base import ReolinkBase
from .const import (
    BASE,
    CONF_CHANNEL,
    CONF_MOTION_OFF_DELAY,
    CONF_PROTOCOL,
    CONF_STREAM,
    COORDINATOR,
    DOMAIN,
    EVENT_DATA_RECEIVED,
    SERVICE_PTZ_CONTROL,
    SERVICE_SET_DAYNIGHT,
    SERVICE_SET_SENSITIVITY,
)

SCAN_INTERVAL = timedelta(minutes=1)


_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["camera", "switch", "binary_sensor"]


async def async_setup(
    hass: HomeAssistant, config: dict
):  # pylint: disable=unused-argument
    """Set up the Reolink component."""
    hass.data.setdefault(DOMAIN, {})

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Reolink from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    base = ReolinkBase(
        hass,
        entry.data,
        entry.options
    )

    base.sync_functions.append(entry.add_update_listener(update_listener))

    if not await base.connect_api():
        return False

    webhook_id = await register_webhook(hass, base.event_id)
    webhook_url = "{}{}".format(
      get_url(hass, prefer_external=False),
      hass.components.webhook.async_generate_path(webhook_id)
    )

    await base.subscribe(webhook_url)

    hass.data[DOMAIN][entry.entry_id] = {BASE: base}

    async def async_update_data():
        """Perform the actual updates."""

        async with async_timeout.timeout(base.timeout):
            await base.renew()
            await base.update_states()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="reolink",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    hass.data[DOMAIN][entry.entry_id][COORDINATOR] = coordinator

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, base.stop())

    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Update the configuration at the base entity and API."""
    base = hass.data[DOMAIN][entry.entry_id][BASE]
    
    base.motion_off_delay = entry.options[CONF_MOTION_OFF_DELAY]
    await base.set_timeout(entry.options[CONF_TIMEOUT])
    await base.set_protocol(entry.options[CONF_PROTOCOL])
    await base.set_stream(entry.options[CONF_STREAM])


async def handle_webhook(hass, webhook_id, request):
    """Handle incoming webhook from Reolink for inbound messages and calls."""
    _LOGGER.debug("Reolink webhook triggered")

    if not request.body_exists:
        _LOGGER.debug("Webhook triggered without payload")

    data = await request.text()
    if not data:
        _LOGGER.debug("Webhook triggered with unknown payload")
        return

    _LOGGER.debug(data)
    matches = re.findall(r'Name="IsMotion" Value="(.+?)"', data)
    if matches:
        is_motion = matches[0] == "true"
    else:
        _LOGGER.debug("Webhook triggered with unknown payload")
        return

    handlers = hass.data["webhook"]
    for wid, info in handlers.items():
        if wid == webhook_id:
            event_id = info["name"]
            hass.bus.async_fire(event_id, {"IsMotion": is_motion})


async def register_webhook(hass, event_id):
    """
    Register a webhook for motion events if it does not exist yet (in case of NVR).
    The webhook name (in info) contains the event id (contains mac address op the camera).
    So when motion triggers the webhook, it triggers this event. The event is handled by
    the binary sensor, in case of NVR the binary sensor also figures out what channel has
    the motion. So the flow is: camera onvif event->webhook->HA event->binary sensor.
    """
    handlers = hass.data["webhook"]
    _LOGGER.debug("Registering webhook for event ID %s", event_id)

    for webhook_id, info in handlers.items():
        _LOGGER.debug("Webhook: %s", webhook_id)
        _LOGGER.debug(info)
        if info["name"] == event_id:
            return webhook_id

    webhook_id = hass.components.webhook.async_generate_id()
    hass.components.webhook.async_register(DOMAIN, event_id, webhook_id, handle_webhook)

    return webhook_id


async def unregister_webhook(hass: HomeAssistant, event_id):
    """Unregister the webhook for motion events."""
    handlers = hass.data["webhook"]

    for webhook_id, info in handlers.items():  # ToDo: check other NVR streams still use this 
        if info["name"] == event_id:
            _LOGGER.info("Unregistering webhook %s", info.name)
            hass.components.webhook.async_unregister(webhook_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    base = hass.data[DOMAIN][entry.entry_id][BASE]

    await unregister_webhook(hass, base.event_id)
    await base.stop()

    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(entry, component)
                for component in PLATFORMS
            ]
        )
    )
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    if len(hass.data[DOMAIN]) == 0:
        hass.services.async_remove(DOMAIN, SERVICE_PTZ_CONTROL)
        hass.services.async_remove(DOMAIN, SERVICE_SET_DAYNIGHT)
        hass.services.async_remove(DOMAIN, SERVICE_SET_SENSITIVITY)

    return unload_ok
