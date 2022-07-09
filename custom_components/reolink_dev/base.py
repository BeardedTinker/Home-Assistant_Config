"""This component updates the camera API and subscription."""
import logging
import os
import re

import datetime as dt
from typing import Optional
import ssl

from urllib.parse import quote_plus
from dateutil.relativedelta import relativedelta

from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_TIMEOUT,
    CONF_USERNAME,
)
from homeassistant.core import Context, HomeAssistant
from homeassistant.helpers.network import get_url, NoURLAvailableError
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.helpers.aiohttp_client import async_create_clientsession
import homeassistant.util.dt as dt_util

from reolink.camera_api import Api
from reolink.subscription_manager import Manager
from reolink.typings import SearchTime
from .typings import VoDEvent, VoDEventThumbnail

from .const import (
    BASE,
    CONF_PLAYBACK_MONTHS,
    CONF_THUMBNAIL_PATH,
    DEFAULT_PLAYBACK_MONTHS,
    EVENT_DATA_RECEIVED,
    CONF_USE_HTTPS,
    CONF_CHANNEL,
    CONF_MOTION_OFF_DELAY,
    CONF_PROTOCOL,
    CONF_STREAM,
    CONF_STREAM_FORMAT,
    CONF_MOTION_STATES_UPDATE_FALLBACK_DELAY,
    DEFAULT_USE_HTTPS,
    DEFAULT_CHANNEL,
    DEFAULT_MOTION_OFF_DELAY,
    DEFAULT_PROTOCOL,
    DEFAULT_STREAM,
    DEFAULT_STREAM_FORMAT,
    DEFAULT_TIMEOUT,
    DEFAULT_MOTION_STATES_UPDATE_FALLBACK_DELAY,
    DOMAIN,
    PUSH_MANAGER,
    SESSION_RENEW_THRESHOLD,
    THUMBNAIL_EXTENSION,
    THUMBNAIL_URL,
    VOD_URL,
)

_LOGGER = logging.getLogger(__name__)
_LOGGER_DATA = logging.getLogger(__name__ + ".data")

STORAGE_VERSION = 1


