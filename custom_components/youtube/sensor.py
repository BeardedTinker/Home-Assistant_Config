"""
A platform which give you info about the newest video on a channel.

For more details about this component, please refer to the documentation at
https://github.com/custom-components/youtube
"""

import html
import logging
import async_timeout
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity

CONF_CHANNEL_ID = 'channel_id'

ICON = 'mdi:youtube'

BASE_URL = 'https://www.youtube.com/feeds/videos.xml?channel_id={}'
BASE_URL_LIVE = "https://www.youtube.com/channel/{}"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_CHANNEL_ID): cv.string,
})

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(
        hass, config, async_add_entities, discovery_info=None):  # pylint: disable=unused-argument
    """Setup sensor platform."""
    channel_id = config['channel_id']
    session = async_create_clientsession(hass)
    try:
        url = BASE_URL.format(channel_id)
        async with async_timeout.timeout(10, loop=hass.loop):
            response = await session.get(url)
            info = await response.text()
        name = html.parser.HTMLParser().unescape(
            info.split('<title>')[1].split('</')[0])
    except Exception:  # pylint: disable=broad-except

        name = None

    if name is not None:
        async_add_entities([YoutubeSensor(channel_id, name, session)], True)

class YoutubeSensor(Entity):
    """YouTube Sensor class"""
    def __init__(self, channel_id, name, session):
        self._state = None
        self.session = session
        self._image = None
        self.live = False
        self._name = name
        self.channel_id = channel_id
        self.url = None
        self.published = None

    async def async_update(self):
        """Update sensor."""
        _LOGGER.debug('%s - Running update', self._name)
        try:
            url = BASE_URL.format(self.channel_id)
            async with async_timeout.timeout(10, loop=self.hass.loop):
                response = await self.session.get(url)
                info = await response.text()
            title = html.parser.HTMLParser().unescape(
                info.split('<title>')[2].split('</')[0])
            url = info.split('<link rel="alternate" href="')[2].split('"/>')[0]
            if self.live or url != self.url:
                self.live = await is_live(self.channel_id, self._name, self.hass, self.session)
            else:
                _LOGGER.debug('%s - Skipping live check', self._name)
            self.url = url
            self.published = info.split('<published>')[2].split('</')[0]
            thumbnail_url = info.split(
                '<media:thumbnail url="')[1].split('"')[0]
            self._state = title
            self._image = thumbnail_url
        except Exception as error:  # pylint: disable=broad-except
            _LOGGER.debug('%s - Could not update - %s', self._name, error)

    @property
    def name(self):
        """Name."""
        return self._name

    @property
    def entity_picture(self):
        """Picture."""
        return self._image

    @property
    def state(self):
        """State."""
        return self._state

    @property
    def icon(self):
        """Icon."""
        return ICON

    @property
    def device_state_attributes(self):
        """Attributes."""
        return {'url': self.url,
                'published': self.published,
                'live': self.live}


async def is_live(channel_id, name, hass, session):
    """Return bool if channel is live"""
    returnvalue = False
    url = BASE_URL_LIVE.format(channel_id)
    try:
        async with async_timeout.timeout(10, loop=hass.loop):
            response = await session.get(url)
            info = await response.text()
        if 'live-promo' in info:
            returnvalue = True
            _LOGGER.debug('%s - Channel is live', name)
    except Exception as error:  # pylint: disable=broad-except
        _LOGGER.debug('%s - Could not update - %s', name, error)
    return returnvalue
