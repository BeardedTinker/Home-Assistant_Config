""" Sensor """
from dateutil.relativedelta import relativedelta
from datetime import datetime, date

from homeassistant.helpers.entity import Entity, generate_entity_id
from homeassistant.components.sensor import ENTITY_ID_FORMAT
from homeassistant.helpers import template as templater

from homeassistant.const import (
    CONF_NAME,
    ATTR_ATTRIBUTION,
)

from .const import (
    ATTRIBUTION,
    DEFAULT_UNIT_OF_MEASUREMENT,
    CONF_ICON_NORMAL,
    CONF_ICON_TODAY,
    CONF_ICON_SOON,
    CONF_DATE,
    CONF_DATE_TEMPLATE,
    CONF_DATE_FORMAT,
    CONF_SOON,
    CONF_HALF_ANNIVERSARY,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_ID_PREFIX,
    CONF_ONE_TIME,
)

ATTR_YEARS_NEXT = "years_at_next_anniversary"
ATTR_YEARS_CURRENT = "current_years"
ATTR_DATE = "date"
ATTR_WEEKS = "weeks_remaining"
ATTR_HALF_DATE = "half_anniversary_date"
ATTR_HALF_DAYS = "days_until_half_anniversary"

async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Setup the sensor platform."""
    async_add_entities([anniversaries(hass, discovery_info)], True)

async def async_setup_entry(hass, config_entry, async_add_devices):
    """Setup sensor platform."""
    async_add_devices([anniversaries(hass, config_entry.data)], True)

def validate_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d"), False
    except ValueError:
        pass
    try:
        return datetime.strptime(value, "%m-%d"), True
    except ValueError:
            return "Invalid Date", False

class anniversaries(Entity):
    def __init__(self, hass, config):
        """Initialize the sensor."""
        self.config = config
        self._name = config.get(CONF_NAME)
        self._id_prefix = config.get(CONF_ID_PREFIX)
        if self._id_prefix is None:
            self._id_prefix = "anniversary_"
        self.entity_id = generate_entity_id(ENTITY_ID_FORMAT, self._id_prefix + self._name, [])
        self._unknown_year = False
        self._date = ""
        self._show_half_anniversary = config.get(CONF_HALF_ANNIVERSARY)
        self._half_days_remaining = 0
        self._half_date = ""
        self._template_sensor = False
        self._date_template = config.get(CONF_DATE_TEMPLATE)
        if self._date_template is not None:
            self._template_sensor = True
        else:
            self._date, self._unknown_year = validate_date(config.get(CONF_DATE))
            if self._show_half_anniversary:
                self._half_date = self._date + relativedelta(months=+6)
        self._icon_normal = config.get(CONF_ICON_NORMAL)
        self._icon_today = config.get(CONF_ICON_TODAY)
        self._icon_soon = config.get(CONF_ICON_SOON)
        self._soon = config.get(CONF_SOON)
        self._date_format = config.get(CONF_DATE_FORMAT)
        self._icon = self._icon_normal
        self._years_next = 0
        self._years_current = 0
        self._state = 0
        self._weeks_remaining = 0
        self._unit_of_measurement = config.get(CONF_UNIT_OF_MEASUREMENT)
        if self._unit_of_measurement is None:
            self._unit_of_measurement = DEFAULT_UNIT_OF_MEASUREMENT
        self._one_time = config.get(CONF_ONE_TIME)

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
    def device_state_attributes(self):
        """Return the state attributes."""
        res = {}
        res[ATTR_ATTRIBUTION] = ATTRIBUTION
        if self._state in ["Invalid Date", "Invalid Template"]:
            return res
        if not self._unknown_year:
            res[ATTR_YEARS_NEXT] = self._years_next
            res[ATTR_YEARS_CURRENT] = self._years_current
        try:
            res[ATTR_DATE] = datetime.strftime(self._date,self._date_format)
        except:
            res[ATTR_DATE] = self._date
        res[ATTR_WEEKS] = self._weeks_remaining
        if self._show_half_anniversary:
            try:
                res[ATTR_HALF_DATE] = datetime.strftime(self._half_date, self._date_format)
            except:
                res[ATTR_HALF_DATE] = self._half_date
            res[ATTR_HALF_DAYS] = self._half_days_remaining
        return res

    @property
    def icon(self):
        return self._icon

    @property
    def unit_of_measurement(self):
        """Return the unit this state is expressed in."""
        if self._state in ["Invalid Date", "Invalid Template"]:
            return
        return self._unit_of_measurement

    async def async_update(self):
        """update the sensor"""
        if self._template_sensor:
            try:
                template_date = templater.Template(self._date_template, self.hass).async_render()
                self._date, self._unknown_year = validate_date(template_date)
            except:
                self._state = "Invalid Template"
                return
            if self._date == "Invalid Date":
                self._state = self._date
                return
        
        today = date.today()
        years = today.year - self._date.year
        nextDate = self._date.date()

        if today >= self._date.date() + relativedelta(year=today.year):
            years = years + 1
            
        if not self._one_time:
            if today >= nextDate:
                nextDate = self._date.date() + relativedelta(year=today.year)
            if today > nextDate:
                nextDate = self._date.date() + relativedelta(year=today.year + 1)

        daysRemaining = (nextDate - today).days

        if self._unknown_year:
            self._date = datetime(nextDate.year, nextDate.month, nextDate.day)

        if daysRemaining == 0:
            self._icon = self._icon_today
        elif daysRemaining <= self._soon:
            self._icon = self._icon_soon
        else:
            self._icon = self._icon_normal

        self._state = daysRemaining
        self._years_next = years
        self._years_current = years - 1
        self._weeks_remaining = int(daysRemaining / 7)

        if self._show_half_anniversary:
            nextHalfDate = self._half_date.date()
            if today > nextHalfDate:
                nextHalfDate = self._half_date.date() + relativedelta(year = today.year)
            if today > nextHalfDate:
                nextHalfDate = self._half_date.date() + relativedelta(year = today.year + 1)
            self._half_days_remaining = (nextHalfDate - today).days
            self._half_date = datetime(nextHalfDate.year, nextHalfDate.month, nextHalfDate.day)
