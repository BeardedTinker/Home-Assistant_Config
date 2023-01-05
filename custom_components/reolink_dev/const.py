"""Constants for the Reolink Camera integration."""

DOMAIN = "reolink_dev"
DOMAIN_DATA = "reolink_dev_devices"
EVENT_DATA_RECEIVED = "reolink_dev-event"
COORDINATOR = "coordinator"
MOTION_UPDATE_COORDINATOR = "motion_update_coordinator"
BASE = "base"
PUSH_MANAGER = "push_manager"
SESSION_RENEW_THRESHOLD = 300
MEDIA_SOURCE = "media_source"
THUMBNAIL_VIEW = "thumbnail_view"
SHORT_TOKENS = "short_tokens"
LONG_TOKENS = "long_tokens"
LAST_EVENT = "last_event"

CONF_USE_HTTPS = "use_https"
CONF_STREAM = "stream"
CONF_STREAM_FORMAT = "stream_format"
CONF_PROTOCOL = "protocol"
CONF_CHANNEL = "channel"
CONF_SMTP_PORT = "smtp_port"
CONF_MOTION_OFF_DELAY = "motion_off_delay"
CONF_PLAYBACK_MONTHS = "playback_months"
CONF_THUMBNAIL_PATH = "playback_thumbnail_path"
CONF_MOTION_STATES_UPDATE_FALLBACK_DELAY = "motion_states_update_fallback_delay"
CONF_ONVIF_SUBSCRIPTION_DISABLED = "onvif_subscription_disabled"

DEFAULT_USE_HTTPS = True
DEFAULT_CHANNEL = 1
DEFAULT_SMTP_PORT = 0
DEFAULT_MOTION_OFF_DELAY = 60
DEFAULT_PROTOCOL = "rtmp"
DEFAULT_STREAM = "main"
DEFAULT_STREAM_FORMAT = "h264"
DEFAULT_MOTION_STATES_UPDATE_FALLBACK_DELAY = 30
DEFAULT_ONVIF_SUBSCRIPTION_DISABLED = False

DEFAULT_TIMEOUT = 30
DEFAULT_PLAYBACK_MONTHS = 2
DEFAULT_THUMBNAIL_OFFSET = 6
DEFAULT_THUMBNAIL_PATH = "/"

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