class ReolinkBase:
    """The implementation of the Reolink IP base class."""

    def __init__(
        self, hass: HomeAssistant, config: dict, options: dict
    ):  # pylint: disable=too-many-arguments
        """Initialize a Reolink camera."""

        self._username = config[CONF_USERNAME]
        self._password = config[CONF_PASSWORD]

        if CONF_CHANNEL not in config:
            self._channel = DEFAULT_CHANNEL
        else:
            self._channel = config[CONF_CHANNEL]

        if CONF_USE_HTTPS not in config:
            self._use_https = DEFAULT_USE_HTTPS
        else:
            self._use_https = config[CONF_USE_HTTPS]

        if config[CONF_PORT] == 80 and self._use_https:
            _LOGGER.warning("Port 80 is used, USE_HTTPS set back to False")
            self._use_https = False

        if CONF_TIMEOUT not in options:
            self._timeout = DEFAULT_TIMEOUT
        else:
            self._timeout = options[CONF_TIMEOUT]

        if CONF_STREAM not in options:
            self._stream = DEFAULT_STREAM
        else:
            self._stream = options[CONF_STREAM]

        if CONF_STREAM_FORMAT not in options:
            self._stream_format = DEFAULT_STREAM_FORMAT
        else:
            self._stream_format = options[CONF_STREAM_FORMAT]

        if CONF_PROTOCOL not in options:
            self._protocol = DEFAULT_PROTOCOL
        else:
            self._protocol = options[CONF_PROTOCOL]

        global last_known_hass
        last_known_hass = hass

        self._api = Api(
            config[CONF_HOST],
            config[CONF_PORT],
            self._username,
            self._password,
            use_https=self._use_https,
            channel=self._channel - 1,
            stream=self._stream,
            stream_format=self._stream_format,
            protocol=self._protocol,
            timeout=self._timeout,
            aiohttp_get_session_callback=callback_get_iohttp_session
        )

        self._hass = hass
        self.async_functions = list()
        self.sync_functions = list()

        self.motion_detection_state = True
        self.object_person_detection_state = True
        self.object_vehicle_detection_state = True

        if CONF_MOTION_OFF_DELAY not in options:
            self.motion_off_delay = DEFAULT_MOTION_OFF_DELAY
        else:
            self.motion_off_delay: int = options[CONF_MOTION_OFF_DELAY]

        if CONF_PLAYBACK_MONTHS not in options:
            self.playback_months = DEFAULT_PLAYBACK_MONTHS
        else:
            self.playback_months: int = options[CONF_PLAYBACK_MONTHS]

        if CONF_THUMBNAIL_PATH not in options:
            self._thumbnail_path = None
        else:
            self._thumbnail_path: str = options[CONF_THUMBNAIL_PATH]

        if CONF_MOTION_STATES_UPDATE_FALLBACK_DELAY not in options:
            self.motion_states_update_fallback_delay = DEFAULT_MOTION_STATES_UPDATE_FALLBACK_DELAY
        else:
            self.motion_states_update_fallback_delay = options[CONF_MOTION_STATES_UPDATE_FALLBACK_DELAY]

        from .binary_sensor import MotionSensor, ObjectDetectedSensor

        self.sensor_motion_detection: Optional[MotionSensor] = None
        self.sensor_person_detection: Optional[ObjectDetectedSensor] = None
        self.sensor_vehicle_detection: Optional[ObjectDetectedSensor] = None
        self.sensor_pet_detection: Optional[ObjectDetectedSensor] = None

    @property
    def name(self):
        """Create the device name."""
        return self._api.name

    @property
    def unique_id(self):
        """Create the unique ID, base for all entities."""
        uid = self._api.mac_address.replace(":", "")
        return f"{uid}-{self.channel}"

    @property
    def event_id(self):
        """Create the event ID string."""
        event_id = self._api.mac_address.replace(":", "")
        return f"{EVENT_DATA_RECEIVED}-{event_id}"

    @property
    def push_manager(self):
        """Create the event ID string."""
        push_id = self._api.mac_address.replace(":", "")
        return f"{PUSH_MANAGER}-{push_id}"

    @property
    def timeout(self):
        """Return the timeout setting."""
        return self._timeout

    @property
    def channel(self):
        """Return the channel setting."""
        return self._channel

    @property
    def api(self):
        """Return the API object."""
        return self._api

    @property
    def thumbnail_path(self):
        """ Thumbnail storage location """
        if not self._thumbnail_path:
            self._thumbnail_path = self._hass.config.path(
                f"{STORAGE_DIR}/{DOMAIN}/{self.unique_id}"
            )
        return self._thumbnail_path

    def enable_https(self, enable: bool):
        self._use_https = enable
        self._api.enable_https(enable)

    def set_thumbnail_path(self, value):
        """ Set custom thumbnail path"""
        self._thumbnail_path = value

    async def connect_api(self):
        """Connect to the Reolink API and fetch initial dataset."""
        if not await self._api.get_settings():
            return False
        if not await self._api.get_states():
            return False
            
        await self._api.get_ai_state()
        await self._api.is_admin()
        return True

    async def set_channel(self, channel):
        """Set the API channel."""
        self._channel = channel
        await self._api.set_channel(channel - 1)

    async def set_protocol(self, protocol):
        """Set the protocol."""
        self._protocol = protocol
        await self._api.set_protocol(protocol)

    async def set_stream(self, stream):
        """Set the stream."""
        self._stream = stream
        await self._api.set_stream(stream)

    async def set_stream_format(self, stream_format):
        """Set the stream format."""
        self._stream_format = stream_format
        await self._api.set_stream_format(stream_format)

    async def set_timeout(self, timeout):
        """Set the API timeout."""
        self._timeout = timeout
        await self._api.set_timeout(timeout)

    async def update_states(self):
        """Call the API of the camera device to update the states."""
        await self._api.get_states()

    async def update_settings(self):
        """Call the API of the camera device to update the settings."""
        await self._api.get_settings()

    async def disconnect_api(self):
        """Disconnect from the API, so the connection will be released."""
        await self._api.logout()

    async def stop(self):
        """Disconnect the API and deregister the event listener."""
        await self.disconnect_api()
        for func in self.async_functions:
            await func()
        for func in self.sync_functions:
            await self._hass.async_add_executor_job(func)

    async def send_search(
        self, start: dt.datetime, end: dt.datetime, only_status: bool = False
    ):
        """ Call the API of the camera device to search for VoDs """
        return await self._api.send_search(start, end, only_status)

    async def emit_search_results(
        self,
        bus_event_id: str,
        camera_id: str,
        start: Optional[dt.datetime] = None,
        end: Optional[dt.datetime] = None,
        context: Optional[Context] = None,
    ):
        """ Run search and emit VoD results to event """

        if end is None:
            end = dt_util.now()
        if start is None:
            start = dt.datetime.combine(end.date().replace(day=1), dt.time.min)
            if self.playback_months > 1:
                start -= relativedelta(months=int(self.playback_months))

        _, files = await self._api.send_search(start, end)

        for file in files:
            end = searchtime_to_datetime(file["EndTime"], end.tzinfo)
            start = searchtime_to_datetime(file["StartTime"], end.tzinfo)
            event_id = str(start.timestamp())
            url = VOD_URL.format(camera_id=camera_id, event_id=quote_plus(file["name"]))

            thumbnail = os.path.join(
                self.thumbnail_path, f"{event_id}.{THUMBNAIL_EXTENSION}"
            )

            self._hass.bus.fire(
                bus_event_id,
                VoDEvent(
                    event_id,
                    start,
                    end - start,
                    file["name"],
                    url,
                    VoDEventThumbnail(
                        THUMBNAIL_URL.format(camera_id=camera_id, event_id=event_id),
                        os.path.isfile(thumbnail),
                        thumbnail,
                    ),
                ),
                context=context,
            )

