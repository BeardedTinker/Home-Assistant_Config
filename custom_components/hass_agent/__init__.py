"""The HASS.Agent integration."""
from __future__ import annotations
import json
import logging
import requests
from .views import MediaPlayerThumbnailView
from homeassistant.helpers import device_registry as dr
from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.components.mqtt.subscription import (
    async_prepare_subscribe_topics,
    async_subscribe_topics,
    async_unsubscribe_topics,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ID, CONF_NAME, CONF_URL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import discovery

from .const import DOMAIN

PLATFORMS: list[Platform] = [Platform.MEDIA_PLAYER]

_logger = logging.getLogger(__name__)


def update_device_info(hass: HomeAssistant, entry: ConfigEntry, new_device_info):
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.unique_id)},
        name=new_device_info["device"]["name"],
        manufacturer=new_device_info["device"]["manufacturer"],
        model=new_device_info["device"]["model"],
        sw_version=new_device_info["device"]["sw_version"],
    )


async def handle_apis_changed(hass: HomeAssistant, entry: ConfigEntry, apis):
    if apis is not None:

        device_registry = dr.async_get(hass)
        device = device_registry.async_get_device(
            identifiers={(DOMAIN, entry.unique_id)}
        )

        media_player = apis.get("media_player", False)
        is_media_player_loaded = hass.data[DOMAIN][entry.entry_id]["loaded"][
            "media_player"
        ]

        notifications = apis.get("notifications", False)

        is_notifications_loaded = hass.data[DOMAIN][entry.entry_id]["loaded"][
            "notifications"
        ]

        if media_player and is_media_player_loaded is False:
            _logger.debug("loading media_player for device: %s", device.name)
            await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

            hass.data[DOMAIN][entry.entry_id]["loaded"]["media_player"] = True
        else:
            if is_media_player_loaded:
                _logger.debug(
                    "unloading media_player for device: %s",
                    device.name,
                )
                await hass.config_entries.async_forward_entry_unload(
                    entry, Platform.MEDIA_PLAYER
                )

                hass.data[DOMAIN][entry.entry_id]["loaded"]["media_player"] = False

        if notifications and is_notifications_loaded is False:
            _logger.debug("loading notify for device: %s", device.name)

            hass.async_create_task(
                discovery.async_load_platform(
                    hass,
                    Platform.NOTIFY,
                    DOMAIN,
                    {CONF_ID: entry.entry_id, CONF_NAME: device.name},
                    {},
                )
            )
            hass.data[DOMAIN][entry.entry_id]["loaded"]["notifications"] = True
        else:
            if is_notifications_loaded:
                _logger.debug("unloading notify for device: %s", device.name)
                await hass.config_entries.async_unload_platforms(
                    entry, [Platform.NOTIFY]
                )

                hass.data[DOMAIN][entry.entry_id]["loaded"]["notifications"] = False


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HASS.Agent from a config entry."""

    hass.data.setdefault(DOMAIN, {})

    hass.data[DOMAIN].setdefault(
        entry.entry_id,
        {
            "internal_mqtt": {},
            "apis": {},
            "thumbnail": None,
            "loaded": {"media_player": False, "notifications": False},
        },
    )

    url = entry.data.get(CONF_URL, None)

    if url is not None:

        def get_device_info():
            return requests.get(f"{url}/info", timeout=10)

        response = await hass.async_add_executor_job(get_device_info)

        response_json = response.json()

        update_device_info(hass, entry, response_json)

        apis = {
            "notifications": True,
            "media_player": False,  # unsupported for the moment
        }

        hass.async_create_task(handle_apis_changed(hass, entry, apis))
        hass.data[DOMAIN][entry.entry_id]["apis"] = apis

    else:
        device_name = entry.data["device"]["name"]

        sub_state = hass.data[DOMAIN][entry.entry_id]["internal_mqtt"]

        def updated(message: ReceiveMessage):
            payload = json.loads(message.payload)
            cached = hass.data[DOMAIN][entry.entry_id]["apis"]
            apis = payload["apis"]

            update_device_info(hass, entry, payload)

            if cached != apis:
                hass.async_create_task(handle_apis_changed(hass, entry, apis))
                hass.data[DOMAIN][entry.entry_id]["apis"] = apis

        sub_state = async_prepare_subscribe_topics(
            hass,
            sub_state,
            {
                f"{entry.unique_id}-apis": {
                    "topic": f"hass.agent/devices/{device_name}",
                    "msg_callback": updated,
                    "qos": 0,
                }
            },
        )

        await async_subscribe_topics(hass, sub_state)

        hass.data[DOMAIN][entry.entry_id]["internal_mqtt"] = sub_state

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""

    # known issue: notify does not always unload

    loaded = hass.data[DOMAIN][entry.entry_id].get("loaded", None)

    if loaded is not None:
        notifications = loaded.get("notifications", False)

        media_player = loaded.get("media_player", False)

        if notifications:
            if unload_ok := await hass.config_entries.async_unload_platforms(
                entry, [Platform.NOTIFY]
            ):
                _logger.debug("unloaded %s for %s", "notify", entry.unique_id)

        if media_player:
            if unload_ok := await hass.config_entries.async_unload_platforms(
                entry, [Platform.MEDIA_PLAYER]
            ):
                _logger.debug("unloaded %s for %s", "media_player", entry.unique_id)
    else:
        _logger.warning("config entry (%s) with has no apis loaded?", entry.entry_id)

    url = entry.data.get(CONF_URL, None)
    if url is None:
        async_unsubscribe_topics(
            hass, hass.data[DOMAIN][entry.entry_id]["internal_mqtt"]
        )

    hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_setup(hass: HomeAssistant, config) -> bool:
    hass.http.register_view(MediaPlayerThumbnailView(hass))
    return True
