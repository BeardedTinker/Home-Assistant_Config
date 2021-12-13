"""This component provides support for Reolink IP cameras."""
from datetime import datetime
import logging
from typing import Union

import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.components.camera import SUPPORT_STREAM, Camera
from homeassistant.components.ffmpeg import DATA_FFMPEG

from homeassistant.helpers import config_validation as cv, entity_platform

from .const import (
    DOMAIN_DATA,
    LAST_EVENT,
    SERVICE_PTZ_CONTROL,
    SERVICE_QUERY_VOD,
    SERVICE_SET_BACKLIGHT,
    SERVICE_SET_DAYNIGHT,
    SERVICE_SET_SENSITIVITY,
    SUPPORT_PLAYBACK,
    SUPPORT_PTZ,
)
from .entity import ReolinkEntity
from .typings import VoDEvent

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_devices):
    """Set up a Reolink IP Camera."""

    platform = entity_platform.current_platform.get()
    camera = ReolinkCamera(hass, config_entry)

    platform.async_register_entity_service(
        SERVICE_SET_SENSITIVITY,
        {
            vol.Required("sensitivity"): cv.positive_int,
            vol.Optional("preset"): cv.positive_int,
        },
        SERVICE_SET_SENSITIVITY,
    )

    platform.async_register_entity_service(
        SERVICE_SET_DAYNIGHT,
        {
            vol.Required("mode"): cv.string,
        },
        SERVICE_SET_DAYNIGHT,
    )

    platform.async_register_entity_service(
        SERVICE_SET_BACKLIGHT,
        {
            vol.Required("mode"): cv.string,
        },
        SERVICE_SET_BACKLIGHT,
    )

    platform.async_register_entity_service(
        SERVICE_PTZ_CONTROL,
        {
            vol.Required("command"): cv.string,
            vol.Optional("preset"): cv.positive_int,
            vol.Optional("speed"): cv.positive_int,
        },
        SERVICE_PTZ_CONTROL,
        [SUPPORT_PTZ],
    )
    platform.async_register_entity_service(
        SERVICE_QUERY_VOD,
        {
            vol.Required("event_id"): cv.string,
            vol.Optional("start"): cv.datetime,
            vol.Optional("end"): cv.datetime,
        },
        SERVICE_QUERY_VOD,
        [SUPPORT_PLAYBACK],
    )

    async_add_devices([camera])


