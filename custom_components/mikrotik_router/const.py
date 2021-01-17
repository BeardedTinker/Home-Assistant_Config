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

CONF_SENSOR_PORT_TRACKER = "sensor_port_tracker"
DEFAULT_SENSOR_PORT_TRACKER = False
CONF_SENSOR_PORT_TRAFFIC = "sensor_port_traffic"
DEFAULT_SENSOR_PORT_TRAFFIC = False
CONF_SENSOR_CLIENT_TRAFFIC = "sensor_client_traffic"
DEFAULT_SENSOR_CLIENT_TRAFFIC = False
CONF_SENSOR_SIMPLE_QUEUES = "sensor_simple_queues"
DEFAULT_SENSOR_SIMPLE_QUEUES = False
CONF_SENSOR_NAT = "sensor_nat"
DEFAULT_SENSOR_NAT = False
CONF_SENSOR_MANGLE = "sensor_mangle"
DEFAULT_SENSOR_MANGLE = False
CONF_SENSOR_PPP = "sensor_ppp"
DEFAULT_SENSOR_PPP = False
CONF_SENSOR_KIDCONTROL = "sensor_kidcontrol"
DEFAULT_SENSOR_KIDCONTROL = False
CONF_SENSOR_SCRIPTS = "sensor_scripts"
DEFAULT_SENSOR_SCRIPTS = False
CONF_SENSOR_ENVIRONMENT = "sensor_environment"
DEFAULT_SENSOR_ENVIRONMENT = False
