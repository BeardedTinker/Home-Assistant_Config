import voluptuous as vol
from .config_singularity import config_singularity
from datetime import datetime, date
import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_NAME, WEEKDAYS, CONF_ENTITIES, ATTR_HIDDEN

"""Constants for garbage_collection."""
# Base component constants
DOMAIN = "garbage_collection"
CALENDAR_NAME = "Garbage Collection"
VERSION = "3.02"
SENSOR_PLATFORM = "sensor"
CALENDAR_PLATFORM = "calendar"
ISSUE_URL = "https://github.com/bruxy70/Garbage-Collection/issues"
ATTRIBUTION = "Data from this is provided by garbage_collection."

ATTR_NEXT_DATE = "next_date"
ATTR_DAYS = "days"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"
DEVICE_CLASS = "garbage_collection__schedule"

# Configuration
CONF_SENSOR = "sensor"
CONF_ENABLED = "enabled"
CONF_FREQUENCY = "frequency"
CONF_ICON_NORMAL = "icon_normal"
CONF_ICON_TODAY = "icon_today"
CONF_ICON_TOMORROW = "icon_tomorrow"
CONF_OFFSET = "offset"
CONF_EXPIRE_AFTER = "expire_after"
CONF_VERBOSE_STATE = "verbose_state"
CONF_FIRST_MONTH = "first_month"
CONF_LAST_MONTH = "last_month"
CONF_COLLECTION_DAYS = "collection_days"
CONF_FORCE_WEEK_NUMBERS = "force_week_order_numbers"
CONF_WEEKDAY_ORDER_NUMBER = "weekday_order_number"
CONF_WEEK_ORDER_NUMBER = "week_order_number"
CONF_DATE = "date"
CONF_EXCLUDE_DATES = "exclude_dates"
CONF_INCLUDE_DATES = "include_dates"
CONF_MOVE_COUNTRY_HOLIDAYS = "move_country_holidays"
CONF_HOLIDAY_IN_WEEK_MOVE = "holiday_in_week_move"
CONF_PROV = "prov"
CONF_STATE = "state"
CONF_OBSERVED = "observed"
CONF_PERIOD = "period"
CONF_FIRST_WEEK = "first_week"
CONF_FIRST_DATE = "first_date"
CONF_SENSORS = "sensors"
CONF_VERBOSE_FORMAT = "verbose_format"
CONF_DATE_FORMAT = "date_format"

# Defaults
DEFAULT_NAME = DOMAIN
DEFAULT_FIRST_MONTH = "jan"
DEFAULT_LAST_MONTH = "dec"
DEFAULT_FREQUENCY = "weekly"
DEFAULT_PERIOD = 1
DEFAULT_FIRST_WEEK = 1
DEFAULT_VERBOSE_STATE = False
DEFAULT_HOLIDAY_IN_WEEK_MOVE = False
DEFAULT_DATE_FORMAT = "%d-%b-%Y"
DEFAULT_VERBOSE_FORMAT = "on {date}, in {days} days"

# Icons
DEFAULT_ICON_NORMAL = "mdi:trash-can"
DEFAULT_ICON_TODAY = "mdi:delete-restore"
DEFAULT_ICON_TOMORROW = "mdi:delete-circle"
ICON = DEFAULT_ICON_NORMAL

# States
STATE_TODAY = "today"
STATE_TOMORROW = "tomorrow"

FREQUENCY_OPTIONS = [
    "weekly",
    "even-weeks",
    "odd-weeks",
    "every-n-weeks",
    "every-n-days",
    "monthly",
    "annual",
    "group",
]

WEEKLY_FREQUENCY = ["weekly", "even-weeks", "odd-weeks"]
EXCEPT_ANNUAL_GROUP = [
    "weekly",
    "even-weeks",
    "odd-weeks",
    "every-n-weeks",
    "every-n-days",
    "monthly",
]
WEEKLY_DAILY = ["every-n-weeks", "every-n-days"]
WEEKLY_FREQUENCY_X = ["every-n-weeks"]
DAILY_FREQUENCY = ["every-n-days"]
MONTHLY_FREQUENCY = ["monthly"]
ANNUAL_GROUP_FREQUENCY = ["annual", "group"]
ANNUAL_FREQUENCY = ["annual"]
GROUP_FREQUENCY = ["group"]

MONTH_OPTIONS = [
    "jan",
    "feb",
    "mar",
    "apr",
    "may",
    "jun",
    "jul",
    "aug",
    "sep",
    "oct",
    "nov",
    "dec",
]