class ReolinkCamera(ReolinkEntity, Camera):
    """An implementation of a Reolink IP camera."""

    def __init__(self, hass, config):
        """Initialize a Reolink camera."""
        ReolinkEntity.__init__(self, hass, config)
        Camera.__init__(self)
        self._entry_id = config.entry_id

        self._ffmpeg = self._hass.data[DATA_FFMPEG]
        # self._last_image = None
        self._ptz_commands = {
            "AUTO": "Auto",
            "DOWN": "Down",
            "FOCUSDEC": "FocusDec",
            "FOCUSINC": "FocusInc",
            "LEFT": "Left",
            "LEFTDOWN": "LeftDown",
            "LEFTUP": "LeftUp",
            "RIGHT": "Right",
            "RIGHTDOWN": "RightDown",
            "RIGHTUP": "RightUp",
            "STOP": "Stop",
            "TOPOS": "ToPos",
            "UP": "Up",
            "ZOOMDEC": "ZoomDec",
            "ZOOMINC": "ZoomInc",
        }
        self._daynight_modes = {
            "AUTO": "Auto",
            "COLOR": "Color",
            "BLACKANDWHITE": "Black&White",
        }

        self._backlight_modes = {
            "BACKLIGHTCONTROL": "BackLightControl",
            "DYNAMICRANGECONTROL": "DynamicRangeControl",
            "OFF": "Off",
        }

    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"reolink_camera_{self._base.unique_id}"

    @property
    def name(self):
        """Return the name of this camera."""
        return self._base.name

    @property
    def ptz_support(self):
        """Return whether the camera has PTZ support."""
        return self._base.api.ptz_support

    @property
    def playback_support(self):
        """ Return whethere the camera has VoDs. """
        # TODO : this should probably be like ptz above, and be a property of the api
        return bool(self._base.api.hdd_info)

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attrs = super().extra_state_attributes
        if attrs is None:
            attrs = {}

        if self._base.api.ptz_support:
            attrs["ptz_presets"] = self._base.api.ptz_presets

        for key, value in self._backlight_modes.items():
            if value == self._base.api.backlight_state:
                attrs["backlight_state"] = key

        for key, value in self._daynight_modes.items():
            if value == self._base.api.daynight_state:
                attrs["daynight_state"] = key

        if self._base.api.sensitivity_presets:
            attrs["sensitivity"] = self.get_sensitivity_presets()

        if self.playback_support:
            data: dict = self.hass.data.get(DOMAIN_DATA)
            data = data.get(self._base.unique_id) if data else None
            last: VoDEvent = data.get(LAST_EVENT) if data else None
            if last and last.url:
                attrs["video_url"] = last.url
                if last.thumbnail and last.thumbnail.exists:
                    attrs["video_thumbnail"] = last.thumbnail.url

        return attrs

    @property
    def supported_features(self):
        """Return supported features."""
        features = SUPPORT_STREAM
        if self.ptz_support:
            features += SUPPORT_PTZ
        if self.playback_support:
            features += SUPPORT_PLAYBACK
        return features

    async def stream_source(self):
        """Return the source of the stream."""
        return await self._base.api.get_stream_source()

    async def async_camera_image(
        self, width: Union[int, None] = None, height: Union[int, None] = None
    ) -> Union[bytes, None]:
        """Return a still image response from the camera."""
        return await self._base.api.get_snapshot()

    async def ptz_control(self, command, **kwargs):
        """Pass PTZ command to the camera."""
        if not self.ptz_support:
            _LOGGER.error("PTZ is not supported on this device")
            return

        await self._base.api.set_ptz_command(
            command=self._ptz_commands[command], **kwargs
        )

    async def query_vods(self, event_id, **kwargs):
        """ Query camera for VoDs and emit results """
        if not self.playback_support:
            _LOGGER.error("Video Playback is not supported on this device")
            return

        await self._base.emit_search_results(
            event_id, self._entry_id, context=self._context, **kwargs
        )

    def get_sensitivity_presets(self):
        """Get formatted sensitivity presets."""
        presets = list()
        preset = dict()

        for api_preset in self._base.api.sensitivity_presets:
            preset["id"] = api_preset["id"]
            preset["sensitivity"] = api_preset["sensitivity"]

            time_string = f'{api_preset["beginHour"]}:{api_preset["beginMin"]}'
            begin = datetime.strptime(time_string, "%H:%M")
            preset["begin"] = begin.strftime("%H:%M")

            time_string = f'{api_preset["endHour"]}:{api_preset["endMin"]}'
            end = datetime.strptime(time_string, "%H:%M")
            preset["end"] = end.strftime("%H:%M")

            presets.append(preset.copy())

        return presets

    async def set_sensitivity(self, sensitivity, **kwargs):
        """Set the sensitivity to the camera."""
        if "preset" in kwargs:
            kwargs["preset"] += 1  # The camera preset ID's on the GUI are always +1
        await self._base.api.set_sensitivity(value=sensitivity, **kwargs)

    async def set_daynight(self, mode):
        """Set the day and night mode to the camera."""
        await self._base.api.set_daynight(value=self._daynight_modes[mode])

    async def set_backlight(self, mode):
        """Set the backlight mode to the camera."""
        await self._base.api.set_backlight(value=self._backlight_modes[mode])

    async def async_enable_motion_detection(self):
        """Predefined camera service implementation."""
        self._base.motion_detection_state = True

    async def async_disable_motion_detection(self):
        """Predefined camera service implementation."""
        self._base.motion_detection_state = False
