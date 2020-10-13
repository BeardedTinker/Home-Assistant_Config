"""This component provides basic support for Reolink IP cameras."""
import logging
import asyncio
import voluptuous as vol
import datetime

from homeassistant.components.camera import Camera, PLATFORM_SCHEMA, SUPPORT_STREAM, ENTITY_IMAGE_URL
from homeassistant.const import CONF_HOST, CONF_NAME, CONF_USERNAME, CONF_PASSWORD, ATTR_ENTITY_ID, EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers import config_validation as cv

from haffmpeg.camera import CameraMjpeg
from homeassistant.components.ffmpeg import DATA_FFMPEG
from homeassistant.helpers.aiohttp_client import async_aiohttp_proxy_stream
from custom_components.reolink_dev.ReolinkPyPi.camera import ReolinkApi

_LOGGER = logging.getLogger(__name__)

STATE_MOTION = "motion"
STATE_NO_MOTION = "no_motion"
STATE_IDLE = "idle"

DEFAULT_NAME = "Reolink Camera"
DEFAULT_STREAM = "main"
DEFAULT_PROTOCOL = "rtmp"
DEFAULT_CHANNEL = 0
CONF_STREAM = "stream"
CONF_PROTOCOL = "protocol"
CONF_CHANNEL = "channel"
DOMAIN = "camera"
SERVICE_ENABLE_FTP = 'enable_ftp'
SERVICE_DISABLE_FTP = 'disable_ftp'
SERVICE_ENABLE_EMAIL = 'enable_email'
SERVICE_DISABLE_EMAIL = 'disable_email'
SERVICE_ENABLE_IR_LIGHTS = 'enable_ir_lights'
SERVICE_DISABLE_IR_LIGHTS = 'disable_ir_lights'
SERVICE_ENABLE_RECORDING = 'enable_recording'
SERVICE_DISABLE_RECORDING = 'disable_recording'
SERVICE_ENABLE_MOTION_DETECTION = 'enable_motion_detection'
SERVICE_DISABLE_MOTION_DETECTION = 'disable_motion_detection'

DEFAULT_BRAND = 'Reolink'
DOMAIN_DATA = 'reolink_devices'


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOST): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_USERNAME): cv.string,
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_STREAM, default=DEFAULT_STREAM): vol.In(["main", "sub"]),
        vol.Optional(CONF_PROTOCOL, default=DEFAULT_PROTOCOL): vol.In(["rtmp", "rtsp"]),
        vol.Optional(CONF_CHANNEL, default=DEFAULT_CHANNEL): cv.positive_int,
    }
)

@asyncio.coroutine
async def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    """Set up a Reolink IP Camera."""

    host = config.get(CONF_HOST)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    stream = config.get(CONF_STREAM)
    protocol = config.get(CONF_PROTOCOL)
    channel = config.get(CONF_CHANNEL)
    name = config.get(CONF_NAME)

    session = ReolinkApi(host, channel)
    await session.login(username, password)

    async_add_devices([ReolinkCamera(hass, session, host, username, password, stream, protocol, channel, name)], update_before_add=True)

# Event enable FTP
    def handler_enable_ftp(call):
        component = hass.data.get(DOMAIN)
        entity = component.get_entity(call.data.get(ATTR_ENTITY_ID))

        if entity:
            entity.enable_ftp_upload()
    hass.services.async_register(DOMAIN, SERVICE_ENABLE_FTP, handler_enable_ftp)

# Event disable FTP
    def handler_disable_ftp(call):
        component = hass.data.get(DOMAIN)
        entity = component.get_entity(call.data.get(ATTR_ENTITY_ID))

        if entity:
            entity.disable_ftp_upload()
    hass.services.async_register(DOMAIN, SERVICE_DISABLE_FTP, handler_disable_ftp)

# Event enable email
    def handler_enable_email(call):
        component = hass.data.get(DOMAIN)
        entity = component.get_entity(call.data.get(ATTR_ENTITY_ID))

        if entity:
            entity.enable_email()
    hass.services.async_register(DOMAIN, SERVICE_ENABLE_EMAIL, handler_enable_email)

# Event disable email
    def handler_disable_email(call):
        component = hass.data.get(DOMAIN)
        entity = component.get_entity(call.data.get(ATTR_ENTITY_ID))

        if entity:
            entity.disable_email()
    hass.services.async_register(DOMAIN, SERVICE_DISABLE_EMAIL, handler_disable_email)

# Event enable ir lights
    def handler_enable_ir_lights(call):
        component = hass.data.get(DOMAIN)
        entity = component.get_entity(call.data.get(ATTR_ENTITY_ID))

        if entity:
            entity.enable_ir_lights()
    hass.services.async_register(DOMAIN, SERVICE_ENABLE_IR_LIGHTS, handler_enable_ir_lights)

# Event disable ir lights
    def handler_disable_ir_lights(call):
        component = hass.data.get(DOMAIN)
        entity = component.get_entity(call.data.get(ATTR_ENTITY_ID))

        if entity:
            entity.disable_ir_lights()
    hass.services.async_register(DOMAIN, SERVICE_DISABLE_IR_LIGHTS, handler_disable_ir_lights)

