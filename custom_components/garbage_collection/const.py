"""Define constants used in garbage_collection."""
from homeassistant.helpers import selector

# Constants for garbage_collection.
# Base component constants
DOMAIN = "garbage_collection"
CALENDAR_NAME = "Garbage Collection"
SENSOR_PLATFORM = "sensor"
CALENDAR_PLATFORM = "calendar"
ATTRIBUTION = "Data from this is provided by garbage_collection."
CONFIG_VERSION = 6

ATTR_NEXT_DATE = "next_date"
ATTR_DAYS = "days"
ATTR_LAST_COLLECTION = "last_collection"
ATTR_LAST_UPDATED = "last_updated"

# Device classes
BINARY_SENSOR_DEVICE_CLASS = "connectivity"
DEVICE_CLASS = "garbage_collection__schedule"

# Configuration
CONF_SENSOR = "sensor"
CONF_ENABLED = "enabled"
CONF_FREQUENCY = "frequency"
CONF_MANUAL = "manual_update"
CONF_ICON_NORMAL = "icon_normal"
CONF_ICON_TODAY = "icon_today"
CONF_ICON_TOMORROW = "icon_tomorrow"
CONF_OFFSET = "offset"
CONF_EXPIRE_AFTER = "expire_after"
CONF_VERBOSE_STATE = "verbose_state"
CONF_FIRST_MONTH = "first_month"
CONF_LAST_MONTH = "last_month"
CONF_COLLECTION_DAYS = "collection_days"
CONF_WEEKDAY_ORDER_NUMBER = "weekday_order_number"
CONF_FORCE_WEEK_NUMBERS = "force_week_order_numbers"
CONF_WEEK_ORDER_NUMBER = "week_order_number"  # Obsolete
CONF_DATE = "date"
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
    selector.SelectOptionDict(value="weekly", label="weekly"),
    selector.SelectOptionDict(value="even-weeks", label="even-weeks"),
    selector.SelectOptionDict(value="odd-weeks", label="odd-weeks"),
    selector.SelectOptionDict(value="every-n-weeks", label="every-n-weeks"),
    selector.SelectOptionDict(value="every-n-days", label="every-n-days"),
    selector.SelectOptionDict(value="monthly", label="monthly"),
    selector.SelectOptionDict(value="annual", label="annual"),
    selector.SelectOptionDict(value="blank", label="blank"),
    selector.SelectOptionDict(value="group", label="group"),
]

WEEKLY_FREQUENCY = ["weekly", "even-weeks", "odd-weeks"]
EXCEPT_ANNUAL_GROUP = [
    "weekly",
    "even-weeks",
    "odd-weeks",
    "every-n-weeks",
    "every-n-days",
    "monthly",
    "blank",
]
EXCEPT_ANNUAL_GROUP_BLANK = [
    "weekly",
    "even-weeks",
    "odd-weeks",
    "every-n-weeks",
    "every-n-days",
    "monthly",
]
WEEKLY_DAILY_MONTHLY = ["every-n-weeks", "every-n-days", "monthly"]
WEEKLY_FREQUENCY_X = ["every-n-weeks"]
DAILY_FREQUENCY = ["every-n-days"]
DAILY_BLANK_FREQUENCY = ["blank", "every-n-days"]
MONTHLY_FREQUENCY = ["monthly"]
ANNUAL_GROUP_FREQUENCY = ["annual", "group"]
ANNUAL_FREQUENCY = ["annual"]
GROUP_FREQUENCY = ["group"]
BLANK_FREQUENCY = ["blank"]

WEEKDAY_OPTIONS = [
    selector.SelectOptionDict(value="mon", label="Monday"),
    selector.SelectOptionDict(value="tue", label="Tuesday"),
    selector.SelectOptionDict(value="wed", label="Wednesday"),
    selector.SelectOptionDict(value="thu", label="Thursday"),
    selector.SelectOptionDict(value="fri", label="Friday"),
    selector.SelectOptionDict(value="sat", label="Saturday"),
    selector.SelectOptionDict(value="sun", label="Sunday"),
]


MONTH_OPTIONS = [
    selector.SelectOptionDict(value="jan", label="January"),
    selector.SelectOptionDict(value="feb", label="February"),
    selector.SelectOptionDict(value="mar", label="March"),
    selector.SelectOptionDict(value="apr", label="April"),
    selector.SelectOptionDict(value="may", label="May"),
    selector.SelectOptionDict(value="jun", label="June"),
    selector.SelectOptionDict(value="jul", label="July"),
    selector.SelectOptionDict(value="aug", label="August"),
    selector.SelectOptionDict(value="sep", label="September"),
    selector.SelectOptionDict(value="oct", label="October"),
    selector.SelectOptionDict(value="nov", label="November"),
    selector.SelectOptionDict(value="dec", label="December"),
]

ORDER_OPTIONS = [
    selector.SelectOptionDict(value="1", label="1st"),
    selector.SelectOptionDict(value="2", label="2nd"),
    selector.SelectOptionDict(value="3", label="3rd"),
    selector.SelectOptionDict(value="4", label="4th"),
    selector.SelectOptionDict(value="5", label="5th"),
]