# warning once in the logs that Internal URL has is using HTTP while external URL is using HTTPS which is incompatible
# HomeAssistant starting 2022.3 when trying to retrieve internal URL
warnedAboutNoURLAvailableError = False

class ReolinkPush:
    """The implementation of the Reolink IP base class."""

    def __init__(
        self, hass: HomeAssistant, host, port, username, password
    ):  # pylint: disable=too-many-arguments
        """Initialize a Reolink camera."""
        self._host = host
        self._port = port
        self._username = username
        self._password = password
        self._hass = hass

        self._sman = None
        self._webhook_url = None
        self._webhook_id = None
        self._event_id = None

    @property
    def sman(self):
        """Return the session manager object."""
        return self._sman

    async def subscribe(self, event_id):
        """Subscribe to motion events and set the webhook as callback."""
        global warnedAboutNoURLAvailableError
        self._event_id = event_id
        self._webhook_id = await self.register_webhook()

        try:
            self._webhook_url = "{}{}".format(
                get_url(self._hass, prefer_external=False),
                self._hass.components.webhook.async_generate_path(self._webhook_id),
            )
        except NoURLAvailableError as ex:
            if not warnedAboutNoURLAvailableError:
                warnedAboutNoURLAvailableError = True
                _LOGGER.warning("Your are using HTTP for internal URL while using HTTPS for external URL in HA which is"
                " not supported anymore by HomeAssistant starting 2022.3."
                 "Please change your configuration to use HTTPS for internal URL or disable HTTPS for external.")
            try:
                self._webhook_url = "{}{}".format(
                    get_url(self._hass, prefer_external=True),
                    self._hass.components.webhook.async_generate_path(self._webhook_id),
                )
            except NoURLAvailableError as ex:
                # If we can't get a URL for external or internal, we will still mark the camara as available
                await self.set_available(True)
                return False

        self._sman = Manager(self._host, self._port, self._username, self._password)
        if await self._sman.subscribe(self._webhook_url):
            _LOGGER.info(
                "Host %s subscribed successfully to webhook %s",
                self._host,
                self._webhook_url,
            )
            await self.set_available(True)
        else:
            _LOGGER.error(
                "Host %s subscription failed to its webhook, base object state will be set to NotAvailable",
                self._host,
            )
            await self.set_available(False)
        return True

    async def register_webhook(self):
        """
        Register a webhook for motion events if it does not exist yet (in case of NVR).
        The webhook name (in info) contains the event id (contains mac address op the camera).
        So when motion triggers the webhook, it triggers this event. The event is handled by
        the binary sensor, in case of NVR the binary sensor also figures out what channel has
        the motion. So the flow is: camera onvif event->webhook->HA event->binary sensor.
        """
        _LOGGER.debug("Registering webhook for event ID %s", self._event_id)

        webhook_id = self._hass.components.webhook.async_generate_id()
        self._hass.components.webhook.async_register(
            DOMAIN, self._event_id, webhook_id, handle_webhook
        )

        return webhook_id

    async def renew(self):
        """Renew the subscription of the motion events (lease time is set to 15 minutes)."""

        # _sman is available only if subscription was able to find an Internal/External URL, we can retry in case user has
        # fixed it after HASS config change
        if self._sman is None:
            return await self.subscribe(self._event_id)

        if self._sman.renewtimer <= SESSION_RENEW_THRESHOLD:
            if not await self._sman.renew():
                _LOGGER.error(
                    "Host %s error renewing the Reolink subscription",
                    self._host,
                )
                await self.set_available(False)
                await self._sman.subscribe(self._webhook_url)
            else:
                _LOGGER.info(
                    "Host %s SUCCESSFULLY renewed Reolink subscription",
                    self._host,
                )
                await self.set_available(True)
        else:
            await self.set_available(True)

    async def set_available(self, available: bool):
        """Set the availability state to the base object."""
        self._hass.bus.async_fire(self._event_id, {"available": available})

    async def unsubscribe(self):
        """Unsubscribe from the motion events."""
        await self.set_available(False)
        await self.unregister_webhook()
        return await self._sman.unsubscribe()

    async def unregister_webhook(self):
        """Unregister the webhook for motion events."""

        _LOGGER.debug("Unregistering webhook %s", self._webhook_id)
        self._hass.components.webhook.async_unregister(self._webhook_id)

    async def count_members(self):
        """Count the number of camera's using this push manager."""
        members = 0
        for entry_id in self._hass.data[DOMAIN]:
            _LOGGER.debug("Got data entry: %s", entry_id)

            if PUSH_MANAGER in entry_id:
                continue  # Count config entries only

            try:
                base = self._hass.data[DOMAIN][entry_id][BASE]
                if base.event_id == self._event_id:
                    members += 1
            except AttributeError:
                pass
            except KeyError:
                pass
        _LOGGER.debug("Found %d listeners for event %s", members, self._event_id)
        return members


