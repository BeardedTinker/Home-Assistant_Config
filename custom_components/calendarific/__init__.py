"""Calendarific Platform"""
from datetime import datetime, date
import logging
import json 
import requests

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import HomeAssistantType

from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    ISSUE_URL,
    VERSION,
)

CONF_API_KEY = "api_key"
CONF_COUNTRY = "country"
CONF_STATE = "state"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_API_KEY): cv.string,
                vol.Required(CONF_COUNTRY): cv.string,
                vol.Optional(CONF_STATE, default=''): cv.string
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

_LOGGER = logging.getLogger(__name__)

holiday_list = []

def setup(hass, config):
    """Set up platform using YAML."""
    if DOMAIN in config:
        api_key = config[DOMAIN].get(CONF_API_KEY)
        country = config[DOMAIN].get(CONF_COUNTRY)
        state = config[DOMAIN].get(CONF_STATE)
        reader =  CalendarificApiReader(api_key, country, state)

        hass.data[DOMAIN] = {
            'apiReader': reader
        }
    return True


async def async_setup_entry(hass: HomeAssistantType, entry: ConfigEntry):
    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, "sensor")
    )
    return True

async def async_unload_entry(hass, entry):
    """Unload a config entry."""
    return await hass.config_entries.async_forward_entry_unload(entry, "sensor")

class CalendarificApiReader:

    def __init__(self, api_key, country, state):
        self._country = country
        self._state = state
        self._api_key = api_key
        self._lastupdated = None
        _LOGGER.debug("apiReader loaded")
        self._holidays = []
        self.next_holidays = []
        self._error_logged = False
        self.update()
    
    def get_state(self):
        return "new"
    
    def get_date(self,holiday_name):
        try:
            today = date.today()
            holiday_datetime = next(i for i in self._holidays if i['name'] == holiday_name)['date']['datetime']
            testdate = date(holiday_datetime['year'],holiday_datetime['month'],holiday_datetime['day'])
            if testdate < today:
                holiday_datetime = next(i for i in self._next_holidays if i['name'] == holiday_name)['date']['datetime']
                testdate = date(holiday_datetime['year'],holiday_datetime['month'],holiday_datetime['day'])
            return testdate
        except:
            return "-"
    
    def get_description(self,holiday_name):
        try:
            return next(i for i in self._holidays if i['name'] == holiday_name)['description']
        except:
            return "NOT FOUND"

    def update(self):
        if self._lastupdated == datetime.now().date():
            return
        self._lastupdated = datetime.now().date()
        year = date.today().year
        params = {'country': self._country,'year': year,'location': self._state}
        calapi = calendarificAPI(self._api_key)
        response = calapi.holidays(params)
        _LOGGER.debug("Updating from Calendarific api")
        if 'error' in response:
            if not self._error_logged:
                _LOGGER.error(response['meta']['error_detail'])
                self._error_logged = True
            return
        self._holidays = response['response']['holidays']
        params['year'] = year + 1
        response = calapi.holidays(params)
        if 'error' in response:
            if not self._error_logged:
                _LOGGER.error(response['meta']['error_detail'])
                self._error_logged = True
            return
        self._error_logged = False
        self._next_holidays = response['response']['holidays']
        global holiday_list
        holiday_list = []
        for holiday in self._holidays:
            holiday_list.append(holiday['name'])
        
        return True

class calendarificAPI:
    api_key = None

    def __init__(self, api_key):
        self.api_key = api_key

    def holidays(self, parameters):
        url = 'https://calendarific.com/api/v2/holidays?'

        if 'api_key' not in parameters:
            parameters['api_key'] = self.api_key

        response = requests.get(url, params=parameters);
        data     = json.loads(response.text)

        if response.status_code != 200:
            if 'error' not in data:
                data['error'] = 'Unknown error.'

        return data