# Event enable recording
    def handler_enable_recording(call):
        component = hass.data.get(DOMAIN)
        entity = component.get_entity(call.data.get(ATTR_ENTITY_ID))

        if entity:
            entity.enable_recording()
    hass.services.async_register(DOMAIN, SERVICE_ENABLE_RECORDING, handler_enable_recording)

# Event disable recording
    def handler_disable_recording(call):
        component = hass.data.get(DOMAIN)
        entity = component.get_entity(call.data.get(ATTR_ENTITY_ID))

        if entity:
            entity.disable_recording()
    hass.services.async_register(DOMAIN, SERVICE_DISABLE_RECORDING, handler_disable_recording)

# Event enable motion detection
    def handler_enable_motion_detection(call):
        component = hass.data.get(DOMAIN)
        entity = component.get_entity(call.data.get(ATTR_ENTITY_ID))

        if entity:
            entity.enable_motion_detection()
    hass.services.async_register(DOMAIN, SERVICE_ENABLE_MOTION_DETECTION, handler_enable_motion_detection)

# Event disable motion detection
    def handler_disable_motion_detection(call):
        component = hass.data.get(DOMAIN)
        entity = component.get_entity(call.data.get(ATTR_ENTITY_ID))

        if entity:
            entity.disable_motion_detection()
    hass.services.async_register(DOMAIN, SERVICE_DISABLE_MOTION_DETECTION, handler_disable_motion_detection)


