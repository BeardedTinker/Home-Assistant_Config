"""This component updates the camera API and subscription."""
import logging
import re

from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_TIMEOUT,
    CONF_USERNAME,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.network import get_url
from homeassistant.helpers.entity_registry import (
    async_entries_for_config_entry,
    async_get_registry as async_get_entity_registry,
)

from reolink.camera_api import Api
from reolink.subscription_manager import Manager

from .const import (
    BASE,
    EVENT_DATA_RECEIVED,
    CONF_CHANNEL,
    CONF_MOTION_OFF_DELAY,
    CONF_PROTOCOL,
    CONF_STREAM,
    DEFAULT_CHANNEL,
    DEFAULT_MOTION_OFF_DELAY,
    DEFAULT_PROTOCOL,
    DEFAULT_STREAM,
    DEFAULT_TIMEOUT,
    DOMAIN,
    PUSH_MANAGER,
    SESSION_RENEW_THRESHOLD,
)

_LOGGER = logging.getLogger(__name__)

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

        if CONF_TIMEOUT not in options:
            self._timeout = DEFAULT_TIMEOUT
        else:
            self._timeout = options[CONF_TIMEOUT]

        if CONF_STREAM not in options:
            self._stream = DEFAULT_STREAM
        else:
            self._stream = options[CONF_STREAM]

        if CONF_PROTOCOL not in options:
            self._protocol= DEFAULT_PROTOCOL
        else:
            self._protocol = options[CONF_PROTOCOL]

        self._api = Api(
            config[CONF_HOST],
            config[CONF_PORT],
            self._username,
            self._password,
            channel=self._channel - 1,
            stream=self._stream,
            protocol=self._protocol,
            timeout=self._timeout,
        )

        self._hass = hass
        self.sync_functions = list()
        self.motion_detection_state = True

        if CONF_MOTION_OFF_DELAY not in options:
            self.motion_off_delay = DEFAULT_MOTION_OFF_DELAY
        else:
            self.motion_off_delay = options[CONF_MOTION_OFF_DELAY]

    @property
    def name(self):
        """Create the device name."""
        return self._api.name

    @property
    def unique_id(self):
        """Create the unique ID, base for all entities."""
        id = self._api.mac_address.replace(":", "")
        return f"{id}-{self.channel}"

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

    async def connect_api(self):
        """Connect to the Reolink API and fetch initial dataset."""
        if not await self._api.get_settings():
            return False
        if not await self._api.get_states():
            return False

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
        for func in self.sync_functions:
            await self._hass.async_add_executor_job(func)


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

    @property
    def sman(self):
        """Return the session manager object."""
        return self._sman

    async def subscribe(self, event_id):
        """Subscribe to motion events and set the webhook as callback."""
        self._webhook_id = await self.register_webhook(event_id)
        self._webhook_url = "{}{}".format(
            get_url(self._hass, prefer_external=False),
            self._hass.components.webhook.async_generate_path(self._webhook_id)
        )

        self._sman = Manager(
            self._host, self._port, self._username, self._password
        )
        if await self._sman.subscribe(self._webhook_url):
            _LOGGER.info(
                "Host %s subscribed successfully to webhook %s",
                self._host,
                self._webhook_url,
            )
            await self.set_available(True)
        return True

    async def register_webhook(self, event_id):
        """
        Register a webhook for motion events if it does not exist yet (in case of NVR).
        The webhook name (in info) contains the event id (contains mac address op the camera).
        So when motion triggers the webhook, it triggers this event. The event is handled by
        the binary sensor, in case of NVR the binary sensor also figures out what channel has
        the motion. So the flow is: camera onvif event->webhook->HA event->binary sensor.
        """
        _LOGGER.debug("Registering webhook for event ID %s", event_id)

        webhook_id = self._hass.components.webhook.async_generate_id()
        self._hass.components.webhook.async_register(DOMAIN, event_id, webhook_id, handle_webhook)

        return webhook_id

    async def renew(self):
        """Renew the subscription of the motion events (lease time is set to 15 minutes)."""
        if self._sman.renewtimer <= SESSION_RENEW_THRESHOLD:
            if not await self._sman.renew():
                _LOGGER.error(
                    "Host %s error renewing the Reolink subscription",
                    self._host,
                )
                await self.set_available(False)
                await self._sman.subscribe(self._webhook_url)

    async def set_available(self, available: bool):
        """Set the availability state to the base object."""
        event_id = await get_event_by_webhook(self._hass, self._webhook_id)

        for entry_id in self._hass.data[DOMAIN]:
            base_entry = self._hass.data[DOMAIN][entry_id][BASE]
            if base_entry.event_id == event_id:
                base_entry.motion_detection_state = available

    async def unsubscribe(self):
        """Unsubscribe from the motion events."""
        await self.set_available(False)
        await self.unregister_webhook()
        return await self._sman.unsubscribe()

    async def unregister_webhook(self):
        """Unregister the webhook for motion events."""

        _LOGGER.debug("Unregistering webhook %s", self._webhook_id)
        self._hass.components.webhook.async_unregister(self._webhook_id)


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

    event_id = await get_event_by_webhook(hass, webhook_id)
    if not event_id:
        _LOGGER.error("Webhook triggered without event to fire")

    hass.bus.async_fire(event_id, {"IsMotion": is_motion})


async def get_webhook_by_event(hass: HomeAssistant, event_id):
    """Find the webhook_id by the event_id."""
    try:
        handlers = hass.data["webhook"]
    except KeyError:
        return

    for wid, info in handlers.items():  # ToDo: check other NVR streams still use this
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
