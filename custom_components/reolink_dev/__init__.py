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
from homeassistant.core import HomeAssistant, Event
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .base import ReolinkBase, ReolinkPush
from .const import (
    BASE,
    CONF_CHANNEL,
    CONF_USE_HTTPS,
    CONF_MOTION_OFF_DELAY,
    CONF_PLAYBACK_MONTHS,
    CONF_PROTOCOL,
    CONF_STREAM,
    CONF_THUMBNAIL_PATH,
    CONF_STREAM_FORMAT,
    CONF_MOTION_STATES_UPDATE_FALLBACK_DELAY,
    COORDINATOR,
    MOTION_UPDATE_COORDINATOR,
    DOMAIN,
    EVENT_DATA_RECEIVED,
    PUSH_MANAGER,
    SERVICE_PTZ_CONTROL,
    SERVICE_QUERY_VOD,
    SERVICE_SET_DAYNIGHT,
    SERVICE_SET_SENSITIVITY,
)

SCAN_INTERVAL = timedelta(minutes=1)


_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["camera", "switch", "binary_sensor", "sensor"]


async def async_setup(
    hass: HomeAssistant, config: dict
):  # pylint: disable=unused-argument
    """Set up the Reolink component."""
    hass.data.setdefault(DOMAIN, {})

    # ensure default storage path is writable by scripts
    default_thumbnail_path = hass.config.path(f"{STORAGE_DIR}/{DOMAIN}")
    if default_thumbnail_path not in hass.config.allowlist_external_dirs:
        hass.config.allowlist_external_dirs.add(default_thumbnail_path)

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Reolink from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    base = ReolinkBase(hass, entry.data, entry.options)
    base.sync_functions.append(entry.add_update_listener(update_listener))

    try:
        if not await base.connect_api():
            raise ConfigEntryNotReady(f"Error while trying to setup {base.name}, API failed to provide required data")
    except:
        raise ConfigEntryNotReady(f"Error while trying to setup {base.name}, API had hard error")

    hass.data[DOMAIN][entry.entry_id] = {BASE: base}

    try:
        """Get a push manager, there should be one push manager per mac address"""
        push = hass.data[DOMAIN][base.push_manager]
    except KeyError:
        push = ReolinkPush(
            hass,
            base.api.host,
            base.api.onvif_port,
            entry.data[CONF_USERNAME],
            entry.data[CONF_PASSWORD],
        )
        await push.subscribe(base.event_id)
        hass.data[DOMAIN][base.push_manager] = push

    async def async_update_data():
        """Perform the actual updates."""

        async with async_timeout.timeout(base.timeout):
            await push.renew()
            await base.update_states()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="reolink.{}".format(base.name),
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator.async_refresh()

    async def async_update_motion_states():
        """Perform motion state updates in case webhooks are not functional"""
        # _LOGGER.debug("Refreshing motion states for camera ({}/{})".format(base.name, base.api.host))

        async with async_timeout.timeout(base.timeout):
            # Force a refresh of motion sensors (in case Webhook is broken)
            if base.sensor_motion_detection is not None:
                # hass.bus.async_fire(base.event_id, {"motion": False})
                await base.sensor_motion_detection.handle_event(Event(base.event_id, {"motion": True}))

    coordinator_motion_update = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="reolink.{}.motion_states".format(base.name),
        update_method=async_update_motion_states,
        update_interval=timedelta(seconds=base.motion_states_update_fallback_delay),
    )

    # Fetch initial data so we have data when entities subscribe
    await coordinator_motion_update.async_refresh()

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )

    hass.data[DOMAIN][entry.entry_id][COORDINATOR] = coordinator
    hass.data[DOMAIN][entry.entry_id][MOTION_UPDATE_COORDINATOR] = coordinator_motion_update

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, base.stop())

    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Update the configuration at the base entity and API."""
    base: ReolinkBase = hass.data[DOMAIN][entry.entry_id][BASE]

    base.motion_off_delay = entry.options[CONF_MOTION_OFF_DELAY]
    base.playback_months = entry.options[CONF_PLAYBACK_MONTHS]

    base.set_thumbnail_path(entry.options.get(CONF_THUMBNAIL_PATH))
    await base.set_timeout(entry.options[CONF_TIMEOUT])
    await base.set_protocol(entry.options[CONF_PROTOCOL])
    await base.set_stream(entry.options[CONF_STREAM])
    await base.set_stream_format(entry.options[CONF_STREAM_FORMAT])

    motion_state_coordinator: DataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id][MOTION_UPDATE_COORDINATOR]

    base.motion_states_update_fallback_delay = entry.options[CONF_MOTION_STATES_UPDATE_FALLBACK_DELAY]

    if motion_state_coordinator.update_interval != base.motion_states_update_fallback_delay:
        if base.motion_states_update_fallback_delay is None or base.motion_states_update_fallback_delay <= 0:
            # _LOGGER.debug("Motion state fallback delay disabled".format(motion_state_coordinator.update_interval))
            motion_state_coordinator.update_interval = None
        else:
            motion_state_coordinator.update_interval = timedelta(seconds=base.motion_states_update_fallback_delay)
            # _LOGGER.debug("Motion state fallback delay changed to {}".format(motion_state_coordinator.update_interval))
            await motion_state_coordinator.async_refresh()
    else:
        # _LOGGER.debug("Motion state fallback delay is unchanged ({})".format(motion_state_coordinator.update_interval))
        pass


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    base = hass.data[DOMAIN][entry.entry_id][BASE]
    push = hass.data[DOMAIN][base.push_manager]

    if not await push.count_members() > 1:
        await push.unsubscribe()
        hass.data[DOMAIN].pop(base.push_manager)

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
        hass.services.async_remove(DOMAIN, SERVICE_QUERY_VOD)

    return unload_ok
