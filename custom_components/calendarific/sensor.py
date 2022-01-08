""" Calendarific Sensor """
from datetime import datetime, date
import logging

import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA

from homeassistant.const import CONF_NAME, ATTR_ATTRIBUTION
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

from .const import (
    ATTRIBUTION,
    DEFAULT_SOON,
    DEFAULT_ICON_SOON,
    DEFAULT_ICON_NORMAL,
    DEFAULT_ICON_TODAY,
    DEFAULT_DATE_FORMAT,
    DEFAULT_UNIT_OF_MEASUREMENT,
    CONF_ICON_NORMAL,
    CONF_ICON_TODAY,
    CONF_ICON_SOON,
    CONF_DATE_FORMAT,
    CONF_SOON,
    CONF_HOLIDAY,
    CONF_UNIT_OF_MEASUREMENT,
    DOMAIN,
)

ATTR_DESCRIPTION = "description"
ATTR_DATE = "date"

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_HOLIDAY): cv.string,
        vol.Optional(CONF_NAME, default=''): cv.string,
        vol.Optional(CONF_SOON, default=DEFAULT_SOON): cv.positive_int,
        vol.Optional(CONF_ICON_NORMAL, default=DEFAULT_ICON_NORMAL): cv.icon,
        vol.Optional(CONF_ICON_TODAY, default=DEFAULT_ICON_TODAY): cv.icon,
        vol.Optional(CONF_ICON_SOON, default=DEFAULT_ICON_SOON): cv.icon,
        vol.Optional(CONF_DATE_FORMAT, default=DEFAULT_DATE_FORMAT): cv.string,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=DEFAULT_UNIT_OF_MEASUREMENT): cv.string,
    }
)

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the sensor platform."""
    if DOMAIN in hass.data:
        reader = hass.data[DOMAIN]['apiReader']
        async_add_entities([calendarific(config, reader)],True)  
     
async def async_setup_entry(hass, entry, async_add_entities):
    """Setup sensor platform."""
    if DOMAIN in hass.data:
        reader = hass.data[DOMAIN]['apiReader']
        async_add_entities(
            [calendarific(entry.data, reader)], False,
        )
    return True


class calendarific(Entity):
    def __init__(self, config, reader):
        """Initialize the sensor."""
        self.config = config
        self._holiday = config.get(CONF_HOLIDAY)
        self._name = config.get(CONF_NAME)
        if self._name == '':
            self._name = self._holiday
        self._icon_normal = config.get(CONF_ICON_NORMAL)
        self._icon_today = config.get(CONF_ICON_TODAY)
        self._icon_soon = config.get(CONF_ICON_SOON)
        self._soon = config.get(CONF_SOON)
        self._date_format = config.get(CONF_DATE_FORMAT)
        self._unit_of_measurement = config.get(CONF_UNIT_OF_MEASUREMENT)
        if self._unit_of_measurement is None:
            self._unit_of_measurement = DEFAULT_UNIT_OF_MEASUREMENT
        self._icon = self._icon_normal
        self._reader = reader
        self._description = self._reader.get_description(self._holiday)
        self._date = self._reader.get_date(self._holiday)
        if self._date == "-":
            self._attr_date = self._date
        else:
            self._attr_date = datetime.strftime(self._date,self._date_format)
        self._state = "unknown"

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return self.config.get("unique_id", None)
        
    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the name of the sensor."""
        return self._state

    @property 
    def extra_state_attributes(self):
        """Return the state attributes."""
        return {
            ATTR_DATE: self._attr_date,
            ATTR_DESCRIPTION: self._description,
            ATTR_ATTRIBUTION: ATTRIBUTION,
        }

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        return self._unit_of_measurement

    @property
    def icon(self):
        return self._icon

    async def async_added_to_hass(self):
        """Once the entity is added we should update to get the initial data loaded."""
        self.async_schedule_update_ha_state(True)

    async def async_update(self):
        await self.hass.async_add_executor_job(self._reader.update)
        self._description = self._reader.get_description(self._holiday)
        self._date = self._reader.get_date(self._holiday)
        if self._date == "-":
            self._state = "unknown"
            self._attr_date = self._date
            return
        self._attr_date = datetime.strftime(self._date,self._date_format)
        today = date.today()
        daysRemaining = 0
        if today < self._date:
            daysRemaining = (self._date - today).days
        elif today == self._date:
            daysRemaining = 0
            
        if daysRemaining == 0:
            self._icon = self._icon_today
        elif daysRemaining <= self._soon:
            self._icon = self._icon_soon
        else:
            self._icon = self._icon_normal
        self._state = daysRemaining