async def handle_webhook(hass, webhook_id, request):
    """Handle incoming webhook from Reolink for inbound messages and calls."""

    _LOGGER.debug("Webhook called")

    if not request.body_exists:
        _LOGGER.debug("Webhook triggered without payload")

    data = await request.text()
    if not data:
        _LOGGER.debug("Webhook triggered with unknown payload")
        return

    _LOGGER_DATA.debug("Webhook received payload: %s", data)

    matches = re.findall(r'Name="IsMotion" Value="(.+?)"', data)
    if matches:
        is_motion = matches[0] == "true"
    else:
        _LOGGER.debug("Webhook triggered with unknown payload")
        return

    event_id = await get_event_by_webhook(hass, webhook_id)
    if not event_id:
        _LOGGER.error("Webhook triggered without event to fire")

    hass.bus.async_fire(event_id, {"motion": is_motion})


async def get_webhook_by_event(hass: HomeAssistant, event_id):
    """Find the webhook_id by the event_id."""
    try:
        handlers = hass.data["webhook"]
    except KeyError:
        return

    for wid, info in handlers.items():
        _LOGGER.debug("Webhook: %s", wid)
        _LOGGER.debug(info)
        if info["name"] == event_id:
            return wid


async def get_event_by_webhook(hass: HomeAssistant, webhook_id):
    """Find the event_id by the webhook_id."""
    try:
        handlers = hass.data["webhook"]
    except KeyError:
        return

    for wid, info in handlers.items():
        if wid == webhook_id:
            event_id = info["name"]
            return event_id


def searchtime_to_datetime(self: SearchTime, timezone: dt.tzinfo):
    """ Convert SearchTime to datetime """
    return dt.datetime(
        self["year"],
        self["mon"],
        self["day"],
        self["hour"],
        self["min"],
        self["sec"],
        tzinfo=timezone,
    )


last_known_hass: Optional[HomeAssistant] = None


def callback_get_iohttp_session():
    """Return the iohttp session for the last known hass instance."""
    global last_known_hass
    if last_known_hass is None:
        raise Exception("No Home Assistant instance found")
        
    context = ssl.create_default_context()
    context.set_ciphers("DEFAULT")
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    session = async_create_clientsession(last_known_hass, verify_ssl=False)
    session.connector._ssl = context
    return session
