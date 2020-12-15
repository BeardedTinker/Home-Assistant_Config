"""Constants for the Reolink Camera integration."""

DOMAIN = "reolink_dev"
DOMAIN_DATA = "reolink_dev_devices"
EVENT_DATA_RECEIVED = "reolink_dev-event"
COORDINATOR = "coordinator"
BASE = "base"
SESSION_RENEW_THRESHOLD = 300

CONF_STREAM = "stream"
CONF_PROTOCOL = "protocol"
CONF_CHANNEL = "channel"
CONF_MOTION_OFF_DELAY = "motion_off_delay"

DEFAULT_CHANNEL = 1
DEFAULT_MOTION_OFF_DELAY = 60
DEFAULT_STREAM = "main"
DEFAULT_TIMEOUT = 10

SERVICE_PTZ_CONTROL = "ptz_control"
SERVICE_SET_SENSITIVITY = "set_sensitivity"
SERVICE_SET_DAYNIGHT = "set_daynight"