COUNTRY_CODES = [
    "",
    "AR",
    "AT",
    "AU",
    "AW",
    "BE",
    "BG",
    "BR",
    "BY",
    "CA",
    "CH",
    "CO",
    "CZ",
    "DE",
    "DK",
    "DO",
    "ECB",
    "EE",
    "ES",
    "FI",
    "FRA",
    "HR",
    "HU",
    "IE",
    "IND",
    "IS",
    "IT",
    "JP",
    "KE",
    "LT",
    "LU",
    "MX",
    "NG",
    "NI",
    "NL",
    "NO",
    "NZ",
    "PE",
    "PL",
    "PT",
    "PTE",
    "RU",
    "SE",
    "SI",
    "SK",
    "UA",
    "UK",
    "US",
    "ZA",
]


def date_text(value):
    """Have to store date as text - datetime is not JSON serialisable"""
    if value is None or value == "":
        return ""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().strftime("%Y-%m-%d")
    except ValueError:
        raise vol.Invalid(f"Invalid date: {value}")


def time_text(value):
    """Have to store time as text - datetime is not JSON serialisable"""
    if value is None or value == "":
        return ""
    try:
        return datetime.strptime(value, "%H:%M").time().strftime("%H:%M")
    except ValueError:
        raise vol.Invalid(f"Invalid date: {value}")


def month_day_text(value):
    if value is None or value == "":
        return ""
    try:
        return datetime.strptime(value, "%m/%d").date().strftime("%m/%d")
    except ValueError:
        raise vol.Invalid(f"Invalid date: {value}")


