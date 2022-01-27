import asyncio
import json
import logging
import re
import voluptuous as vol
from datetime import date, datetime, timedelta

from homeassistant.components.sensor import PLATFORM_SCHEMA
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.discovery import async_load_platform

REQUIREMENTS = [ ]

_LOGGER = logging.getLogger(__name__)

CONF_ATTRIBUTION = ""
CONF_ANNIVERSARIES = "anniversaries"
CONF_DATE_FORMAT = "date_format"
CONF_ITEMS = 'items'
CONF_MULTIPLE = 'multiple'
CONF_NAME = 'name'
CONF_UNIT = 'unit_of_measurement'

DEFAULT_ANNIVERSARIES = ''
DEFAULT_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_ICON = 'mdi:calendar'
DEFAULT_ITEMS = 0
DEFAULT_MULTIPLE = 'false'
DEFAULT_NAME = 'events'
DEFAULT_TYPE = 'event'
DEFAULT_UNIT = ''

SCAN_INTERVAL = timedelta(minutes=5)
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_ANNIVERSARIES, default=DEFAULT_ANNIVERSARIES): cv.ensure_list,
    vol.Optional(CONF_DATE_FORMAT, default=DEFAULT_DATE_FORMAT): cv.string,
    vol.Optional(CONF_ITEMS, default=DEFAULT_ITEMS): cv.string,
    vol.Optional(CONF_MULTIPLE, default=DEFAULT_MULTIPLE): cv.boolean,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
    vol.Optional(CONF_UNIT, default=DEFAULT_UNIT): cv.string,
})

# get anniversary date
# if specified date does not include year, add current year according to formatting
def _get_anniversary_date(self, i, year):
    m = re.search('(^\d{1,2}.\d{1,2}$)',self._anniversaries[i]['date'])
    if m is not None:
    # yY bBm d - cx
        m = self._date_format.find("%Y")
        if m == -1:
            m = self._date_format.find("%y")
            if m != -1:
                year = str(int(year) % 1000)

        if m == len(self._date_format) - 2:
             mydate = self._anniversaries[i]['date'][:m] + "-" + str(year) + self._anniversaries[i]['date'][m:]
        else:
             mydate = self._anniversaries[i]['date'][:m] + str(year) + "-" + self._anniversaries[i]['date'][m:]
    else:
        mydate = self._anniversaries[i]['date']

    try:
        mydate_p = datetime.strptime(mydate,self._date_format)
    except ValueError:
        _LOGGER.warning("anniversary: format of the date specified does not match date_format parameter... ignoring event " + self._anniversaries[i]['date'])
        mydate_p = None

    return mydate_p

@asyncio.coroutine
def async_setup_platform(hass, config, async_add_devices, discovery_info=None):
    name = config.get(CONF_NAME)
    anniversaries = config.get(CONF_ANNIVERSARIES)
    date_format = config.get(CONF_DATE_FORMAT)
    items = int(config.get(CONF_ITEMS))
    multiple = config.get(CONF_MULTIPLE)
    unit = config.get(CONF_UNIT)

    async_add_devices(
        [AnniversarySensor(hass, name, anniversaries, date_format, multiple, unit, items )],update_before_add=True)

