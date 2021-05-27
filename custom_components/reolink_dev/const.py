"""Constants for the Reolink Camera integration."""

DOMAIN = "reolink_dev"
DOMAIN_DATA = "reolink_dev_devices"
EVENT_DATA_RECEIVED = "reolink_dev-event"
COORDINATOR = "coordinator"
BASE = "base"
PUSH_MANAGER = "push_manager"
SESSION_RENEW_THRESHOLD = 300
MEDIA_SOURCE = "media_source"
THUMBNAIL_VIEW = "thumbnail_view"
SHORT_TOKENS = "short_tokens"
LONG_TOKENS = "long_tokens"
LAST_EVENT = "last_event"

CONF_STREAM = "stream"
CONF_PROTOCOL = "protocol"
CONF_CHANNEL = "channel"
CONF_MOTION_OFF_DELAY = "motion_off_delay"
CONF_PLAYBACK_MONTHS = "playback_months"
CONF_THUMBNAIL_PATH = "playback_thumbnail_path"

DEFAULT_CHANNEL = 1
DEFAULT_MOTION_OFF_DELAY = 60
DEFAULT_PROTOCOL = "rtmp"
DEFAULT_STREAM = "main"
DEFAULT_TIMEOUT = 30
DEFAULT_PLAYBACK_MONTHS = 2
DEFAULT_THUMBNAIL_OFFSET = 6

SUPPORT_PTZ = 1024
SUPPORT_PLAYBACK = 2048

SERVICE_PTZ_CONTROL = "ptz_control"
SERVICE_SET_BACKLIGHT = "set_backlight"
SERVICE_SET_DAYNIGHT = "set_daynight"
SERVICE_SET_SENSITIVITY = "set_sensitivity"

SERVICE_QUERY_VOD = "query_vods"

THUMBNAIL_EXTENSION = "jpg"

THUMBNAIL_URL = "/api/" + DOMAIN + "/media_proxy/{camera_id}/{event_id}.jpg"
VOD_URL = "/api/" + DOMAIN + "/vod/{camera_id}/{event_id}"
