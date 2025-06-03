"""Constants for Moonraker."""

from enum import Enum

from homeassistant.const import Platform

# Base component constants
DOMAIN = "moonraker"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "1.8.0"
MANIFACTURER = "@marcolivierarsenault"

# Platforms
PLATFORMS = [
    Platform.SENSOR,
    Platform.CAMERA,
    Platform.BUTTON,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
    Platform.NUMBER,
    Platform.LIGHT,
]

CONF_API_KEY = "api_key"
CONF_URL = "url"
CONF_PORT = "port"
CONF_TLS = "tls"
CONF_PRINTER_NAME = "printer_name"
CONF_OPTION_CAMERA_STREAM = "camera_stream_url"
CONF_OPTION_CAMERA_SNAPSHOT = "camera_snapshot_url"
CONF_OPTION_POLLING_RATE = "polling_rate"
CONF_OPTION_CAMERA_PORT = "camera_port"
CONF_OPTION_THUMBNAIL_PORT = "thumbnail_port"

# API dict keys
HOSTNAME = "hostname"
OBJ = "objects"

# API timeout
TIMEOUT = 10


class METHODS(Enum):
    """API methods."""

    HOST_RESTART = "machine.reboot"
    HOST_SHUTDOWN = "machine.shutdown"
    MACHINE_DEVICE_POWER_DEVICES = "machine.device_power.devices"
    MACHINE_DEVICE_POWER_GET_DEVICE = "machine.device_power.get_device"
    MACHINE_DEVICE_POWER_POST_DEVICE = "machine.device_power.post_device"
    MACHINE_UPDATE_REFRESH = "machine.update.refresh"
    MACHINE_UPDATE_STATUS = "machine.update.status"
    MACHINE_SYSTEM_INFO = "machine.system_info"
    PRINTER_EMERGENCY_STOP = "printer.emergency_stop"
    PRINTER_INFO = "printer.info"
    PRINTER_GCODE_HELP = "printer.gcode.help"
    PRINTER_GCODE_SCRIPT = "printer.gcode.script"
    PRINTER_OBJECTS_LIST = "printer.objects.list"
    PRINTER_OBJECTS_QUERY = "printer.objects.query"
    PRINTER_OBJECTS_SUBSCRIBE = "printer.objects.subscribe"
    PRINTER_PRINT_CANCEL = "printer.print.cancel"
    PRINTER_PRINT_PAUSE = "printer.print.pause"
    PRINTER_PRINT_RESUME = "printer.print.resume"
    PRINTER_FIRMWARE_RESTART = "printer.firmware_restart"
    SERVER_FILES_METADATA = "server.files.metadata"
    SERVER_HISTORY_TOTALS = "server.history.totals"
    SERVER_HISTORY_RESET_TOTALS = "server.history.reset_totals"
    SERVER_JOB_QUEUE_STATUS = "server.job_queue.status"
    SERVER_JOB_QUEUE_START = "server.job_queue.start"
    SERVER_RESTART = "server.restart"
    SERVER_WEBCAMS_LIST = "server.webcams.list"


class ExtendedEnum(Enum):
    """Extended Enum class."""

    @classmethod
    def list(cls):
        """Return a list of all enum values."""
        return [c.value for c in cls]


class PRINTSTATES(ExtendedEnum):
    """Printer state."""

    STANDBY = "standby"
    PRINTING = "printing"
    PAUSED = "paused"
    COMPLETE = "complete"
    CANCELLED = "cancelled"
    ERROR = "error"


class PRINTERSTATES(ExtendedEnum):
    """Printer state."""

    READY = "ready"
    STARTUP = "startup"
    SHUTDOWN = "shutdown"
    ERROR = "error"