class configuration(config_singularity):
    """
    Type and validation seems duplicare, but I cannot use custom validators in ShowForm
    It calls convert from voluptuous-serialize that does not accept them
    so I pass it twice - once the type, then the validator :( )
    """

    options = {
        CONF_NAME: {
            "step": 1,
            "method": vol.Required,
            "type": str,
            "validator": cv.string,
        },
        ATTR_HIDDEN: {
            "step": 1,
            "method": vol.Optional,
            "default": False,
            "type": bool,
            "validator": cv.boolean,
        },
        CONF_FREQUENCY: {
            "step": 1,
            "method": vol.Required,
            "default": DEFAULT_FREQUENCY,
            "type": vol.In(FREQUENCY_OPTIONS),
        },
        CONF_OFFSET: {
            "step": 1,
            "method": vol.Optional,
            "default": 0,
            "type": int,
            "validator": vol.All(vol.Coerce(int), vol.Range(min=-31, max=31)),
        },
        CONF_ICON_NORMAL: {
            "step": 1,
            "method": vol.Optional,
            "default": DEFAULT_ICON_NORMAL,
            "type": str,
            "validator": cv.icon,
        },
        CONF_ICON_TODAY: {
            "step": 1,
            "method": vol.Optional,
            "default": DEFAULT_ICON_TODAY,
            "type": str,
            "validator": cv.icon,
        },
        CONF_ICON_TOMORROW: {
            "step": 1,
            "method": vol.Optional,
            "default": DEFAULT_ICON_TOMORROW,
            "type": str,
            "validator": cv.icon,
        },
        CONF_EXPIRE_AFTER: {
            "step": 1,
            "method": vol.Optional,
            "type": str,
            "validator": time_text,
        },
        CONF_VERBOSE_STATE: {
            "step": 1,
            "method": vol.Optional,
            "default": DEFAULT_VERBOSE_STATE,
            "type": bool,
            "validator": cv.boolean,
        },
        CONF_VERBOSE_FORMAT: {
            "step": 1,
            "method": vol.Optional,
            "default": DEFAULT_VERBOSE_FORMAT,
            "type": str,
            "validator": cv.string,
        },
        CONF_DATE_FORMAT: {
            "step": 1,
            "method": vol.Optional,
            "default": DEFAULT_DATE_FORMAT,
            "type": str,
            "validator": cv.string,
        },
        CONF_DATE: {
            "step": 2,
            "valid_for": lambda f: f in ANNUAL_FREQUENCY,
            "method": vol.Optional,
            "type": str,
            "validator": month_day_text,
        },
        CONF_ENTITIES: {
            "step": 2,
            "valid_for": lambda f: f in GROUP_FREQUENCY,
            "method": vol.Optional,
            "type": str,
            "validator": cv.entity_ids,
        },
        CONF_COLLECTION_DAYS: {
            "step": 3,
            "valid_for": lambda f: f in EXCEPT_ANNUAL_GROUP,
            "method": vol.Optional,
            "type": [str],
            "validator": vol.All(cv.ensure_list, [vol.In(WEEKDAYS)]),
        },
        CONF_WEEKDAY_ORDER_NUMBER: {
            "step": 4,
            "valid_for": lambda f: f in MONTHLY_FREQUENCY,
            "method": vol.Optional,
            "type": [int],
            "validator": vol.All(
                cv.ensure_list, [vol.All(vol.Coerce(int), vol.Range(min=1, max=5))]
            ),
        },
        CONF_WEEK_ORDER_NUMBER: {
            "step": 4,
            "valid_for": lambda f: f in MONTHLY_FREQUENCY,
            "method": vol.Optional,
            "type": [int],
            "validator": vol.All(
                cv.ensure_list, [vol.All(vol.Coerce(int), vol.Range(min=1, max=5))]
            ),
        },
        CONF_FIRST_MONTH: {
            "step": 4,
            "valid_for": lambda f: f in EXCEPT_ANNUAL_GROUP,
            "method": vol.Optional,
            "default": DEFAULT_FIRST_MONTH,
            "type": vol.In(MONTH_OPTIONS),
        },
        CONF_LAST_MONTH: {
            "step": 4,
            "valid_for": lambda f: f in EXCEPT_ANNUAL_GROUP,
            "method": vol.Optional,
            "default": DEFAULT_LAST_MONTH,
            "type": vol.In(MONTH_OPTIONS),
        },
        CONF_PERIOD: {
            "step": 4,
            "valid_for": lambda f: f in WEEKLY_DAILY,
            "method": vol.Optional,
            "default": DEFAULT_PERIOD,
            "type": int,
            "validator": vol.All(vol.Coerce(int), vol.Range(min=1, max=52)),
        },
        CONF_FIRST_WEEK: {
            "step": 4,
            "valid_for": lambda f: f in WEEKLY_FREQUENCY_X,
            "method": vol.Optional,
            "default": DEFAULT_FIRST_WEEK,
            "type": int,
            "validator": vol.All(vol.Coerce(int), vol.Range(min=1, max=52)),
        },
        CONF_FIRST_DATE: {
            "step": 4,
            "valid_for": lambda f: f in DAILY_FREQUENCY,
            "method": vol.Optional,
            "type": str,
            "validator": date_text,
        },
        CONF_INCLUDE_DATES: {
            "step": 4,
            "valid_for": lambda f: f in EXCEPT_ANNUAL_GROUP,
            "method": vol.Optional,
            "type": str,
            "validator": vol.All(cv.ensure_list, [date_text]),
        },
        CONF_EXCLUDE_DATES: {
            "step": 4,
            "valid_for": lambda f: f in EXCEPT_ANNUAL_GROUP,
            "method": vol.Optional,
            "type": str,
            "validator": vol.All(cv.ensure_list, [date_text]),
        },
        CONF_MOVE_COUNTRY_HOLIDAYS: {
            "step": 4,
            "valid_for": lambda f: f in EXCEPT_ANNUAL_GROUP,
            "method": vol.Optional,
            "type": vol.In(COUNTRY_CODES),
        },
        CONF_HOLIDAY_IN_WEEK_MOVE: {
            "step": 4,
            "method": vol.Optional,
            "default": DEFAULT_HOLIDAY_IN_WEEK_MOVE,
            "type": bool,
            "validator": cv.boolean,
        },
        CONF_PROV: {
            "step": 4,
            "valid_for": lambda f: f in EXCEPT_ANNUAL_GROUP,
            "method": vol.Optional,
            "type": str,
            "validator": cv.string,
        },
        CONF_STATE: {
            "step": 4,
            "valid_for": lambda f: f in EXCEPT_ANNUAL_GROUP,
            "method": vol.Optional,
            "type": str,
            "validator": cv.string,
        },
        CONF_OBSERVED: {
            "step": 4,
            "valid_for": lambda f: f in EXCEPT_ANNUAL_GROUP,
            "method": vol.Optional,
            "default": True,
            "type": bool,
            "validator": cv.boolean,
        },
    }


extra_options = {
    CONF_FORCE_WEEK_NUMBERS: {
        "valid_for": lambda f: f in MONTHLY_FREQUENCY,
        "method": vol.Optional,
        "default": False,
        "type": bool,
        "validator": cv.boolean,
    }
}

config_definition = configuration()

SENSOR_SCHEMA = vol.Schema(config_definition.compile_schema())

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {vol.Optional(CONF_SENSORS): vol.All(cv.ensure_list, [SENSOR_SCHEMA])}
        )
    },
    extra=vol.ALLOW_EXTRA,
)
