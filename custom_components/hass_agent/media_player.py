from __future__ import annotations
import json

import logging
import time
from typing import Any
from homeassistant import util

from homeassistant.components.mqtt.models import ReceiveMessage
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN


from homeassistant.components.mqtt.subscription import (
    async_prepare_subscribe_topics,
    async_subscribe_topics,
    async_unsubscribe_topics,
)
from homeassistant.config_entries import ConfigEntry

from homeassistant.components.media_player import (
    MediaPlayerDeviceClass,
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
)

from homeassistant.components.media_player.const import MEDIA_TYPE_MUSIC

from homeassistant.components.media_player.browse_media import (
    BrowseMedia,
    async_process_play_media_url,
)

from homeassistant.const import (
    STATE_IDLE,
    STATE_OFF,
    STATE_PAUSED,
    STATE_PLAYING,
)

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.components import media_source, mqtt

_logger = logging.getLogger(__name__)

SUPPORT_HAMP = (
    MediaPlayerEntityFeature.VOLUME_MUTE
    | MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PLAY_MEDIA
    | MediaPlayerEntityFeature.SEEK
    | MediaPlayerEntityFeature.BROWSE_MEDIA
    | MediaPlayerEntityFeature.VOLUME_SET
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> bool:
    device_registry = dr.async_get(hass)
    device = device_registry.async_get_device(identifiers={(DOMAIN, entry.unique_id)})

    if device is None:
        return False

    async_add_entities(
        [HassAgentMediaPlayerDevice(entry.unique_id, entry.entry_id, device)]
    )

    return True


class HassAgentMediaPlayerDevice(MediaPlayerEntity):
    """HASS.Agent MediaPlayer Device"""

    @callback
    def update_thumbnail(self, message: ReceiveMessage):
        self.hass.data[DOMAIN][self._entry_id]["thumbnail"] = message.payload

        self._attr_media_image_url = (
            f"/api/hass_agent/{self.entity_id}/thumbnail.png?time={time.time()}"
        )

    @property
    def media_image_local(self) -> str | None:
        return self._attr_media_image_url

    @callback
    def updated(self, message: ReceiveMessage):
        """Updates the media player with new data from MQTT"""
        payload = json.loads(message.payload)

        self._state = payload["state"].lower()
        self._volume_level = payload["volume"]
        self._muted = payload["muted"]
        self._available = True

        if self._state != "off":
            self._attr_media_album_artist = payload["albumartist"]
            self._attr_media_album_name = payload["albumtitle"]
            self._attr_media_artist = payload["artist"]
            self._attr_media_title = payload["title"]

            self._attr_media_duration = payload["duration"]
            self._attr_media_position = payload["currentposition"]

            self._attr_media_position_updated_at = util.dt.utcnow()

        self._last_updated = time.time()

        # self.media_image_url

        self.async_write_ha_state()

    async def async_added_to_hass(self) -> None:
        self._listeners = async_prepare_subscribe_topics(
            self.hass,
            self._listeners,
            {
                f"{self._attr_unique_id}-state": {
                    "topic": f"hass.agent/media_player/{self._attr_device_info['name']}/state",
                    "msg_callback": self.updated,
                    "qos": 0,
                },
                f"{self._attr_unique_id}-thumbnail": {
                    "topic": f"hass.agent/media_player/{self._attr_device_info['name']}/thumbnail",
                    "msg_callback": self.update_thumbnail,
                    "qos": 0,
                    "encoding": None,
                },
            },
        )

        await async_subscribe_topics(self.hass, self._listeners)

    async def async_will_remove_from_hass(self) -> None:
        if self._listeners is not None:
            async_unsubscribe_topics(self.hass, self._listeners)

    def __init__(self, unique_id, entry_id, device: dr.DeviceEntry):
        """Initialize"""
        self._entry_id = entry_id
        self._name = device.name
        self._attr_device_info = {
            "identifiers": device.identifiers,
            "name": device.name,
            "manufacturer": device.manufacturer,
            "model": device.model,
            "sw_version": device.sw_version,
        }
        self._command_topic = f"hass.agent/media_player/{device.name}/cmd"
        self._attr_unique_id = f"media_player_{unique_id}"
        self._available = False
        self._muted = False
        self._volume_level = 0
        self._playing = ""
        self._state = ""

        self._listeners = {}
        self._last_updated = 0

    async def _send_command(self, command, data=None):
        """Send a command"""
        _logger.debug("Sending command: %s", command)

        payload = {"command": command, "data": data}

        await mqtt.async_publish(self.hass, self._command_topic, json.dumps(payload))

    @property
    def name(self):
        """Return the name of the device"""
        return self._name

    @property
    def state(self):
        """Return the state of the device"""
        if self._state is None:
            return STATE_OFF
        if self._state == "idle":
            return STATE_IDLE
        if self._state == "playing":
            return STATE_PLAYING
        if self._state == "paused":
            return STATE_PAUSED

        return STATE_IDLE

    @property
    def available(self):
        """Return if we're available"""

        diff = round(time.time() - self._last_updated)
        return diff < 5

    # @property
    # def media_title(self):
    #     """Return the title of current playing media"""
    #     return self._playing

    @property
    def volume_level(self):
        """Return the volume level of the media player (0..1)"""
        return self._volume_level / 100.0
        
    async def async_set_volume_level(self, volume: float) -> None:
        """Send new volume_level to device."""
        volume = round(volume * 100)
        await self._send_command("setvolume", volume)

    @property
    def is_volume_muted(self):
        """Return if volume is currently muted"""
        return self._muted

    @property
    def supported_features(self):
        """Flag media player features that are supported"""
        return SUPPORT_HAMP

    @property
    def device_class(self):
        """Announce ourselve as a speaker"""
        return MediaPlayerDeviceClass.SPEAKER

    @property
    def media_content_type(self):
        """Content type of current playing media"""
        return MEDIA_TYPE_MUSIC

    async def async_media_seek(self, position: float) -> None:
        self._attr_media_position = position
        self._attr_media_position_updated_at = util.dt.utcnow()
        await self._send_command("seek", position)

    async def async_volume_up(self):
        """Volume up the media player"""
        await self._send_command("volumeup")

    async def async_volume_down(self):
        """Volume down media player"""
        await self._send_command("volumedown")

    async def async_mute_volume(self, mute):
        """Mute the volume"""
        await self._send_command("mute")

    async def async_media_play(self):
        """Send play command"""
        self._state = STATE_PLAYING
        await self._send_command("play")

    async def async_media_pause(self):
        """Send pause command"""
        self._state = STATE_PAUSED
        await self._send_command("pause")

    async def async_media_stop(self):
        """Send stop command"""
        self._state = STATE_PAUSED
        await self._send_command("stop")

    async def async_media_next_track(self):
        """Send next track command"""
        await self._send_command("next")

    async def async_media_previous_track(self):
        """Send previous track command"""
        await self._send_command("previous")

    async def async_browse_media(
        self, media_content_type: str | None = None, media_content_id: str | None = None
    ) -> BrowseMedia:
        """Implement the websocket media browsing helper."""
        # If your media player has no own media sources to browse, route all browse commands
        # to the media source integration.
        return await media_source.async_browse_media(
            self.hass,
            media_content_id,
            # This allows filtering content. In this case it will only show audio sources.
            content_filter=lambda item: item.media_content_type.startswith("audio/"),
        )

    async def async_play_media(self, media_type: str, media_id: str, **kwargs: Any):
        """Play media source"""
        if not media_type.startswith("music") and not media_type.startswith("audio/") and not media_type.startswith("provider"):
            _logger.error(
                "Invalid media type %r. Only %s is supported!",
                media_type,
                MEDIA_TYPE_MUSIC,
            )
            return

        if media_source.is_media_source_id(media_id):
            play_item = await media_source.async_resolve_media(self.hass, media_id)

            # play_item returns a relative URL if it has to be resolved on the Home Assistant host
            # This call will turn it into a full URL
            media_id = async_process_play_media_url(self.hass, play_item.url)

        _logger.debug("Received media request from HA: %s", media_id)

        self._state = STATE_PLAYING
        await self._send_command("playmedia", media_id)
