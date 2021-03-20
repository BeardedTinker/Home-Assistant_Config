"""Constants for the Reolink Camera integration."""

DOMAIN = "reolink_dev"
DOMAIN_DATA = "reolink_dev_devices"
EVENT_DATA_RECEIVED = "reolink_dev-event"
COORDINATOR = "coordinator"
BASE = "base"
PUSH_MANAGER = "push_manager"
SESSION_RENEW_THRESHOLD = 300

CONF_STREAM = "stream"
CONF_PROTOCOL = "protocol"
CONF_CHANNEL = "channel"
CONF_MOTION_OFF_DELAY = "motion_off_delay"
CONF_PLAYBACK_MONTHS = "playback_months"
CONF_PLAYBACK_THUMBNAILS = "playback_thumbnails"
CONF_THUMBNAIL_OFFSET = "playback_thumbnail_offset"

DEFAULT_CHANNEL = 1
DEFAULT_MOTION_OFF_DELAY = 60
DEFAULT_PROTOCOL = "rtmp"
DEFAULT_STREAM = "main"
DEFAULT_TIMEOUT = 30
DEFAULT_PLAYBACK_MONTHS = 2
DEFAULT_PLAYBACK_THUMBNAILS = False
DEFAULT_THUMBNAIL_OFFSET = 6

SERVICE_PTZ_CONTROL = "ptz_control"
SERVICE_SET_BACKLIGHT = "set_backlight"
SERVICE_SET_DAYNIGHT = "set_daynight"
SERVICE_SET_SENSITIVITY = "set_sensitivity"
