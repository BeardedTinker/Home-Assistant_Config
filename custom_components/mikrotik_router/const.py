"""Constants used by the Mikrotik Router component and platforms."""

DOMAIN = "mikrotik_router"
DEFAULT_NAME = "Mikrotik Router"
DATA_CLIENT = "client"
ATTRIBUTION = "Data provided by Mikrotik"

RUN_SCRIPT_COMMAND = "run_script"

DEFAULT_ENCODING = "ISO-8859-1"
DEFAULT_LOGIN_METHOD = "plain"

DEFAULT_HOST = "10.0.0.1"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin"
DEFAULT_PORT = 0
DEFAULT_DEVICE_NAME = "Mikrotik"
DEFAULT_SSL = False

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 30
LIST_UNIT_OF_MEASUREMENT = ["bps", "Kbps", "Mbps", "B/s", "KB/s", "MB/s"]
DEFAULT_UNIT_OF_MEASUREMENT = "Kbps"
CONF_TRACK_IFACE_CLIENTS = "track_iface_clients"
DEFAULT_TRACK_IFACE_CLIENTS = True
CONF_TRACK_HOSTS = "track_network_hosts"
DEFAULT_TRACK_HOSTS = False
CONF_TRACK_HOSTS_TIMEOUT = "track_network_hosts_timeout"
DEFAULT_TRACK_HOST_TIMEOUT = 180
