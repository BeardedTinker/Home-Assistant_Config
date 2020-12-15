"""This component updates the camera API and subscription."""
import logging

from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_TIMEOUT,
    CONF_USERNAME,
)

from reolink.camera_api import Api
from reolink.subscription_manager import Manager

from .const import (
    EVENT_DATA_RECEIVED,
    CONF_CHANNEL,
    CONF_MOTION_OFF_DELAY,
    DEFAULT_CHANNEL,
    DEFAULT_TIMEOUT,
    SESSION_RENEW_THRESHOLD,
)

_LOGGER = logging.getLogger(__name__)


class ReolinkBase:
    """The implementation of the Reolink IP base class."""

    def __init__(
        self, hass, config: dict, options: dict
    ):  # pylint: disable=too-many-arguments
        """Initialize a Reolink camera."""
        _LOGGER.debug(config)
        _LOGGER.debug(options)
        self._username = config[CONF_USERNAME]
        self._password = config[CONF_PASSWORD]

        if CONF_CHANNEL not in config:
            self.channel = DEFAULT_CHANNEL
        else:
            self.channel = config[CONF_CHANNEL]

        if CONF_TIMEOUT not in config:
            self._timeout = DEFAULT_TIMEOUT
        else:
            self._timeout = config[CONF_TIMEOUT]

        self._api = Api(
            config[CONF_HOST],
            config[CONF_PORT],
            self._username,
            self._password,
            channel=self.channel - 1,
            timeout=self._timeout,
        )
        self._sman = None
        self._webhook_url = None
        self._hass = hass
        self.sync_functions = list()
        self.motion_detection_state = True

        if CONF_MOTION_OFF_DELAY not in options:
            self.motion_off_delay = 60
        else:
            self.motion_off_delay = options[CONF_MOTION_OFF_DELAY]

    @property
    def name(self):
        """Create the device name."""
        if self.channel == 1:
            return self._api.name
        return f"{self._api.name}{self.channel}"

    @property
    def unique_id(self):
        """Create the unique ID, base for all entities."""
        return f"{self._api.mac_address}{self.channel}"

    @property
    def event_id(self):
        """Create the event ID string."""
        event_id = self._api.mac_address.replace(":", "")
        return f"{EVENT_DATA_RECEIVED}-{event_id}-{self.channel}"

    @property
    def api(self):
        """Return the API object."""
        return self._api

    @property
    def sman(self):
        """Return the Session Manager object."""
        return self._sman

    async def connect_api(self):
        """Connect to the Reolink API and fetch initial dataset."""
        if not await self._api.get_settings():
            return False
        if not await self._api.get_states():
            return False

        await self._api.is_admin()
        return True

    async def update_api(self):
        """Call the API of the camera device to update the states."""
        await self._api.get_states()

    async def disconnect_api(self):
        """Disconnect from the API, so the connection will be released."""
        await self._api.logout()

    async def subscribe(self, webhook_url):
        """Subscribe to motion events and set the webhook as callback."""
        self._webhook_url = webhook_url

        if not self._api.session_active:
            _LOGGER.error("Please connect with the camera API before subscribing")
            return False

        self._sman = Manager(
            self._api.host, self._api.onvif_port, self._username, self._password
        )
        if not await self._sman.subscribe(self._webhook_url):
            return False

        _LOGGER.info(
            "Host %s subscribed successfully to webhook %s!",
            self._api.host,
            webhook_url,
        )
        return True

    async def renew(self):
        """Renew the subscription of the motion events (lease time is set to 15 minutes)."""
        if self._sman.renewtimer <= SESSION_RENEW_THRESHOLD:
            if not await self._sman.renew():
                _LOGGER.error(
                    "Host %s error renewing the Reolink subscription",
                    self._api.host,
                )
                await self._sman.subscribe(self._webhook_url)

    async def unsubscribe(self):
        """Unsubscribe from the motion events."""
        return await self._sman.unsubscribe()

    async def stop(self):
        """Disconnect the APi and unsubscribe."""
        await self.disconnect_api()
        await self.unsubscribe()
        for func in self.sync_functions:
            await self._hass.async_add_executor_job(func)
