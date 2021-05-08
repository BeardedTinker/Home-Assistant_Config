"""
Support for Luftdaten sensors.

Copyright (c) 2019 Mario Villavecchia

Licensed under MIT. All rights reserved.

https://github.com/lichtteil/local_luftdaten/
"""

import logging
import asyncio
import aiohttp
import async_timeout

import json

import requests
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import Entity
import homeassistant.helpers.config_validation as cv

from .const import *


_LOGGER = logging.getLogger(__name__)


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_MONITORED_CONDITIONS):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_RESOURCE, default=DEFAULT_RESOURCE): cv.string,
    vol.Optional(CONF_VERIFY_SSL, default=DEFAULT_VERIFY_SSL): cv.boolean,
    vol.Optional(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): cv.time_period
})


@asyncio.coroutine
async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the Luftdaten sensor."""
    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    verify_ssl = config.get(CONF_VERIFY_SSL)

    resource = config.get(CONF_RESOURCE).format(host)

    session = async_get_clientsession(hass, verify_ssl)
    rest_client = LuftdatenClient(hass.loop, session, resource)

    devices = []
    for variable in config[CONF_MONITORED_CONDITIONS]:
        devices.append(LuftdatenSensor(rest_client, name, variable))

    async_add_entities(devices, True)


class LuftdatenSensor(Entity):
    """Implementation of a LuftdatenSensor sensor."""

    def __init__(self, rest_client, name, sensor_type):
        """Initialize the LuftdatenSensor sensor."""
        self.rest_client = rest_client
        self._name = name
        self._state = None
        self.sensor_type = sensor_type
        self._unit_of_measurement = SENSOR_TYPES[sensor_type][1]
        self._device_class = SENSOR_TYPES[sensor_type][2]
        self._unique_id = '{} {}'.format(self._name, SENSOR_TYPES[self.sensor_type][0])

    @property
    def name(self):
        """Return the name of the sensor."""
        return '{} {}'.format(self._name, SENSOR_TYPES[self.sensor_type][0])

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def device_class(self):
        """Return the device class of this entity, if any."""
        return self._device_class

    @property
    def icon(self):
        """Icon of the sensor, if class is None."""
        if SENSOR_TYPES[self.sensor_type][0] == "PM2.5":
            return 'mdi:thought-bubble-outline'
        elif SENSOR_TYPES[self.sensor_type][0] == "PM10":
            return 'mdi:thought-bubble'
        elif SENSOR_TYPES[self.sensor_type][2] == None:
            return 'mdi:cloud-search-outline'

    @property
    def unique_id(self):
        return self._unique_id

    async def async_update(self):
        """Get the latest data from REST API and update the state."""
        try:
            await self.rest_client.async_update()
        except LuftdatenError:
            value = None
            return
        value = self.rest_client.data

        try:
            parsed_json = json.loads(value)
            if not isinstance(parsed_json, dict):
                _LOGGER.warning("JSON result was not a dictionary")
                return
        except ValueError:
            _LOGGER.warning("REST result could not be parsed as JSON")
            _LOGGER.debug("Erroneous JSON: %s", value)
            return

        sensordata_values = parsed_json['sensordatavalues']
        for sensordata_value in sensordata_values:
            if sensordata_value['value_type'] == self.sensor_type:
                self._state = sensordata_value['value']


class LuftdatenError(Exception):
    pass


class LuftdatenClient(object):
    """Class for handling the data retrieval."""

    def __init__(self, loop, session, resource):
        """Initialize the data object."""
        self._loop = loop
        self._session = session
        self._resource = resource
        self.data = None

    async def async_update(self):
        """Get the latest data from Luftdaten service."""
        _LOGGER.debug("Get data from %s", str(self._resource))
        try:
            with async_timeout.timeout(30, loop=self._loop):
                response = await self._session.get(self._resource)
            self.data = await response.text()
            _LOGGER.debug("Received data: %s", str(self.data))
        except aiohttp.ClientError as err:
            _LOGGER.warning("REST request error: {0}".format(err))
            self.data = None
            raise LuftdatenError
        except asyncio.TimeoutError:
            _LOGGER.warning("REST request timeout")
            self.data = None
            raise LuftdatenError