class AnniversarySensor(Entity):

    def __init__(self, hass, name, anniversaries, date_format, multiple, unit, items):
        """Initialize the sensor."""
        self._hass = hass
        self._name = name
        self._anniversaries = anniversaries
        self._items = items
        self._multiple = multiple
        self._unit = unit
        self._state = None
        self._icon = DEFAULT_ICON
        try:
             today = datetime.today().strftime(date_format)
             self._date_format = date_format
        except ValueError:
             self._date_format = DEFAULT_DATE_FORMAT

    @property
    def extra_state_attributes(self):
        attr = {}
        first_anni = 367
        first_event_in = 0
        first_event_name = ""
        event_anniversary = ""
        event_icon = ""
        event_on = ""
        events_list = ""
        first_event_on = ""
        first_event_anniversary = None
        today = datetime.today().strftime(self._date_format)
        today_p = datetime.strptime(today,self._date_format)
        attr_ext = {}

        for i in range(len(self._anniversaries)):
            if 'date' in self._anniversaries[i]:
                next_year = False
                anni_date_p = _get_anniversary_date(self, i, today_p.year)

                if anni_date_p is not None:
                    this_year = str(today_p.year) + "-" + str(anni_date_p.month) + "-" + str(anni_date_p.day)
                    this_year_p = datetime.strptime(this_year,"%Y-%m-%d")
                    ddiff = (this_year_p - today_p).days
                    if ddiff < 0:
                        ddiff += 365
                        next_year = True

                    if next_year:
                        event_on = str(today_p.year + 1) + "-" + str(anni_date_p.month) + "-" + str(anni_date_p.day)
                    else:
                        event_on = this_year
                    event_on = datetime.strptime(event_on,"%Y-%m-%d").strftime(self._date_format)

                    m = re.search('(^\d{1,2}.\d{1,2}$)',self._anniversaries[i]['date'])
                    if m is None: # date contains year as well
                        if next_year:
                            event_anniversary = int(today_p.year - anni_date_p.year + 1)
                        else:
                            event_anniversary = int(today_p.year - anni_date_p.year)
                    else:
                        event_anniversary = None

                    if ddiff < first_anni:
                        first_anni = ddiff
                        if 'event' in self._anniversaries[i]:
                            first_event_name = self._anniversaries[i]['event']

                        first_event_on = event_on

                        first_event_anniversary = event_anniversary
                    elif ddiff == first_anni and self._multiple:
                        if 'event' in self._anniversaries[i]:
                            first_event_name += "|" + self._anniversaries[i]['event']

                    if ddiff not in attr_ext and self._items > 0:
                        if 'icon' in self._anniversaries[i]:
                            event_icon = self._anniversaries[i]['icon']
                        else:
                            event_icon = DEFAULT_ICON

                        if 'type' in self._anniversaries[i]:
                            event_type = self._anniversaries[i]['type']
                        else:
                            event_type = DEFAULT_TYPE

                        attr_ext[ddiff] = "{ \"event\":\"" + self._anniversaries[i]['event'] + \
                            "\", \"event_in\":\"" + str(ddiff) + \
                            "\", \"event_on\":\"" + event_on + \
                            "\", \"anniversary\":\"" + str(event_anniversary) + \
                            "\", \"type\":\"" + event_type + \
                            "\", \"icon\":\"" + event_icon + "\"}"

        if self._unit != "":
            attr["unit_of_measurement"] = self._unit
        attr["first_event_name"] = first_event_name
        attr["first_event_in"] = first_anni
        attr["first_event_on"] = first_event_on
        if first_event_anniversary is not None:
            attr["anniversary"] = first_event_anniversary

        if self._items > 0:
            events_list = "["
            for key,value in sorted(attr_ext.items())[:self._items]:
                events_list = events_list + value + ","
            events_list = events_list[:-1] + "]"
            attr["events"] = json.loads(events_list)

        return attr

    @asyncio.coroutine
    async def async_update(self):
        first_anni = 367
        today = datetime.today().strftime(self._date_format)
        today_p = datetime.strptime(today,self._date_format)

        for i in range(len(self._anniversaries)):
            if 'date' in self._anniversaries[i]:
                anni_date_p = _get_anniversary_date(self, i, today_p.year)
                if anni_date_p is not None:
                    this_year = str(today_p.year) + "-" + str(anni_date_p.month) + "-" + str(anni_date_p.day)
                    this_year_p = datetime.strptime(this_year,"%Y-%m-%d")
                    ddiff = (this_year_p - today_p).days
                    if ddiff < 0:
                        ddiff += 365
                    if ddiff < first_anni:
                        first_anni = ddiff
                        if 'icon' in self._anniversaries[i]:
                            self._icon = self._anniversaries[i]['icon']
                        else:
                            self._icon = DEFAULT_ICON

        self._state = first_anni
        return self._state

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def icon(self):
        return self._icon
