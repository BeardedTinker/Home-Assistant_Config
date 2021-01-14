"""Reolink integration for HomeAssistant."""
import asyncio
from datetime import timedelta
import logging

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
from homeassistant.helpers import device_registry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .base import ReolinkBase, ReolinkPush
from .const import (
    BASE,
    CONF_CHANNEL,
    CONF_MOTION_OFF_DELAY,
    CONF_PROTOCOL,
    CONF_STREAM,
    COORDINATOR,
    DOMAIN,
    EVENT_DATA_RECEIVED,
    PUSH_MANAGER,
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
    hass.data[DOMAIN][entry.entry_id] = {BASE: base}

    try:
        """Get a push manager, there should be one push manager per mac address"""
        push = hass.data[DOMAIN][entry.entry_id][base.push_manager]
    except KeyError:
        push = ReolinkPush(hass, base.api.host, base.api.onvif_port, entry.data[CONF_USERNAME], entry.data[CONF_PASSWORD])
        await push.subscribe(base.event_id)
        hass.data[DOMAIN][entry.entry_id][base.push_manager] = push

    async def async_update_data():
        """Perform the actual updates."""

        async with async_timeout.timeout(base.timeout):
            await push.renew()
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


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    base = hass.data[DOMAIN][entry.entry_id][BASE]
    push = hass.data[DOMAIN][entry.entry_id][base.push_manager]

    keep_subscription = False
    for entry_id in hass.data[DOMAIN]:
        if entry_id == entry.entry_id:
            continue
        _LOGGER.debug(entry_id)
        
        base_entry = hass.data[DOMAIN][entry_id][BASE]
        _LOGGER.debug(base_entry.event_id)

        if base_entry.event_id == base.event_id and base_entry.unique_id != base.unique_id:
            keep_subscription = True
            break

    if not keep_subscription:
        push.unsubscribe()

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