class ReolinkCamera(Camera):
    """An implementation of a Reolink IP camera."""

    def __init__(self, hass, session, host, username, password, stream, protocol, channel, name):
        """Initialize a Reolink camera."""

        super().__init__()
        self._host = host
        self._username = username
        self._password = password
        self._stream = stream
        self._protocol = protocol
        self._channel = channel
        self._name = name
        self._reolinkSession = session
        self._hass = hass
        self._manager = self._hass.data[DATA_FFMPEG]

        self._last_update = 0
        self._last_image = None
        self._last_motion = 0
        self._ftp_state = None
        self._email_state = None
        self._ir_state = None
        self._recording_state = None
        self._ptzpresets = dict()
        self._motion_detection_state = None
        self._state = STATE_IDLE

        self._hass.bus.async_listen(EVENT_HOMEASSISTANT_STOP, self.disconnect)

    @property
    def state_attributes(self):
        """Return the camera state attributes."""
        attrs = {"access_token": self.access_tokens[-1]}

        if self._last_motion:
            attrs["last_motion"] = self._last_motion
        
        if self._last_update:
            attrs["last_update"] = self._last_update

        attrs["ftp_enabled"] = self._ftp_state
        attrs["email_enabled"] = self._email_state
        attrs["ir_lights_enabled"] = self._ir_state
        attrs["recording_enabled"] = self._recording_state
        attrs["ptzpresets"] = self._ptzpresets
        attrs["motion_detection_enabled"] = self._motion_detection_state

        return attrs

    @property
    def supported_features(self):
        """Return supported features."""
        return SUPPORT_STREAM

    @property
    def name(self):
        """Return the name of this camera."""
        return self._name

    @property
    def should_poll(self):
        """Polling needed for the device status."""
        return True

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def ftp_state(self):
        """Camera Motion FTP upload Status."""
        return self._ftp_state

    @property
    def email_state(self):
        """Camera email Status."""
        return self._email_state

    @property
    def recording_state(self):
        """Camera recording status."""
        return self._recording_state

    @property
    def ptzpresets(self):
        """Camera PTZ presets list."""
        return self._ptzpresets

    @property
    def motion_detection_state(self):
        """Camera motion detection setting status."""
        return self._motion_detection_state

    async def stream_source(self):
        """Return the source of the stream."""
        if self._protocol == "rtsp":
            rtspChannel = f"{self._channel+1:02d}"
            stream_source = f"rtsp://{self._username}:{self._password}@{self._host}:{self._reolinkSession.rtspport}/h264Preview_{rtspChannel}_{self._stream}"
        else:
            stream_source = f"rtmp://{self._host}:{self._reolinkSession.rtmpport}/bcs/channel{self._channel}_{self._stream}.bcs?channel={self._channel}&stream=0&user={self._username}&password={self._password}"

        return stream_source

    async def handle_async_mjpeg_stream(self, request):
        """Generate an HTTP MJPEG stream from the camera."""
        stream_source = await self.stream_source()

        stream = CameraMjpeg(self._manager.binary, loop=self._hass.loop)
        await stream.open_camera(stream_source)

        try:
            stream_reader = await stream.get_reader()
            return await async_aiohttp_proxy_stream(
                self._hass,
                request,
                stream_reader,
                self._manager.ffmpeg_stream_content_type,
            )
        finally:
            await stream.close()

    async def camera_image(self):
        """Return bytes of camera image."""
        return self._reolinkSession.still_image

    async def async_camera_image(self):
        """Return a still image response from the camera."""
        return await self._reolinkSession.snapshot

    def enable_ftp_upload(self):
        """Enable motion ftp recording in camera."""
        if asyncio.run_coroutine_threadsafe(self._reolinkSession.set_ftp(True), self.hass.loop).result():
            self._ftp_state = True
            self._hass.states.set(self.entity_id, self.state, self.state_attributes)

    def disable_ftp_upload(self):
        """Disable motion ftp recording."""
        if asyncio.run_coroutine_threadsafe(self._reolinkSession.set_ftp(False), self.hass.loop).result():
            self._ftp_state = False
            self._hass.states.set(self.entity_id, self.state, self.state_attributes)

    def enable_email(self):
        """Enable email motion detection in camera."""
        if asyncio.run_coroutine_threadsafe(self._reolinkSession.set_email(True), self.hass.loop).result():
            self._email_state = True
            self._hass.states.set(self.entity_id, self.state, self.state_attributes)

    def disable_email(self):
        """Disable email motion detection."""
        if asyncio.run_coroutine_threadsafe(self._reolinkSession.set_email(False), self.hass.loop).result():
            self._email_state = False
            self._hass.states.set(self.entity_id, self.state, self.state_attributes)

    def enable_ir_lights(self):
        """Enable IR lights."""
        if asyncio.run_coroutine_threadsafe(self._reolinkSession.set_ir_lights(True), self.hass.loop).result():
            self._ir_state = True
            self._hass.states.set(self.entity_id, self.state, self.state_attributes)

    def disable_ir_lights(self):
        """Disable IR lights."""
        if asyncio.run_coroutine_threadsafe(self._reolinkSession.set_ir_lights(False), self.hass.loop).result():
            self._ir_state = False
            self._hass.states.set(self.entity_id, self.state, self.state_attributes)

    def enable_recording(self):
        """Enable recording."""
        if asyncio.run_coroutine_threadsafe(self._reolinkSession.set_recording(True), self.hass.loop).result():
            self._recording_state = True
            self._hass.states.set(self.entity_id, self.state, self.state_attributes)

    def disable_recording(self):
        """Disable recording."""
        if asyncio.run_coroutine_threadsafe(self._reolinkSession.set_recording(False), self.hass.loop).result():
            self._recording_state = False
            self._hass.states.set(self.entity_id, self.state, self.state_attributes)

    def enable_motion_detection(self):
        """Enable motion_detecion."""
        if asyncio.run_coroutine_threadsafe(self._reolinkSession.set_motion_detection(True), self.hass.loop).result():
            self._motion_detection_state = True
            self._hass.states.set(self.entity_id, self.state, self.state_attributes)

    def disable_motion_detection(self):
        """Disable motion detecion."""
        if asyncio.run_coroutine_threadsafe(self._reolinkSession.set_motion_detection(False), self.hass.loop).result():
            self._motion_detection_state = False
            self._hass.states.set(self.entity_id, self.state, self.state_attributes)
    
    async def update_motion_state(self):
        await self._reolinkSession.get_motion_state()

        if self._reolinkSession.motion_state == True:
            self._state = STATE_MOTION
            self._last_motion = self._reolinkSession.last_motion
        else:
            self._state = STATE_NO_MOTION
    
    async def update_status(self):
        await self._reolinkSession.get_settings()

        self._last_update = datetime.datetime.now()
        self._ftp_state = self._reolinkSession.ftp_state
        self._email_state = self._reolinkSession.email_state
        self._ir_state = self._reolinkSession.ir_state
        self._recording_state = self._reolinkSession.recording_state
        self._ptzpresets = self._reolinkSession.ptzpresets
        self._motion_detection_state = self._reolinkSession.motion_detection_state

    async def async_update(self):
        """Update the data from the camera."""
        if not self._reolinkSession.session_active():
            if (self._last_update == 0 or
               (datetime.datetime.now() - self._last_update).total_seconds() >= 60):
                #asyncio.run_coroutine_threadsafe(self._reolinkSession.login(self._username, self._password), self.hass.loop).result()
                await self._reolinkSession.login(self._username, self._password)
            else:
                return
        
        if not self._reolinkSession.session_active():
            _LOGGER.error(f"Failed to reconnect with Reolink at IP {self._host}. Retrying in 60 seconds.")
            self._last_update = datetime.datetime.now()

        try:
            #asyncio.run_coroutine_threadsafe(self.update_motion_state(), self.hass.loop).result()
            await self.update_motion_state()

            if (self._last_update == 0 or
               (datetime.datetime.now() - self._last_update).total_seconds() >= 30):
                #asyncio.run_coroutine_threadsafe(self.update_status(), self.hass.loop)
                await self.update_status()

        except Exception as ex:
            _LOGGER.error(f"Got exception while fetching the state: {ex}")
            self._reolinkSession.clear_token()

    async def disconnect(self, event):
        _LOGGER.info("Disconnecting from Reolink camera")
        await self._reolinkSession.logout()
