"""This component provides support for Reolink IP cameras."""
import asyncio
from datetime import datetime
import logging

from haffmpeg.camera import CameraMjpeg
import voluptuous as vol

from homeassistant.components.camera import SUPPORT_STREAM, Camera
from homeassistant.components.ffmpeg import DATA_FFMPEG
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.aiohttp_client import (
    async_aiohttp_proxy_web,
    async_get_clientsession,
)

from .const import SERVICE_PTZ_CONTROL, SERVICE_SET_DAYNIGHT, SERVICE_SET_SENSITIVITY
from .entity import ReolinkEntity

_LOGGER = logging.getLogger(__name__)


@asyncio.coroutine
async def async_setup_entry(hass, config_entry, async_add_devices):
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
        SERVICE_PTZ_CONTROL,
        {
            vol.Required("command"): cv.string,
            vol.Optional("preset"): cv.positive_int,
            vol.Optional("speed"): cv.positive_int,
        },
        SERVICE_PTZ_CONTROL,
    )

    async_add_devices([camera])


class ReolinkCamera(ReolinkEntity, Camera):
    """An implementation of a Reolink IP camera."""

    def __init__(self, hass, config):
        """Initialize a Reolink camera."""
        ReolinkEntity.__init__(self, hass, config)
        Camera.__init__(self)

        self._hass = hass
        self._ffmpeg = self._hass.data[DATA_FFMPEG]
        self._last_image = None
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
    def device_state_attributes(self):
        """Return the camera state attributes."""
        attrs = {}
        if self._base.api.ptz_support:
            attrs["ptz_presets"] = self._base.api.ptz_presets

        for key, value in self._daynight_modes.items():
            if value == self._base.api.daynight_state:
                attrs["daynight_state"] = key

        if self._base.api.sensitivity_presets:
            attrs["sensitivity"] = self.get_sensitivity_presets()

        return attrs

    @property
    def supported_features(self):
        """Return supported features."""
        return SUPPORT_STREAM

    async def stream_source(self):
        """Return the source of the stream."""        
        return await self._base.api.get_stream_source()

    async def handle_async_mjpeg_stream(self, request):
        """Generate an HTTP MJPEG stream from the camera."""
        stream_source = await self.stream_source()

        websession = async_get_clientsession(self._hass)
        stream_coro = websession.get(stream_source, timeout=10)

        return await async_aiohttp_proxy_web(self._hass, request, stream_coro)

    async def async_camera_image(self):
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

    async def async_enable_motion_detection(self):
        """Predefined camera service implementation."""
        self._base.motion_detection_state = True

    async def async_disable_motion_detection(self):
        """Predefined camera service implementation."""
        self._base.motion_detection_state = False
