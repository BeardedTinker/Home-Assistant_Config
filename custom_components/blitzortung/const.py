import datetime

PLATFORMS = ["sensor"]

DOMAIN = "blitzortung"
DATA_UNSUBSCRIBE = "unsubscribe"
ATTR_LIGHTNING_DISTANCE = "distance"
ATTR_LIGHTNING_AZIMUTH = "azimuth"
ATTR_LIGHTNING_COUNTER = "counter"

SERVER_STATS = "server_stats"

BASE_URL_TEMPLATE = (
    "http://data{data_host_nr}.blitzortung.org/Data/Protected/last_strikes.php"
)
CONF_RADIUS = "radius"
DEFAULT_IDLE_RESET_TIMEOUT = 120
CONF_IDLE_RESET_TIMEOUT = "idle_reset_timeout"
DEFAULT_UPDATE_INTERVAL = datetime.timedelta(seconds=60)
NUMBER_OF_EVENTS = 200
REQUEST_TIMEOUT = 10
MAX_RETRIES = 3

DEFAULT_RADIUS = 100

ATTR_LAT = "lat"
ATTR_LON = "lon"
