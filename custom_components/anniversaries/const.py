""" Constants """
import voluptuous as vol
from datetime import datetime, date
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_NAME


# Base component constants
DOMAIN = "anniversaries"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "3.2.0"
PLATFORM = "sensor"
ISSUE_URL = "https://github.com/pinkywafer/Anniversaries/issues"
ATTRIBUTION = "Data from this is provided by Anniversaries"

ATTR_YEARS_NEXT = "years_at_next_anniversary"
ATTR_YEARS_CURRENT = "current_years"
ATTR_DATE = "date"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"

# Configuration
CONF_SENSOR = "sensor"
CONF_ENABLED = "enabled"
CONF_DATE = "date"
CONF_ICON_NORMAL = "icon_normal"
CONF_ICON_TODAY = "icon_today"
CONF_ICON_SOON = "icon_soon"
CONF_DATE_FORMAT = "date_format"
CONF_SENSORS = "sensors"
CONF_SOON = "days_as_soon"
CONF_HALF_ANNIVERSARY = "show_half_anniversary"
CONF_UNIT_OF_MEASUREMENT = "unit_of_measurement"
CONF_ID_PREFIX = "id_prefix"
CONF_ONE_TIME = "one_time"

# Defaults
DEFAULT_NAME = DOMAIN
DEFAULT_ICON_NORMAL = "mdi:calendar-blank"
DEFAULT_ICON_TODAY = "mdi:calendar-star"
DEFAULT_ICON_SOON = "mdi:calendar"
DEFAULT_DATE_FORMAT = "%Y-%m-%d"
DEFAULT_SOON = 1
DEFAULT_HALF_ANNIVERSARY = False
DEFAULT_UNIT_OF_MEASUREMENT = "Days"
DEFAULT_ID_PREFIX = "anniversary_"
DEFAULT_ONE_TIME = False

ICON = DEFAULT_ICON_NORMAL

def check_date(value):
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().strftime("%Y-%m-%d")
    except ValueError:
        pass
    try:
        return datetime.strptime(value, "%m-%d").date().strftime("%m-%d")
    except ValueError:
        raise vol.Invalid(f"Invalid date: {value}")


SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_DATE): check_date,
        vol.Optional(CONF_SOON, default=DEFAULT_SOON): cv.positive_int,
        vol.Optional(CONF_ICON_NORMAL, default=DEFAULT_ICON_NORMAL): cv.icon,
        vol.Optional(CONF_ICON_TODAY, default=DEFAULT_ICON_TODAY): cv.icon,
        vol.Optional(CONF_ICON_SOON, default=DEFAULT_ICON_SOON): cv.icon,
        vol.Optional(CONF_DATE_FORMAT, default=DEFAULT_DATE_FORMAT): cv.string,
        vol.Optional(CONF_HALF_ANNIVERSARY, default=DEFAULT_HALF_ANNIVERSARY): cv.boolean,
        vol.Optional(CONF_UNIT_OF_MEASUREMENT, default=DEFAULT_UNIT_OF_MEASUREMENT): cv.string,
        vol.Optional(CONF_ID_PREFIX, default=DEFAULT_ID_PREFIX): cv.string,
        vol.Optional(CONF_ONE_TIME, default=DEFAULT_ONE_TIME): cv.boolean,
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {vol.Optional(CONF_SENSORS): vol.All(cv.ensure_list, [SENSOR_SCHEMA])}
        )
    },
    extra=vol.ALLOW_EXTRA,
)
