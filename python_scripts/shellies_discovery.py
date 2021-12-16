"""
This script adds MQTT discovery support for Shellies devices.
"""
ATTR_DEVICE_CLASS = "device_class"
ATTR_ENABLED = "enabled"
ATTR_ENTITY_CATEGORY = "entity_category"
ATTR_ICON = "icon"
ATTR_MANUFACTURER = "Allterco Robotics"
ATTR_PAYLOAD = "payload"
ATTR_POWER_AC = "ac"
ATTR_RELAY = "relay"
ATTR_ROLLER = "roller"
ATTR_SHELLY = "Shelly"
ATTR_TOPIC = "topic"

BUTTON_MUTE = "mute"
BUTTON_RESTART = "restart"
BUTTON_SELF_TEST = "self_test"
BUTTON_UNMUTE = "unmute"
BUTTON_UPDATE_FIRMWARE = "update_firmware"

COMP_FAN = "fan"
COMP_LIGHT = "light"
COMP_SWITCH = "switch"

CONF_DEVELOP = "develop"
CONF_DISCOVERY_PREFIX = "discovery_prefix"
CONF_EXPIRE_AFTER = "expire_after"
CONF_EXT_SWITCH = "ext-switch"
CONF_FORCE_UPDATE_SENSORS = "force_update_sensors"
CONF_FRIENDLY_NAME = "friendly_name"
CONF_FW_VER = "fw_ver"
CONF_HOST = "host"
CONF_ID = "id"
CONF_IGNORED_DEVICES = "ignored_devices"
CONF_IGNORE_DEVICE_MODEL = "ignore_device_model"
CONF_MAC = "mac"
CONF_MODE = "mode"
CONF_MODEL_ID = "model"
CONF_POSITION_TEMPLATE = "position_template"
CONF_POWERED = "powered"
CONF_PUSH_OFF_DELAY = "push_off_delay"
CONF_QOS = "qos"
CONF_SET_POSITION_TEMPLATE = "set_position_template"
CONF_USE_FAHRENHEIT = "use_fahrenheit"

DEFAULT_DISC_PREFIX = "homeassistant"

DEVICE_CLASS_AWNING = "awning"
DEVICE_CLASS_BATTERY = "battery"
DEVICE_CLASS_BATTERY_CHARGING = "battery_charging"
DEVICE_CLASS_BLIND = "blind"
DEVICE_CLASS_COLD = "cold"
DEVICE_CLASS_CONNECTIVITY = "connectivity"
DEVICE_CLASS_CURRENT = "current"
DEVICE_CLASS_CURTAIN = "curtain"
DEVICE_CLASS_DAMPER = "damper"
DEVICE_CLASS_DOOR = "door"
DEVICE_CLASS_ENERGY = "energy"
DEVICE_CLASS_GARAGE = "garage"
DEVICE_CLASS_GARAGE_DOOR = "garage_door"
DEVICE_CLASS_GAS = "gas"
DEVICE_CLASS_GATE = "gate"
DEVICE_CLASS_HEAT = "heat"
DEVICE_CLASS_HUMIDITY = "humidity"
DEVICE_CLASS_ILLUMINANCE = "illuminance"
DEVICE_CLASS_LIGHT = "light"
DEVICE_CLASS_LOCK = "lock"
DEVICE_CLASS_MOISTURE = "moisture"
DEVICE_CLASS_MOTION = "motion"
DEVICE_CLASS_MOVING = "moving"
DEVICE_CLASS_OCCUPANCY = "occupancy"
DEVICE_CLASS_OPENING = "opening"
DEVICE_CLASS_PLUG = "plug"
DEVICE_CLASS_POWER = "power"
DEVICE_CLASS_POWER_FACTOR = "power_factor"
DEVICE_CLASS_PRESENCE = "presence"
DEVICE_CLASS_PRESSURE = "pressure"
DEVICE_CLASS_PROBLEM = "problem"
DEVICE_CLASS_RESTART = "restart"
DEVICE_CLASS_SAFETY = "safety"
DEVICE_CLASS_SHADE = "shade"
DEVICE_CLASS_SHUTTER = "shutter"
DEVICE_CLASS_SIGNAL_STRENGTH = "signal_strength"
DEVICE_CLASS_SMOKE = "smoke"
DEVICE_CLASS_SOUND = "sound"
DEVICE_CLASS_TEMPERATURE = "temperature"
DEVICE_CLASS_TIMESTAMP = "timestamp"
DEVICE_CLASS_UPDATE = "update"
DEVICE_CLASS_VIBRATION = "vibration"
DEVICE_CLASS_VOLTAGE = "voltage"
DEVICE_CLASS_WINDOW = "window"

ENTITY_CATEGORY_CONFIG = "config"
ENTITY_CATEGORY_DIAGNOSTIC = "diagnostic"

EXPIRE_AFTER_FOR_BATTERY_POWERED = int(1.2 * 12 * 60 * 60)  # 1.2 * 12 h
EXPIRE_AFTER_FOR_AC_POWERED = int(2.2 * 10 * 60)  # 2.2 * 10 min
EXPIRE_AFTER_FOR_SHELLY_MOTION = int(1.2 * 60 * 60)  # 1.2 * 60 min
EXPIRE_AFTER_FOR_SHELLY_VALVE = int(1.2 * 60 * 60)  # 1.2 * 60 min

KEY_ACTION_TEMPLATE = "act_tpl"
KEY_ACTION_TOPIC = "act_t"
KEY_AUTOMATION_TYPE = "atype"
KEY_AVAILABILITY_TOPIC = "avty_t"
KEY_COMMAND_TOPIC = "cmd_t"
KEY_CONFIGURATION_URL = "cu"
KEY_CONNECTIONS = "cns"
KEY_CURRENT_TEMPERATURE_TEMPLATE = "curr_temp_tpl"
KEY_CURRENT_TEMPERATURE_TOPIC = "curr_temp_t"
KEY_DEVICE = "dev"
KEY_DEVICE_CLASS = "dev_cla"
KEY_ENABLED_BY_DEFAULT = "en"
KEY_ENTITY_CATEGORY = "entity_category"
KEY_EXPIRE_AFTER = "exp_aft"
KEY_FORCE_UPDATE = "frc_upd"
KEY_ICON = "icon"
KEY_JSON_ATTRIBUTES_TEMPLATE = "json_attr_tpl"
KEY_JSON_ATTRIBUTES_TOPIC = "json_attr_t"
KEY_MAC = "mac"
KEY_MANUFACTURER = "mf"
KEY_MAX_TEMP = "max_temp"
KEY_MIN_TEMP = "min_temp"
KEY_MODE_STATE_TEMPLATE = "mode_stat_tpl"
KEY_MODE_STATE_TOPIC = "mode_stat_t"
KEY_MODEL = "mdl"
KEY_MODES = "modes"
KEY_NAME = "name"
KEY_OFF_DELAY = "off_dly"
KEY_OPTIMISTIC = "opt"
KEY_PAYLOAD = "pl"
KEY_PAYLOAD_AVAILABLE = "pl_avail"
KEY_PAYLOAD_CLOSE = "pl_cls"
KEY_PAYLOAD_NOT_AVAILABLE = "pl_not_avail"
KEY_PAYLOAD_OFF = "pl_off"
KEY_PAYLOAD_ON = "pl_on"
KEY_PAYLOAD_OPEN = "pl_open"
KEY_PAYLOAD_PRESS = "payload_press"
KEY_PAYLOAD_STOP = "pl_stop"
KEY_POSITION_TEMPLATE = "pos_tpl"
KEY_POSITION_TOPIC = "pos_t"
KEY_PRECISION = "precision"
KEY_QOS = "qos"
KEY_RETAIN = "ret"
KEY_SET_POSITION_TEMPLATE = "set_pos_tpl"
KEY_SET_POSITION_TOPIC = "set_pos_t"
KEY_STATE_CLASS = "stat_cla"
KEY_STATE_CLOSING = "stat_closing"
KEY_STATE_OPENING = "stat_opening"
KEY_STATE_STOPPED = "stat_stopped"
KEY_STATE_TEMPLATE = "stat_tpl"
KEY_STATE_TOPIC = "stat_t"
KEY_SUBTYPE = "stype"
KEY_SW_VERSION = "sw"
KEY_TEMPERATURE_COMMAND_TEMPLATE = "temp_cmd_tpl"
KEY_TEMPERATURE_COMMAND_TOPIC = "temp_cmd_t"
KEY_TEMPERATURE_STATE_TEMPLATE = "temp_stat_tpl"
KEY_TEMPERATURE_STATE_TOPIC = "temp_stat_t"
KEY_TOPIC = "t"
KEY_TYPE = "type"
KEY_UNIQUE_ID = "uniq_id"
KEY_UNIT = "unit_of_meas"
KEY_VALUE_TEMPLATE = "val_tpl"

LIGHT_COLOR = "color"
LIGHT_WHITE = "white"

# Maximum light transition time in milliseconds
MAX_TRANSITION = 5000

# Firmware 1.6.5 release date
MIN_4PRO_FIRMWARE_DATE = 20200408

# Firmware 1.1.0 release date
MIN_MOTION_FIRMWARE_DATE = 20210226

MIN_VALVE_FIRMWARE_DATE = 20211215

# Firmware 1.11.0 release date
MIN_FIRMWARE_DATE = 20210720

MODEL_SHELLY1 = f"{ATTR_SHELLY} 1"
MODEL_SHELLY1L = f"{ATTR_SHELLY} 1L"
MODEL_SHELLY1PM = f"{ATTR_SHELLY} 1PM"
MODEL_SHELLY2 = f"{ATTR_SHELLY} 2"
MODEL_SHELLY25 = f"{ATTR_SHELLY} 2.5"
MODEL_SHELLY3EM = f"{ATTR_SHELLY} 3EM"
MODEL_SHELLY4PRO = f"{ATTR_SHELLY} 4Pro"
MODEL_SHELLYAIR = f"{ATTR_SHELLY} Air"
MODEL_SHELLYBULB = f"{ATTR_SHELLY} Bulb"
MODEL_SHELLYBULBRGBW = f"{ATTR_SHELLY} DUO RGBW"
MODEL_SHELLYBUTTON1 = f"{ATTR_SHELLY} Button1"
MODEL_SHELLYDIMMER = f"{ATTR_SHELLY} Dimmer"
MODEL_SHELLYDIMMER2 = f"{ATTR_SHELLY} Dimmer 2"
MODEL_SHELLYDUO = f"{ATTR_SHELLY} DUO"
MODEL_SHELLYDW = f"{ATTR_SHELLY} Door/Window"
MODEL_SHELLYDW2 = f"{ATTR_SHELLY} Door/Window 2"
MODEL_SHELLYEM = f"{ATTR_SHELLY} EM"
MODEL_SHELLYFLOOD = f"{ATTR_SHELLY} Flood"
MODEL_SHELLYGAS = f"{ATTR_SHELLY} Gas"
MODEL_SHELLYHT = f"{ATTR_SHELLY} H&T"
MODEL_SHELLYI3 = f"{ATTR_SHELLY} i3"
MODEL_SHELLYMOTION = f"{ATTR_SHELLY} Motion"
MODEL_SHELLYPLUG = f"{ATTR_SHELLY} Plug"
MODEL_SHELLYPLUG_S = f"{ATTR_SHELLY} Plug S"
MODEL_SHELLYPLUG_US = f"{ATTR_SHELLY} Plug US"
MODEL_SHELLYRGBW2 = f"{ATTR_SHELLY} RGBW2"
MODEL_SHELLYSENSE = f"{ATTR_SHELLY} Sense"
MODEL_SHELLYSMOKE = f"{ATTR_SHELLY} Smoke"
MODEL_SHELLYUNI = f"{ATTR_SHELLY} UNI"
MODEL_SHELLYVALVE = f"{ATTR_SHELLY} Valve"
MODEL_SHELLYVINTAGE = f"{ATTR_SHELLY} Vintage"

MODEL_SHELLY1_ID = "SHSW-1"  # Shelly 1
MODEL_SHELLY1_PREFIX = "shelly1"

MODEL_SHELLY1L_ID = "SHSW-L"  # Shelly 1L
MODEL_SHELLY1L_PREFIX = "shelly1l"

MODEL_SHELLY1PM_ID = "SHSW-PM"  # Shelly 1PM
MODEL_SHELLY1PM_PREFIX = "shelly1pm"

MODEL_SHELLY2_ID = "SHSW-21"  # Shelly 2
MODEL_SHELLY2_PREFIX = "shellyswitch"

MODEL_SHELLY25_ID = "SHSW-25"  # Shelly 2.5
MODEL_SHELLY25_PREFIX = "shellyswitch25"

MODEL_SHELLY3EM_ID = "SHEM-3"  # Shelly 3EM
MODEL_SHELLY3EM_PREFIX = "shellyem3"

MODEL_SHELLY4PRO_ID = "SHSW-44"  # Shelly 4Pro
MODEL_SHELLY4PRO_PREFIX = "shelly4pro"

MODEL_SHELLYAIR_ID = "SHAIR-1"  # Shelly Air
MODEL_SHELLYAIR_PREFIX = "shellyair"

MODEL_SHELLYBULB_ID = "SHBLB-1"  # Shelly Bulb
MODEL_SHELLYBULB_PREFIX = "shellybulb"

MODEL_SHELLYBULBRGBW_ID = "SHCB-1"  # Shelly DUO RGBW
MODEL_SHELLYBULBRGBW_PREFIX = "shellycolorbulb"

MODEL_SHELLYBUTTON1_ID = "SHBTN-1"  # Shelly Button1
MODEL_SHELLYBUTTON1V2_ID = "SHBTN-2"  # Shelly Button1 v2
MODEL_SHELLYBUTTON1_PREFIX = "shellybutton1"

MODEL_SHELLYDIMMER_ID = "SHDM-1"  # Shelly Dimmer
MODEL_SHELLYDIMMER_PREFIX = "shellydimmer"

MODEL_SHELLYDIMMER2_ID = "SHDM-2"  # Shelly Dimmer 2
MODEL_SHELLYDIMMER2_PREFIX = "shellydimmer2"

MODEL_SHELLYDUO_ID = "SHBDUO-1"  # Shelly Duo
MODEL_SHELLYDUO_PREFIX = "shellybulbduo"

MODEL_SHELLYDW_ID = "SHDW-1"  # Shelly Door/Window
MODEL_SHELLYDW_PREFIX = "shellydw"

MODEL_SHELLYDW2_ID = "SHDW-2"  # Shelly Door/Window 2
MODEL_SHELLYDW2_PREFIX = "shellydw2"

MODEL_SHELLYEM_ID = "SHEM"  # Shelly EM
MODEL_SHELLYEM_PREFIX = "shellyem"

MODEL_SHELLYFLOOD_ID = "SHWT-1"  # Shelly Flood
MODEL_SHELLYFLOOD_PREFIX = "shellyflood"

MODEL_SHELLYGAS_ID = "SHGS-1"  # Shelly Gas
MODEL_SHELLYGAS_PREFIX = "shellygas"

MODEL_SHELLYHT_ID = "SHHT-1"  # Shelly H&T
MODEL_SHELLYHT_PREFIX = "shellyht"

MODEL_SHELLYI3_ID = "SHIX3-1"  # Shelly i3
MODEL_SHELLYI3_PREFIX = "shellyix3"

MODEL_SHELLYMOTION_ID = "SHMOS-01"  # Shelly Motion
MODEL_SHELLYMOTION_PREFIX = "shellymotionsensor"

MODEL_SHELLYPLUG_ID = "SHPLG-1"  # Shelly Plug
MODEL_SHELLYPLUG_E_ID = "SHPLG2-1"  # Shelly Plug E
MODEL_SHELLYPLUG_PREFIX = "shellyplug"

MODEL_SHELLYPLUG_S_ID = "SHPLG-S"  # Shelly Plug S
MODEL_SHELLYPLUG_S_PREFIX = "shellyplug-s"

MODEL_SHELLYPLUG_US_ID = "SHPLG-U1"  # Shelly Plug US
MODEL_SHELLYPLUG_US_PREFIX = "shellyplug-u1"

MODEL_SHELLYRGBW2_ID = "SHRGBW2"  # Shelly RGBW2
MODEL_SHELLYRGBW2_PREFIX = "shellyrgbw2"

MODEL_SHELLYSENSE_ID = "SHSEN-1"  # Shelly Sense
MODEL_SHELLYSENSE_PREFIX = "shellysense"

MODEL_SHELLYSMOKE_ID = "SHSM-01"  # Shelly Smoke
MODEL_SHELLYSMOKE_PREFIX = "shellysmoke"

MODEL_SHELLYVALVE_ID = "SHTRV-01"  # Shelly Valve
MODEL_SHELLYVALVE_PREFIX = "shellytrv"

MODEL_SHELLYVINTAGE_ID = "SHVIN-1"  # Shelly Vintage
MODEL_SHELLYVINTAGE_PREFIX = "shellyvintage"

MODEL_SHELLYUNI_ID = "SHUNI-1"  # Shelly UNI
MODEL_SHELLYUNI_PREFIX = "shellyuni"

OFF_DELAY = 2

PL_MUTE = "mute"
PL_RESTART = "reboot"
PL_SELF_TEST = "self_test"
PL_UNMUTE = "unmute"
PL_UPDATE_FIRMWARE = "update_fw"

SENSOR_ADC = "adc"
SENSOR_BATTERY = "battery"
SENSOR_CHARGER = "charger"
SENSOR_CLOUD = "cloud"
SENSOR_CONCENTRATION = "concentration"
SENSOR_CURRENT = "current"
SENSOR_DOUBLE_SHORTPUSH = "double shortpush"
SENSOR_DOUBLE_SHORTPUSH_0 = "double shortpush 0"
SENSOR_DOUBLE_SHORTPUSH_1 = "double shortpush 1"
SENSOR_DOUBLE_SHORTPUSH_2 = "double shortpush 2"
SENSOR_ENERGY = "energy"
SENSOR_EXT_HUMIDITY = "ext_humidity"
SENSOR_EXT_SWITCH = "ext_switch"
SENSOR_EXT_TEMPERATURE = "ext_temperature"
SENSOR_FIRMWARE_UPDATE = "firmware update"
SENSOR_FLOOD = "flood"
SENSOR_GAS = "gas"
SENSOR_HUMIDITY = "humidity"
SENSOR_ILLUMINATION = "illumination"
SENSOR_INPUT = "input"
SENSOR_INPUT_0 = "input 0"
SENSOR_INPUT_1 = "input 1"
SENSOR_INPUT_2 = "input 2"
SENSOR_LOADERROR = "loaderror"
SENSOR_LONGPUSH = "longpush"
SENSOR_LONGPUSH_0 = "longpush 0"
SENSOR_LONGPUSH_1 = "longpush 1"
SENSOR_LONGPUSH_2 = "longpush 2"
SENSOR_LONGPUSH_SHORTPUSH_0 = "longpush shortpush 0"
SENSOR_LONGPUSH_SHORTPUSH_1 = "longpush shortpush 1"
SENSOR_LONGPUSH_SHORTPUSH_2 = "longpush shortpush 2"
SENSOR_LUX = "lux"
SENSOR_MOTION = "motion"
SENSOR_OPENING = "opening"
SENSOR_OPERATION = "operation"
SENSOR_OVERLOAD = "overload"
SENSOR_OVERPOWER = "overpower"
SENSOR_OVERPOWER_VALUE = "overpower_value"
SENSOR_OVERTEMPERATURE = "overtemperature"
SENSOR_POWER = "power"
SENSOR_POWER_FACTOR = "pf"
SENSOR_REACTIVE_POWER = "reactive_power"
SENSOR_RETURNED_ENERGY = "returned_energy"
SENSOR_RSSI = "rssi"
SENSOR_IP = "ip"
SENSOR_SELF_TEST = "self_test"
SENSOR_SHORTPUSH = "shortpush"
SENSOR_SHORTPUSH_0 = "shortpush/0"
SENSOR_SHORTPUSH_1 = "shortpush/1"
SENSOR_SHORTPUSH_2 = "shortpush/2"
SENSOR_SHORTPUSH_LONGPUSH_0 = "shortpush longpush 0"
SENSOR_SHORTPUSH_LONGPUSH_1 = "shortpush longpush 1"
SENSOR_SHORTPUSH_LONGPUSH_2 = "shortpush longpush 2"
SENSOR_SMOKE = "smoke"
SENSOR_SSID = "ssid"
SENSOR_TEMPERATURE = "temperature"
SENSOR_TEMPERATURE_F = "temperature_f"
SENSOR_TEMPERATURE_STATUS = "temperature_status"
SENSOR_TILT = "tilt"
SENSOR_TOTAL = "total"
SENSOR_TOTALWORKTIME = "totalworktime"
SENSOR_TOTAL_RETURNED = "total_returned"
SENSOR_TRIPLE_SHORTPUSH = "triple shortpush"
SENSOR_TRIPLE_SHORTPUSH_0 = "triple shortpush 0"
SENSOR_TRIPLE_SHORTPUSH_1 = "triple shortpush 1"
SENSOR_TRIPLE_SHORTPUSH_2 = "triple shortpush 2"
SENSOR_UPTIME = "uptime"
SENSOR_LAST_RESTART = "last_restart"
SENSOR_VIBRATION = "vibration"
SENSOR_VOLTAGE = "voltage"

STATE_CLASS_MEASUREMENT = "measurement"
STATE_CLASS_TOTAL_INCREASING = "total_increasing"

TOPIC_ADC = "adc/0"
TOPIC_ANNOUNCE = "announce"
TOPIC_COLOR_0_STATUS = "color/0/status"
TOPIC_COMMAND = "command"
TOPIC_EXT_SWITCH = "ext_switch/0"
TOPIC_INFO = "info"
TOPIC_INPUT_0 = "input/0"
TOPIC_INPUT_1 = "input/1"
TOPIC_INPUT_2 = "input/2"
TOPIC_INPUT_EVENT = "input_event"
TOPIC_INPUT_EVENT_0 = "input_event/0"
TOPIC_INPUT_EVENT_1 = "input_event/1"
TOPIC_INPUT_EVENT_2 = "input_event/2"
TOPIC_LONGPUSH = "longpush"
TOPIC_LONGPUSH_0 = "longpush/0"
TOPIC_LONGPUSH_1 = "longpush/1"
TOPIC_LONGPUSH_2 = "longpush/2"
TOPIC_MUTE = "sensor/mute"
TOPIC_OVERPOWER_VALUE = "overpower_value"
TOPIC_RELAY = "relay"
TOPIC_SELF_TEST = "sensor/start_self_test"
TOPIC_STATUS = "status"
TOPIC_TEMPERATURE = "sensor/temperature"
TOPIC_TEMPERATURE_STATUS = "temperature_status"
TOPIC_UNMUTE = "sensor/unmute"
TOPIC_VOLTAGE = "voltage"

TPL_ACTION_TEMPLATE = "{{%if value_json.thermostats[0].target_t.value<={min_temp}%}}off{{%elif value_json.thermostats[0].pos==0%}}idle{{%else%}}heating{{%endif%}}"
TPL_ADC = "{{value|float|round(2)}}"
TPL_BATTERY = "{{value|float|round}}"
TPL_BATTERY_FROM_JSON = "{{value_json.bat}}"
TPL_CHARGER = "{%if value_json.charger==true%}ON{%else%}OFF{%endif%}"
TPL_CLOUD = "{%if value_json.cloud.connected==true%}ON{%else%}OFF{%endif%}"
TPL_CONCENTRATION = "{%if 0<=value|int<=65535%}{{value}}{%endif%}"
TPL_CURRENT = "{{value|float|round(2)}}"
TPL_CURRENT_TEMPERATURE = "{{value_json.thermostats[0].tmp.value}}"
TPL_DOUBLE_SHORTPUSH = "{%if value_json.event==^SS^%}ON{%else%}OFF{%endif%}"
TPL_ENERGY_WH = "{{(value|float/1000)|round(2)}}"
TPL_ENERGY_WMIN = "{{(value|float/60/1000)|round(2)}}"
TPL_GAS = "{%if value in [^mild^,^heavy^]%}ON{%else%}OFF{%endif%}"
TPL_GAS_TO_JSON = "{{{^status^:value}|tojson}}"
TPL_HUMIDITY = "{%if value!=999%}{{value|float|round(1)}}{%endif%}"
TPL_HUMIDITY_EXT = "{%if value!=999%}{{value|float|round(1)}}{%endif%}"
TPL_ILLUMINATION = "{{value_json.lux}}"
TPL_ILLUMINATION_TO_JSON = "{{{^illumination^:value}|tojson}}"
TPL_IP = "{{value_json.ip}}"
TPL_IP_FROM_INFO = "{{value_json.wifi_sta.ip}}"
TPL_LONGPUSH = "{%if value_json.event==^L^%}ON{%else%}OFF{%endif%}"
TPL_LONGPUSH_SHORTPUSH = "{%if value_json.event==^LS^%}ON{%else%}OFF{%endif%}"
TPL_LUX = "{{value|float|round}}"
TPL_MOTION = "{%if value_json.motion==true%}ON{%else%}OFF{%endif%}"
TPL_NEW_FIRMWARE_FROM_ANNOUNCE = "{%if value_json.new_fw==true%}ON{%else%}OFF{%endif%}"
TPL_NEW_FIRMWARE_FROM_INFO = (
    "{%if value_json[^update^].has_update==true%}ON{%else%}OFF{%endif%}"
)
TPL_OVERPOWER = "{%if value_json.overpower==true%}ON{%else%}OFF{%endif%}"
TPL_OVERPOWER_RELAY = "{%if value==^overpower^%}ON{%else%}OFF{%endif%}"
TPL_OVERPOWER_VALUE_TO_JSON = "{{{^overpower_value^:value}|tojson}}"
TPL_POSITION = "{%if value!=-1%}{{value}}{%endif%}"
TPL_POWER = "{{value|float|round(1)}}"
TPL_POWER_FACTOR = "{{value|float*100|round}}"
TPL_RSSI = "{{value_json.wifi_sta.rssi}}"
TPL_SET_TARGET_TEMPERATURE = "{{value|int}}"
TPL_SHORTPUSH = "{%if value_json.event==^S^%}ON{%else%}OFF{%endif%}"
TPL_SHORTPUSH_LONGPUSH = "{%if value_json.event==^SL^%}ON{%else%}OFF{%endif%}"
TPL_SSID = "{{value_json.wifi_sta.ssid}}"
TPL_TARGET_TEMPERATURE = "{{ value_json.thermostats[0].target_t.value }}"
TPL_TEMPERATURE = "{%if value!=999%}{{value|float|round(1)}}{%endif%}"
TPL_TEMPERATURE_EXT = "{%if value!=999%}{{value|float|round(1)}}{%endif%}"
TPL_TEMPERATURE_STATUS = "{{value|lower}}"
TPL_TILT = "{{value|float}}"
TPL_TRIPLE_SHORTPUSH = "{%if value_json.event==^SSS^%}ON{%else%}OFF{%endif%}"
TPL_UPDATE_TO_JSON = "{{value_json[^update^]|tojson}}"
TPL_UPTIME = "{{(as_timestamp(now())-value_json.uptime)|timestamp_local}}"
TPL_VIBRATION = "{%if value_json.vibration==true%}ON{%else%}OFF{%endif%}"
TPL_VOLTAGE = "{{value|float|round(1)}}"

UNIT_AMPERE = "A"
UNIT_CELSIUS = "°C"
UNIT_DBM = "dBm"
UNIT_DEGREE = "°"
UNIT_FAHRENHEIT = "°F"
UNIT_KWH = "kWh"
UNIT_LUX = "lx"
UNIT_PERCENT = "%"
UNIT_PPM = "ppm"
UNIT_SECOND = "s"
UNIT_VAR = "VAR"
UNIT_VOLT = "V"
UNIT_WATT = "W"

VALUE_BUTTON_DOUBLE_PRESS = "button_double_press"
VALUE_BUTTON_LONG_PRESS = "button_long_press"
VALUE_BUTTON_LONG_SHORT_PRESS = "button_long_short_press"
VALUE_BUTTON_SHORT_LONG_PRESS = "button_short_long_press"
VALUE_BUTTON_SHORT_PRESS = "button_short_press"
VALUE_BUTTON_TRIPLE_PRESS = "button_triple_press"
VALUE_BUTTON_SHORT_RELEASE = "button_short_release"
VALUE_CLOSE = "close"
VALUE_CLOSE = "close"
VALUE_FALSE = "false"
VALUE_OFF = "off"
VALUE_ON = "on"
VALUE_OPEN = "open"
VALUE_OPEN = "open"
VALUE_STOP = "stop"
VALUE_STOP = "stop"
VALUE_TRIGGER = "trigger"
VALUE_TRUE = "true"

DEVICE_TRIGGERS_MAP = {
    VALUE_BUTTON_DOUBLE_PRESS: "SS",
    VALUE_BUTTON_LONG_PRESS: "L",
    VALUE_BUTTON_LONG_SHORT_PRESS: "LS",
    VALUE_BUTTON_SHORT_LONG_PRESS: "SL",
    VALUE_BUTTON_SHORT_PRESS: "S",
    VALUE_BUTTON_TRIPLE_PRESS: "SSS",
}

PL_0_1 = {VALUE_ON: "0", VALUE_OFF: "1"}
PL_1_0 = {VALUE_ON: "1", VALUE_OFF: "0"}
PL_OPEN_CLOSE = {VALUE_ON: VALUE_OPEN, VALUE_OFF: VALUE_CLOSE}
PL_TRUE_FALSE = {VALUE_ON: VALUE_TRUE, VALUE_OFF: VALUE_FALSE}

ROLLER_DEVICE_CLASSES = [
    DEVICE_CLASS_AWNING,
    DEVICE_CLASS_BLIND,
    DEVICE_CLASS_CURTAIN,
    DEVICE_CLASS_DAMPER,
    DEVICE_CLASS_DOOR,
    DEVICE_CLASS_GARAGE,
    DEVICE_CLASS_GATE,
    DEVICE_CLASS_SHADE,
    DEVICE_CLASS_SHUTTER,
    DEVICE_CLASS_WINDOW,
]


def clean_name(string):
    """Clean entity/device name."""
    return string.replace("-", " ").replace("_", " ").title()


def format_mac(mac):
    """Format the mac address string."""
    return ":".join(mac[i : i + 2] for i in range(0, 12, 2))


def parse_version(version):
    """Parse version string and return version date integer."""
    try:
        if "-" in version:
            return int(version.split("-", 1)[0])
    except TypeError:
        return version


def get_device_config(dev_id):
    """Get device configuration."""
    result = data.get(dev_id, data.get(dev_id.lower(), {}))  # noqa: F821
    if not result:
        result = {}
    try:
        if len(result) > 0:
            result[0]
    except TypeError:
        logger.error("Wrong configuration for %s", dev_id)  # noqa: F821
        result = {}
    finally:
        return result


def mqtt_publish(topic, payload, retain):
    """Publish data to MQTT broker."""
    service_data = {
        "topic": topic,
        "payload": str(payload).replace("'", '"').replace("^", "'"),
        "retain": retain,
        "qos": 0,
    }
    logger.debug(service_data)
    logger.debug("Sending to MQTT broker: %s %s", topic, payload)  # noqa: F821
    hass.services.call("mqtt", "publish", service_data, False)  # noqa: F821


expire_after = None

qos = 0
retain = True

no_battery_sensor = False

fw_ver = data.get(CONF_FW_VER)  # noqa: F821
dev_id = data.get(CONF_ID)  # noqa: F821
model_id = data.get(CONF_MODEL_ID)
mode = data.get(CONF_MODE)
host = data.get(CONF_HOST)

use_fahrenheit = False

roller_mode = False
if mode == "roller":
    roller_mode = True

ignored = [
    element.lower() for element in data.get(CONF_IGNORED_DEVICES, [])
]  # noqa: F821
mac = data.get(CONF_MAC)  # noqa: F821

if not dev_id:
    raise ValueError("id value None is not valid, check script configuration")
if len(dev_id) > 32:
    raise ValueError(
        f"id value {dev_id} is longer than 32 characters, use shorter custom MQTT prefix"
    )
if not mac:
    raise ValueError("mac value None is not valid, check script configuration")
if not fw_ver:
    raise ValueError("fw_ver value None is not valid, check script configuration")

mac = str(mac).lower()  # noqa: F821

try:
    cur_ver_date = parse_version(fw_ver)
except (IndexError, ValueError):
    raise ValueError(
        f"Firmware version {fw_ver} is not supported, please update your device {dev_id}"
    )

dev_id_prefix = dev_id.rsplit("-", 1)[0].lower()

if (
    dev_id_prefix == MODEL_SHELLY4PRO_PREFIX or MODEL_SHELLY4PRO_ID == model_id
) and cur_ver_date < MIN_4PRO_FIRMWARE_DATE:
    raise ValueError(
        f"Firmware dated {MIN_4PRO_FIRMWARE_DATE} is required, please update your device {dev_id}"
    )

if (
    dev_id_prefix == MODEL_SHELLYMOTION_PREFIX or MODEL_SHELLYMOTION_ID == model_id
) and cur_ver_date < MIN_MOTION_FIRMWARE_DATE:
    raise ValueError(
        f"Firmware dated {MIN_MOTION_FIRMWARE_DATE} is required, please update your device {dev_id}"
    )

if (
    dev_id_prefix == MODEL_SHELLYVALVE_PREFIX or MODEL_SHELLYVALVE_ID == model_id
) and cur_ver_date < MIN_VALVE_FIRMWARE_DATE:
    raise ValueError(
        f"Firmware dated {MIN_VALVE_FIRMWARE_DATE} is required, please update your device {dev_id}"
    )

if (
    dev_id_prefix
    not in (
        MODEL_SHELLY4PRO_PREFIX,
        MODEL_SHELLYMOTION_PREFIX,
        MODEL_SHELLYVALVE_PREFIX,
    )
    and model_id
    not in (MODEL_SHELLY4PRO_ID, MODEL_SHELLYMOTION_ID, MODEL_SHELLYVALVE_ID)
) and cur_ver_date < MIN_FIRMWARE_DATE:
    raise ValueError(
        f"Firmware dated {MIN_FIRMWARE_DATE} is required, please update your device {dev_id}"
    )

logger.debug(
    "id: %s, mac: %s, fw_ver: %s, model: %s", dev_id, mac, fw_ver, model_id
)  # noqa: F821

try:
    if int(data.get(CONF_QOS, 0)) in (0, 1, 2):  # noqa: F821
        qos = int(data.get(CONF_QOS, 0))  # noqa: F821
    else:
        raise ValueError()
except ValueError:
    logger.error("Not valid qos value, the default value 0 was used")  # noqa: F821

disc_prefix = data.get(CONF_DISCOVERY_PREFIX, DEFAULT_DISC_PREFIX)  # noqa: F821

ignore_device_model = data.get(CONF_IGNORE_DEVICE_MODEL, False)  # noqa: F821
if not isinstance(ignore_device_model, bool):
    ignore_device_model = False

develop = data.get(CONF_DEVELOP, False)  # noqa: F821
if develop:
    disc_prefix = "develop"
    retain = False
    logger.error("DEVELOP MODE !!!")  # noqa: F821

battery_powered = False
bin_sensors = []
bin_sensors_device_classes = []
bin_sensors_enabled = []
bin_sensors_entity_categories = []
bin_sensors_pl = []
bin_sensors_topics = []
bin_sensors_tpls = []
ext_humi_sensors = 0
ext_temp_sensors = 0
inputs = 0
inputs_types = []
lights_bin_sensors = []
lights_bin_sensors_device_classes = []
lights_bin_sensors_pl = []
lights_bin_sensors_tpls = []
lights_sensors = []
lights_sensors_device_classes = []
lights_sensors_entity_categories = []
lights_sensors_state_classes = []
lights_sensors_tpls = []
lights_sensors_units = []
meters = 0
meters_sensors = []
meters_sensors_device_classes = []
meters_sensors_state_classes = []
meters_sensors_tpls = []
meters_sensors_units = []
meters_sensors_units = []
model = None
relay_components = [COMP_SWITCH, COMP_LIGHT, COMP_FAN]
relays = 0
relays_bin_sensors = []
relays_bin_sensors_device_classes = []
relays_bin_sensors_entity_categories = []
relays_bin_sensors_pl = []
relays_bin_sensors_topics = []
relays_bin_sensors_tpls = []
relays_sensors = []
relays_sensors_device_classes = []
relays_sensors_state_classes = []
relays_sensors_tpls = []
relays_sensors_units = []
rgbw_lights = 0
rollers = 0
sensors = []
sensors_device_classes = []
sensors_enabled = []
sensors_entity_categories = []
sensors_state_classes = []
sensors_topics = []
sensors_tpls = []
sensors_units = []
white_lights = 0
climate_entity_option = {}
buttons = {}

if model_id == MODEL_SHELLY1_ID or dev_id_prefix == MODEL_SHELLY1_PREFIX:
    model = MODEL_SHELLY1

    ext_humi_sensors = 1
    ext_temp_sensors = 3
    inputs = 1
    relays = 1

    bin_sensors = [SENSOR_FIRMWARE_UPDATE, SENSOR_EXT_SWITCH]
    bin_sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC, None]
    bin_sensors_enabled = [True, False]
    bin_sensors_device_classes = [DEVICE_CLASS_UPDATE, None]
    bin_sensors_pl = [None, PL_1_0]
    bin_sensors_topics = [TOPIC_INFO, TOPIC_EXT_SWITCH]
    bin_sensors_tpls = [TPL_NEW_FIRMWARE_FROM_INFO, None]
    inputs_types = [VALUE_BUTTON_LONG_PRESS, VALUE_BUTTON_SHORT_PRESS]
    relays_bin_sensors = [
        SENSOR_INPUT,
        SENSOR_LONGPUSH,
        SENSOR_SHORTPUSH,
    ]
    relays_bin_sensors_entity_categories = [None, None, None]
    relays_bin_sensors_device_classes = [None, None, None]
    relays_bin_sensors_pl = [PL_1_0, None, None]
    relays_bin_sensors_topics = [None, TOPIC_INPUT_EVENT, TOPIC_INPUT_EVENT]
    relays_bin_sensors_tpls = [None, TPL_LONGPUSH, TPL_SHORTPUSH]
    sensors = [SENSOR_RSSI, SENSOR_SSID, SENSOR_UPTIME, SENSOR_IP]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [STATE_CLASS_MEASUREMENT, None, None, None]
    sensors_enabled = [False, False, False, False]
    sensors_device_classes = [
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
    ]
    sensors_topics = [TOPIC_INFO, TOPIC_INFO, TOPIC_INFO, TOPIC_ANNOUNCE]
    sensors_tpls = [TPL_RSSI, TPL_SSID, TPL_UPTIME, TPL_IP]
    sensors_units = [UNIT_DBM, None, None, None]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLY1L_ID or dev_id_prefix == MODEL_SHELLY1L_PREFIX:
    model = MODEL_SHELLY1L

    ext_humi_sensors = 1
    ext_temp_sensors = 3
    inputs = 2
    relays = 1

    bin_sensors = [
        SENSOR_INPUT_0,
        SENSOR_INPUT_1,
        SENSOR_SHORTPUSH_0,
        SENSOR_LONGPUSH_0,
        SENSOR_SHORTPUSH_1,
        SENSOR_LONGPUSH_1,
        SENSOR_FIRMWARE_UPDATE,
        SENSOR_OVERTEMPERATURE,
    ]
    bin_sensors_entity_categories = [
        None,
        None,
        None,
        None,
        None,
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    bin_sensors_enabled = [False, False, True, True, True, True, True, True]
    bin_sensors_device_classes = [
        None,
        None,
        None,
        None,
        None,
        None,
        DEVICE_CLASS_UPDATE,
        DEVICE_CLASS_PROBLEM,
    ]
    bin_sensors_pl = [PL_1_0, PL_1_0, None, None, None, None, None, PL_1_0]
    bin_sensors_topics = [
        TOPIC_INPUT_0,
        TOPIC_INPUT_1,
        TOPIC_INPUT_EVENT_0,
        TOPIC_INPUT_EVENT_0,
        TOPIC_INPUT_EVENT_1,
        TOPIC_INPUT_EVENT_1,
        TOPIC_INFO,
        None,
    ]
    bin_sensors_tpls = [
        None,
        None,
        TPL_SHORTPUSH,
        TPL_LONGPUSH,
        TPL_SHORTPUSH,
        TPL_LONGPUSH,
        TPL_NEW_FIRMWARE_FROM_INFO,
        None,
    ]
    inputs_types = [VALUE_BUTTON_LONG_PRESS, VALUE_BUTTON_SHORT_PRESS]
    relays_sensors = [SENSOR_POWER, SENSOR_ENERGY]
    relays_sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_TOTAL_INCREASING,
    ]
    relays_sensors_device_classes = [DEVICE_CLASS_POWER, DEVICE_CLASS_ENERGY]
    relays_sensors_tpls = [TPL_POWER, TPL_ENERGY_WMIN]
    relays_sensors_units = [UNIT_WATT, UNIT_KWH]
    sensors = [SENSOR_TEMPERATURE, SENSOR_RSSI, SENSOR_SSID, SENSOR_UPTIME, SENSOR_IP]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        None,
        None,
        None,
    ]
    sensors_enabled = [True, False, False, False, False]
    sensors_device_classes = [
        DEVICE_CLASS_TEMPERATURE,
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
    ]
    sensors_topics = [None, TOPIC_INFO, TOPIC_INFO, TOPIC_INFO, TOPIC_ANNOUNCE]
    sensors_tpls = [TPL_TEMPERATURE, TPL_RSSI, TPL_SSID, TPL_UPTIME, TPL_IP]
    sensors_units = [UNIT_CELSIUS, UNIT_DBM, None, None, None]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLY1PM_ID or dev_id_prefix == MODEL_SHELLY1PM_PREFIX:
    model = MODEL_SHELLY1PM
    relays = 1
    inputs = 1
    inputs_types = [VALUE_BUTTON_LONG_PRESS, VALUE_BUTTON_SHORT_PRESS]
    relays_sensors = [SENSOR_POWER, SENSOR_ENERGY]
    relays_sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_TOTAL_INCREASING,
    ]
    relays_sensors_units = [UNIT_WATT, UNIT_KWH]
    relays_sensors_device_classes = [DEVICE_CLASS_POWER, DEVICE_CLASS_ENERGY]
    relays_sensors_tpls = [TPL_POWER, TPL_ENERGY_WMIN]
    relays_bin_sensors = [
        SENSOR_INPUT,
        SENSOR_LONGPUSH,
        SENSOR_SHORTPUSH,
        SENSOR_OVERPOWER,
    ]
    relays_bin_sensors_entity_categories = [
        None,
        None,
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    relays_bin_sensors_pl = [PL_1_0, None, None, None]
    relays_bin_sensors_topics = [
        None,
        TOPIC_INPUT_EVENT,
        TOPIC_INPUT_EVENT,
        TOPIC_RELAY,
    ]
    relays_bin_sensors_tpls = [None, TPL_LONGPUSH, TPL_SHORTPUSH, TPL_OVERPOWER_RELAY]
    relays_bin_sensors_device_classes = [None, None, None, DEVICE_CLASS_PROBLEM]
    sensors = [
        SENSOR_TEMPERATURE,
        SENSOR_RSSI,
        SENSOR_SSID,
        SENSOR_UPTIME,
        SENSOR_IP,
        SENSOR_TEMPERATURE_STATUS,
    ]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        None,
        None,
        None,
        None,
    ]
    sensors_enabled = [True, False, False, False, False, True]
    sensors_device_classes = [
        DEVICE_CLASS_TEMPERATURE,
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
        None,
    ]
    sensors_units = [UNIT_CELSIUS, UNIT_DBM, None, None, None, None]
    sensors_tpls = [
        TPL_TEMPERATURE,
        TPL_RSSI,
        TPL_SSID,
        TPL_UPTIME,
        TPL_IP,
        TPL_TEMPERATURE_STATUS,
    ]
    sensors_topics = [
        None,
        TOPIC_INFO,
        TOPIC_INFO,
        TOPIC_INFO,
        TOPIC_ANNOUNCE,
        TOPIC_TEMPERATURE_STATUS,
    ]
    bin_sensors = [SENSOR_OVERTEMPERATURE, SENSOR_FIRMWARE_UPDATE]
    bin_sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    bin_sensors_enabled = [True, True]
    bin_sensors_device_classes = [DEVICE_CLASS_PROBLEM, DEVICE_CLASS_UPDATE]
    bin_sensors_pl = [PL_1_0, None]
    bin_sensors_tpls = [None, TPL_NEW_FIRMWARE_FROM_INFO]
    bin_sensors_topics = [None, TOPIC_INFO]
    ext_humi_sensors = 1
    ext_temp_sensors = 3
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLYAIR_ID or dev_id_prefix == MODEL_SHELLYAIR_PREFIX:
    model = MODEL_SHELLYAIR
    relays = 1
    relays_sensors = [SENSOR_POWER, SENSOR_ENERGY]
    relays_sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_TOTAL_INCREASING,
    ]
    relays_sensors_units = [UNIT_WATT, UNIT_KWH]
    relays_sensors_device_classes = [DEVICE_CLASS_POWER, DEVICE_CLASS_ENERGY]
    relays_sensors_tpls = [TPL_POWER, TPL_ENERGY_WMIN]
    relays_bin_sensors = [SENSOR_INPUT]
    relays_bin_sensors_entity_categories = [None]
    relays_bin_sensors_pl = [PL_1_0]
    relays_bin_sensors_tpls = [None]
    relays_bin_sensors_device_classes = [None]
    sensors = [
        SENSOR_TEMPERATURE,
        SENSOR_TOTALWORKTIME,
        SENSOR_RSSI,
        SENSOR_SSID,
        SENSOR_UPTIME,
        SENSOR_IP,
    ]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        None,
        STATE_CLASS_MEASUREMENT,
        None,
        None,
        None,
    ]
    sensors_enabled = [True, False, False, False, False, False]
    sensors_device_classes = [
        DEVICE_CLASS_TEMPERATURE,
        None,
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
    ]
    sensors_units = [UNIT_CELSIUS, UNIT_SECOND, UNIT_DBM, None, None, None]
    sensors_tpls = [TPL_TEMPERATURE, None, TPL_RSSI, TPL_SSID, TPL_UPTIME, TPL_IP]
    sensors_topics = [None, None, TOPIC_INFO, TOPIC_INFO, TOPIC_INFO, TOPIC_ANNOUNCE]
    bin_sensors = [SENSOR_OVERTEMPERATURE, SENSOR_FIRMWARE_UPDATE]
    bin_sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    bin_sensors_enabled = [True, True]
    bin_sensors_device_classes = [DEVICE_CLASS_PROBLEM, DEVICE_CLASS_UPDATE]
    bin_sensors_pl = [PL_1_0, None]
    bin_sensors_tpls = [None, TPL_NEW_FIRMWARE_FROM_INFO]
    bin_sensors_topics = [None, TOPIC_INFO]
    ext_temp_sensors = 1
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLY2_ID or dev_id_prefix == MODEL_SHELLY2_PREFIX:
    model = MODEL_SHELLY2
    relays = 2
    rollers = 1
    inputs = 2
    inputs_types = [VALUE_BUTTON_LONG_PRESS, VALUE_BUTTON_SHORT_PRESS]
    relays_sensors = [SENSOR_POWER, SENSOR_ENERGY]
    relays_sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_TOTAL_INCREASING,
    ]
    relays_sensors_units = [UNIT_WATT, UNIT_KWH]
    relays_sensors_device_classes = [DEVICE_CLASS_POWER, DEVICE_CLASS_ENERGY]
    relays_sensors_tpls = [TPL_POWER, TPL_ENERGY_WMIN]
    relays_bin_sensors = [
        SENSOR_LONGPUSH,
        SENSOR_SHORTPUSH,
        SENSOR_OVERPOWER,
    ]
    relays_bin_sensors_entity_categories = [None, None, ENTITY_CATEGORY_DIAGNOSTIC]
    relays_bin_sensors_pl = [None, None, None]
    relays_bin_sensors_topics = [TOPIC_INPUT_EVENT, TOPIC_INPUT_EVENT, TOPIC_RELAY]
    relays_bin_sensors_tpls = [TPL_LONGPUSH, TPL_SHORTPUSH, TPL_OVERPOWER_RELAY]
    relays_bin_sensors_device_classes = [None, None, DEVICE_CLASS_PROBLEM]
    bin_sensors = [
        SENSOR_FIRMWARE_UPDATE,
        SENSOR_INPUT_0,
        SENSOR_INPUT_1,
    ]
    bin_sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC, None, None]
    bin_sensors_enabled = [True, False, False]
    bin_sensors_pl = [None, PL_1_0, PL_1_0]
    bin_sensors_device_classes = [DEVICE_CLASS_UPDATE, None, None]
    bin_sensors_tpls = [TPL_NEW_FIRMWARE_FROM_INFO, None, None]
    bin_sensors_topics = [TOPIC_INFO, TOPIC_INPUT_0, TOPIC_INPUT_1]
    sensors = [SENSOR_RSSI, SENSOR_SSID, SENSOR_UPTIME, SENSOR_IP, SENSOR_VOLTAGE]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        None,
    ]
    sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        None,
        None,
        None,
        STATE_CLASS_MEASUREMENT,
    ]
    sensors_enabled = [False, False, False, False, True]
    sensors_units = [UNIT_DBM, None, None, None, UNIT_VOLT]
    sensors_device_classes = [
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
        DEVICE_CLASS_VOLTAGE,
    ]
    sensors_tpls = [TPL_RSSI, TPL_SSID, TPL_UPTIME, TPL_IP, TPL_VOLTAGE]
    sensors_topics = [TOPIC_INFO, TOPIC_INFO, TOPIC_INFO, TOPIC_ANNOUNCE, TOPIC_VOLTAGE]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLY25_ID or dev_id_prefix == MODEL_SHELLY25_PREFIX:
    model = MODEL_SHELLY25
    relays = 2
    rollers = 1
    inputs = 2
    inputs_types = [VALUE_BUTTON_LONG_PRESS, VALUE_BUTTON_SHORT_PRESS]
    relays_sensors = [SENSOR_POWER, SENSOR_ENERGY]
    relays_sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_TOTAL_INCREASING,
    ]
    relays_sensors_units = [UNIT_WATT, UNIT_KWH]
    relays_sensors_device_classes = [DEVICE_CLASS_POWER, DEVICE_CLASS_ENERGY]
    relays_sensors_tpls = [TPL_POWER, TPL_ENERGY_WMIN]
    relays_bin_sensors = [
        SENSOR_LONGPUSH,
        SENSOR_SHORTPUSH,
        SENSOR_OVERPOWER,
    ]
    relays_bin_sensors_entity_categories = [None, None, ENTITY_CATEGORY_DIAGNOSTIC]
    relays_bin_sensors_pl = [None, None, None]
    relays_bin_sensors_topics = [TOPIC_INPUT_EVENT, TOPIC_INPUT_EVENT, TOPIC_RELAY]
    relays_bin_sensors_tpls = [TPL_LONGPUSH, TPL_SHORTPUSH, TPL_OVERPOWER_RELAY]
    relays_bin_sensors_device_classes = [None, None, DEVICE_CLASS_PROBLEM]
    sensors = [
        SENSOR_TEMPERATURE,
        SENSOR_RSSI,
        SENSOR_SSID,
        SENSOR_UPTIME,
        SENSOR_IP,
        SENSOR_TEMPERATURE_STATUS,
        SENSOR_VOLTAGE,
    ]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        None,
    ]
    sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        None,
        None,
        None,
        None,
        STATE_CLASS_MEASUREMENT,
    ]
    sensors_enabled = [True, False, False, False, False, True, True]
    sensors_device_classes = [
        DEVICE_CLASS_TEMPERATURE,
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
        None,
        DEVICE_CLASS_VOLTAGE,
    ]
    sensors_units = [UNIT_CELSIUS, UNIT_DBM, None, None, None, None, UNIT_VOLT]
    sensors_tpls = [
        TPL_TEMPERATURE,
        TPL_RSSI,
        TPL_SSID,
        TPL_UPTIME,
        TPL_IP,
        TPL_TEMPERATURE_STATUS,
        TPL_VOLTAGE,
    ]
    sensors_topics = [
        None,
        TOPIC_INFO,
        TOPIC_INFO,
        TOPIC_INFO,
        TOPIC_ANNOUNCE,
        TOPIC_TEMPERATURE_STATUS,
        TOPIC_VOLTAGE,
    ]
    bin_sensors = [
        SENSOR_OVERTEMPERATURE,
        SENSOR_FIRMWARE_UPDATE,
        SENSOR_INPUT_0,
        SENSOR_INPUT_1,
    ]
    bin_sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        None,
        None,
    ]
    bin_sensors_enabled = [True, True, False, False]
    bin_sensors_device_classes = [DEVICE_CLASS_PROBLEM, DEVICE_CLASS_UPDATE, None, None]
    bin_sensors_pl = [PL_1_0, None, PL_1_0, PL_1_0]
    bin_sensors_tpls = [None, TPL_NEW_FIRMWARE_FROM_INFO, None, None]
    bin_sensors_topics = [None, TOPIC_INFO, TOPIC_INPUT_0, TOPIC_INPUT_1]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLYUNI_ID or dev_id_prefix == MODEL_SHELLYUNI_PREFIX:
    model = MODEL_SHELLYUNI
    relays = 2
    inputs = 1
    inputs_types = [VALUE_BUTTON_LONG_PRESS, VALUE_BUTTON_SHORT_PRESS]
    ext_humi_sensors = 1
    ext_temp_sensors = 3
    relays_bin_sensors = [
        SENSOR_INPUT,
        SENSOR_LONGPUSH,
        SENSOR_SHORTPUSH,
        SENSOR_OVERPOWER,
    ]
    relays_bin_sensors_entity_categories = [
        None,
        None,
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    relays_bin_sensors_pl = [PL_1_0, PL_1_0, PL_0_1, None]
    relays_bin_sensors_topics = [
        None,
        TOPIC_INPUT_EVENT,
        TOPIC_INPUT_EVENT,
        TOPIC_RELAY,
    ]
    relays_bin_sensors_tpls = [None, TPL_LONGPUSH, TPL_SHORTPUSH, TPL_OVERPOWER_RELAY]
    relays_bin_sensors_device_classes = [None, None, None, DEVICE_CLASS_PROBLEM]
    sensors = [SENSOR_ADC, SENSOR_RSSI, SENSOR_SSID, SENSOR_UPTIME, SENSOR_IP]
    sensors_entity_categories = [
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        None,
        None,
        None,
    ]
    sensors_enabled = [True, False, False, False, False]
    sensors_device_classes = [
        DEVICE_CLASS_VOLTAGE,
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
    ]
    sensors_units = [UNIT_VOLT, UNIT_DBM, None, None, None]
    sensors_tpls = [TPL_ADC, TPL_RSSI, TPL_SSID, TPL_UPTIME, TPL_IP]
    sensors_topics = [TOPIC_ADC, TOPIC_INFO, TOPIC_INFO, TOPIC_INFO, TOPIC_ANNOUNCE]
    bin_sensors = [SENSOR_FIRMWARE_UPDATE]
    bin_sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC]
    bin_sensors_enabled = [True]
    bin_sensors_device_classes = [DEVICE_CLASS_UPDATE]
    bin_sensors_tpls = [TPL_NEW_FIRMWARE_FROM_INFO]
    bin_sensors_pl = [None]
    bin_sensors_topics = [TOPIC_INFO]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if (
    model_id in (MODEL_SHELLYPLUG_ID, MODEL_SHELLYPLUG_E_ID)
    or dev_id_prefix == MODEL_SHELLYPLUG_PREFIX
):
    model = MODEL_SHELLYPLUG
    relays = 1
    relays_sensors = [SENSOR_POWER, SENSOR_ENERGY]
    relays_sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_TOTAL_INCREASING,
    ]
    relays_sensors_units = [UNIT_WATT, UNIT_KWH]
    relays_sensors_device_classes = [DEVICE_CLASS_POWER, DEVICE_CLASS_ENERGY]
    relays_sensors_tpls = [TPL_POWER, TPL_ENERGY_WMIN]
    relays_bin_sensors = [SENSOR_OVERPOWER]
    relays_bin_sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC]
    relays_bin_sensors_pl = [None]
    relays_bin_sensors_topics = [TOPIC_RELAY]
    relays_bin_sensors_tpls = [TPL_OVERPOWER_RELAY]
    relays_bin_sensors_device_classes = [DEVICE_CLASS_PROBLEM]
    bin_sensors = [SENSOR_FIRMWARE_UPDATE]
    bin_sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC]
    bin_sensors_enabled = [True]
    bin_sensors_device_classes = [DEVICE_CLASS_UPDATE]
    bin_sensors_tpls = [TPL_NEW_FIRMWARE_FROM_INFO]
    bin_sensors_topics = [TOPIC_INFO]
    sensors = [SENSOR_RSSI, SENSOR_SSID, SENSOR_UPTIME, SENSOR_IP]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [STATE_CLASS_MEASUREMENT, None, None, None]
    sensors_enabled = [False, False, False, False]
    sensors_units = [UNIT_DBM, None, None, None]
    sensors_device_classes = [
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
    ]
    sensors_tpls = [TPL_RSSI, TPL_SSID, TPL_UPTIME, TPL_IP]
    sensors_topics = [TOPIC_INFO, TOPIC_INFO, TOPIC_INFO, TOPIC_ANNOUNCE]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLYPLUG_US_ID or dev_id_prefix == MODEL_SHELLYPLUG_US_PREFIX:
    model = MODEL_SHELLYPLUG_US
    relays = 1
    relays_sensors = [SENSOR_POWER, SENSOR_ENERGY]
    relays_sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_TOTAL_INCREASING,
    ]
    relays_sensors_units = [UNIT_WATT, UNIT_KWH]
    relays_sensors_device_classes = [DEVICE_CLASS_POWER, DEVICE_CLASS_ENERGY]
    relays_sensors_tpls = [TPL_POWER, TPL_ENERGY_WMIN]
    relays_bin_sensors = [SENSOR_OVERPOWER]
    relays_bin_sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC]
    relays_bin_sensors_pl = [None]
    relays_bin_sensors_topics = [TOPIC_RELAY]
    relays_bin_sensors_tpls = [TPL_OVERPOWER_RELAY]
    relays_bin_sensors_device_classes = [DEVICE_CLASS_PROBLEM]
    bin_sensors = [SENSOR_FIRMWARE_UPDATE]
    bin_sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC]
    bin_sensors_enabled = [True]
    bin_sensors_device_classes = [DEVICE_CLASS_UPDATE]
    bin_sensors_tpls = [TPL_NEW_FIRMWARE_FROM_INFO]
    bin_sensors_topics = [TOPIC_INFO]
    sensors = [SENSOR_RSSI, SENSOR_SSID, SENSOR_UPTIME, SENSOR_IP]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [STATE_CLASS_MEASUREMENT, None, None, None]
    sensors_enabled = [False, False, False, False]
    sensors_units = [UNIT_DBM, None, None, None]
    sensors_device_classes = [
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
    ]
    sensors_tpls = [TPL_RSSI, TPL_SSID, TPL_UPTIME, TPL_IP]
    sensors_topics = [TOPIC_INFO, TOPIC_INFO, TOPIC_INFO, TOPIC_ANNOUNCE]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLYPLUG_S_ID or dev_id_prefix == MODEL_SHELLYPLUG_S_PREFIX:
    model = MODEL_SHELLYPLUG_S
    relays = 1
    relays_sensors = [SENSOR_POWER, SENSOR_ENERGY]
    relays_sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_TOTAL_INCREASING,
    ]
    relays_sensors_units = [UNIT_WATT, UNIT_KWH]
    relays_sensors_device_classes = [DEVICE_CLASS_POWER, DEVICE_CLASS_ENERGY]
    relays_sensors_tpls = [TPL_POWER, TPL_ENERGY_WMIN]
    relays_bin_sensors = [SENSOR_OVERPOWER]
    relays_bin_sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC]
    relays_bin_sensors_pl = [None]
    relays_bin_sensors_topics = [TOPIC_RELAY]
    relays_bin_sensors_tpls = [TPL_OVERPOWER_RELAY]
    relays_bin_sensors_device_classes = [DEVICE_CLASS_PROBLEM]
    sensors = [SENSOR_TEMPERATURE, SENSOR_RSSI, SENSOR_SSID, SENSOR_UPTIME, SENSOR_IP]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        None,
        None,
        None,
    ]
    sensors_enabled = [True, False, False, False, False]
    sensors_device_classes = [
        DEVICE_CLASS_TEMPERATURE,
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
    ]
    sensors_units = [UNIT_CELSIUS, UNIT_DBM, None, None, None]
    sensors_tpls = [TPL_TEMPERATURE, TPL_RSSI, TPL_SSID, TPL_UPTIME, TPL_IP]
    sensors_topics = [None, TOPIC_INFO, TOPIC_INFO, TOPIC_INFO, TOPIC_ANNOUNCE]
    bin_sensors = [SENSOR_OVERTEMPERATURE, SENSOR_FIRMWARE_UPDATE]
    bin_sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    bin_sensors_enabled = [True, True]
    bin_sensors_device_classes = [DEVICE_CLASS_PROBLEM, DEVICE_CLASS_UPDATE]
    bin_sensors_pl = [PL_1_0, None]
    bin_sensors_tpls = [None, TPL_NEW_FIRMWARE_FROM_INFO]
    bin_sensors_topics = [None, TOPIC_INFO]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLY4PRO_ID or dev_id_prefix == MODEL_SHELLY4PRO_PREFIX:
    model = MODEL_SHELLY4PRO
    relays = 4
    relays_sensors = [SENSOR_POWER, SENSOR_ENERGY]
    relays_sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_TOTAL_INCREASING,
    ]
    relays_sensors_units = [UNIT_WATT, UNIT_KWH]
    relays_sensors_device_classes = [DEVICE_CLASS_POWER, DEVICE_CLASS_ENERGY]
    relays_sensors_tpls = [TPL_POWER, TPL_ENERGY_WMIN]
    relays_bin_sensors = [SENSOR_OVERPOWER, SENSOR_INPUT]
    relays_bin_sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC, None]
    relays_bin_sensors_pl = [None, PL_1_0]
    relays_bin_sensors_topics = [TOPIC_RELAY, None]
    relays_bin_sensors_tpls = [TPL_OVERPOWER_RELAY, None]
    relays_bin_sensors_device_classes = [DEVICE_CLASS_PROBLEM, None]
    bin_sensors = [SENSOR_FIRMWARE_UPDATE]
    bin_sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC]
    bin_sensors_enabled = [True]
    bin_sensors_device_classes = [DEVICE_CLASS_UPDATE]
    bin_sensors_tpls = [TPL_NEW_FIRMWARE_FROM_ANNOUNCE]
    bin_sensors_topics = [TOPIC_ANNOUNCE]
    sensors = [SENSOR_IP]
    sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC]
    sensors_state_classes = [None]
    sensors_enabled = [False]
    sensors_device_classes = [None]
    sensors_units = [None]
    sensors_tpls = [TPL_IP]
    sensors_topics = [TOPIC_ANNOUNCE]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLYHT_ID or dev_id_prefix == MODEL_SHELLYHT_PREFIX:
    model = MODEL_SHELLYHT
    sensors = [
        SENSOR_TEMPERATURE,
        SENSOR_HUMIDITY,
        SENSOR_BATTERY,
        SENSOR_RSSI,
        SENSOR_SSID,
        SENSOR_UPTIME,
        SENSOR_IP,
        SENSOR_TEMPERATURE_F,
    ]
    sensors_entity_categories = [
        None,
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        None,
    ]
    sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        None,
        None,
        None,
        STATE_CLASS_MEASUREMENT,
    ]
    sensors_enabled = [True, True, True, False, False, False, False, True]
    sensors_device_classes = [
        DEVICE_CLASS_TEMPERATURE,
        DEVICE_CLASS_HUMIDITY,
        DEVICE_CLASS_BATTERY,
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
        DEVICE_CLASS_TEMPERATURE,
    ]
    sensors_units = [
        UNIT_CELSIUS,
        UNIT_PERCENT,
        UNIT_PERCENT,
        UNIT_DBM,
        None,
        None,
        None,
        UNIT_FAHRENHEIT,
    ]
    sensors_tpls = [
        TPL_TEMPERATURE,
        TPL_HUMIDITY,
        TPL_BATTERY,
        TPL_RSSI,
        TPL_SSID,
        TPL_UPTIME,
        TPL_IP,
        TPL_TEMPERATURE,
    ]
    sensors_topics = [
        None,
        None,
        None,
        TOPIC_INFO,
        TOPIC_INFO,
        TOPIC_INFO,
        TOPIC_ANNOUNCE,
        TOPIC_TEMPERATURE,
    ]
    bin_sensors = [SENSOR_FIRMWARE_UPDATE, SENSOR_CLOUD]
    bin_sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    bin_sensors_enabled = [True, False]
    bin_sensors_device_classes = [DEVICE_CLASS_UPDATE, DEVICE_CLASS_CONNECTIVITY]
    bin_sensors_tpls = [TPL_NEW_FIRMWARE_FROM_ANNOUNCE, TPL_CLOUD]
    bin_sensors_topics = [TOPIC_ANNOUNCE, TOPIC_INFO]
    bin_sensors_pl = [None, None]
    battery_powered = True

if model_id == MODEL_SHELLYMOTION_ID or dev_id_prefix == MODEL_SHELLYMOTION_PREFIX:
    model = MODEL_SHELLYMOTION
    sensors = [
        SENSOR_LUX,
        SENSOR_BATTERY,
        SENSOR_RSSI,
        SENSOR_IP,
        SENSOR_SSID,
        SENSOR_UPTIME,
    ]
    sensors_entity_categories = [
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        None,
        None,
        None,
    ]
    sensors_enabled = [True, True, False, False, False, False]
    sensors_device_classes = [
        DEVICE_CLASS_ILLUMINANCE,
        DEVICE_CLASS_BATTERY,
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        None,
        DEVICE_CLASS_TIMESTAMP,
    ]
    sensors_units = [UNIT_LUX, UNIT_PERCENT, UNIT_DBM, None, None, None]
    sensors_tpls = [
        TPL_ILLUMINATION,
        TPL_BATTERY_FROM_JSON,
        TPL_RSSI,
        TPL_IP,
        TPL_SSID,
        TPL_UPTIME,
    ]
    sensors_topics = [
        TOPIC_STATUS,
        TOPIC_STATUS,
        TOPIC_INFO,
        TOPIC_ANNOUNCE,
        TOPIC_INFO,
        TOPIC_INFO,
    ]
    bin_sensors = [
        SENSOR_FIRMWARE_UPDATE,
        SENSOR_MOTION,
        SENSOR_VIBRATION,
        SENSOR_CHARGER,
        SENSOR_CLOUD,
    ]
    bin_sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        None,
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    bin_sensors_enabled = [True, True, True, True, False]
    bin_sensors_device_classes = [
        DEVICE_CLASS_UPDATE,
        DEVICE_CLASS_MOTION,
        DEVICE_CLASS_VIBRATION,
        DEVICE_CLASS_BATTERY_CHARGING,
        DEVICE_CLASS_CONNECTIVITY,
    ]
    bin_sensors_pl = [None, None, None, None, None]
    bin_sensors_tpls = [
        TPL_NEW_FIRMWARE_FROM_INFO,
        TPL_MOTION,
        TPL_VIBRATION,
        TPL_CHARGER,
        TPL_CLOUD,
    ]
    bin_sensors_topics = [
        TOPIC_INFO,
        TOPIC_STATUS,
        TOPIC_STATUS,
        TOPIC_INFO,
        TOPIC_INFO,
    ]
    battery_powered = True

if model_id == MODEL_SHELLYGAS_ID or dev_id_prefix == MODEL_SHELLYGAS_PREFIX:
    model = MODEL_SHELLYGAS
    sensors = [
        SENSOR_OPERATION,
        SENSOR_SELF_TEST,
        SENSOR_CONCENTRATION,
        SENSOR_RSSI,
        SENSOR_SSID,
        SENSOR_UPTIME,
        SENSOR_IP,
    ]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [
        None,
        None,
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        None,
        None,
        None,
    ]
    sensors_enabled = [True, True, True, False, False, False, False]
    sensors_device_classes = [
        None,
        None,
        None,
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
    ]
    sensors_tpls = [
        None,
        None,
        TPL_CONCENTRATION,
        TPL_RSSI,
        TPL_SSID,
        TPL_UPTIME,
        TPL_IP,
    ]
    sensors_topics = [
        None,
        None,
        None,
        TOPIC_INFO,
        TOPIC_INFO,
        TOPIC_INFO,
        TOPIC_ANNOUNCE,
    ]
    sensors_units = [None, None, UNIT_PPM, UNIT_DBM, None, None, None]
    bin_sensors = [SENSOR_FIRMWARE_UPDATE, SENSOR_GAS]
    bin_sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC, None]
    bin_sensors_enabled = [True, True]
    bin_sensors_device_classes = [DEVICE_CLASS_UPDATE, DEVICE_CLASS_GAS]
    bin_sensors_tpls = [TPL_NEW_FIRMWARE_FROM_INFO, TPL_GAS]
    bin_sensors_topics = [TOPIC_INFO, None]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        },
        BUTTON_SELF_TEST: {
            ATTR_TOPIC: TOPIC_SELF_TEST,
            ATTR_PAYLOAD: PL_SELF_TEST,
            ATTR_ENABLED: True,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_DIAGNOSTIC,
        },
        BUTTON_MUTE: {
            ATTR_TOPIC: TOPIC_MUTE,
            ATTR_PAYLOAD: PL_MUTE,
            ATTR_ENABLED: True,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
            ATTR_ICON: "mdi:volume-variant-off",
        },
        BUTTON_UNMUTE: {
            ATTR_TOPIC: TOPIC_UNMUTE,
            ATTR_PAYLOAD: PL_UNMUTE,
            ATTR_ENABLED: True,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
            ATTR_ICON: "mdi:volume-high",
        },
    }

if (
    model_id in (MODEL_SHELLYBUTTON1_ID, MODEL_SHELLYBUTTON1V2_ID)
    or dev_id_prefix == MODEL_SHELLYBUTTON1_PREFIX
):
    model = MODEL_SHELLYBUTTON1
    inputs = 1
    inputs_types = [
        VALUE_BUTTON_LONG_PRESS,
        VALUE_BUTTON_SHORT_PRESS,
        VALUE_BUTTON_DOUBLE_PRESS,
        VALUE_BUTTON_TRIPLE_PRESS,
    ]
    sensors = [SENSOR_BATTERY, SENSOR_RSSI, SENSOR_SSID, SENSOR_UPTIME, SENSOR_IP]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        None,
        None,
        None,
    ]
    sensors_enabled = [True, False, False, False, False]
    sensors_device_classes = [
        DEVICE_CLASS_BATTERY,
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
    ]
    sensors_units = [UNIT_PERCENT, UNIT_DBM, None, None, None]
    sensors_tpls = [TPL_BATTERY, TPL_RSSI, TPL_SSID, TPL_UPTIME, TPL_IP]
    sensors_topics = [None, TOPIC_INFO, TOPIC_INFO, TOPIC_INFO, TOPIC_ANNOUNCE]
    bin_sensors = [
        SENSOR_INPUT_0,
        SENSOR_SHORTPUSH,
        SENSOR_DOUBLE_SHORTPUSH,
        SENSOR_TRIPLE_SHORTPUSH,
        SENSOR_LONGPUSH,
        SENSOR_FIRMWARE_UPDATE,
        SENSOR_CHARGER,
    ]
    bin_sensors_entity_categories = [
        None,
        None,
        None,
        None,
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    bin_sensors_enabled = [False, True, True, True, True, True, True]
    bin_sensors_device_classes = [
        None,
        None,
        None,
        None,
        None,
        DEVICE_CLASS_UPDATE,
        DEVICE_CLASS_BATTERY_CHARGING,
    ]
    bin_sensors_tpls = [
        None,
        TPL_SHORTPUSH,
        TPL_DOUBLE_SHORTPUSH,
        TPL_TRIPLE_SHORTPUSH,
        TPL_LONGPUSH,
        TPL_NEW_FIRMWARE_FROM_ANNOUNCE,
        None,
    ]
    bin_sensors_pl = [PL_1_0, None, None, None, None, None, PL_TRUE_FALSE]
    bin_sensors_topics = [
        None,
        TOPIC_INPUT_EVENT_0,
        TOPIC_INPUT_EVENT_0,
        TOPIC_INPUT_EVENT_0,
        TOPIC_INPUT_EVENT_0,
        TOPIC_ANNOUNCE,
        None,
    ]
    battery_powered = True

if model_id == MODEL_SHELLYDW_ID or dev_id_prefix == MODEL_SHELLYDW_PREFIX:
    model = MODEL_SHELLYDW
    sensors = [SENSOR_LUX, SENSOR_BATTERY, SENSOR_TILT, SENSOR_IP]
    sensors_entity_categories = [
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        None,
    ]
    sensors_enabled = [True, True, True, False]
    sensors_device_classes = [
        DEVICE_CLASS_ILLUMINANCE,
        DEVICE_CLASS_BATTERY,
        None,
        None,
    ]
    sensors_units = [UNIT_LUX, UNIT_PERCENT, UNIT_DEGREE, None]
    sensors_tpls = [TPL_LUX, TPL_BATTERY, TPL_TILT, TPL_IP]
    sensors_topics = [None, None, None, TOPIC_ANNOUNCE]
    bin_sensors = [SENSOR_OPENING, SENSOR_VIBRATION, SENSOR_FIRMWARE_UPDATE]
    bin_sensors_entity_categories = [None, None, ENTITY_CATEGORY_DIAGNOSTIC]
    bin_sensors_enabled = [True, True, True]
    bin_sensors_device_classes = [
        DEVICE_CLASS_OPENING,
        DEVICE_CLASS_VIBRATION,
        DEVICE_CLASS_UPDATE,
    ]
    bin_sensors_pl = [PL_OPEN_CLOSE, PL_1_0, None]
    bin_sensors_tpls = [None, None, TPL_NEW_FIRMWARE_FROM_ANNOUNCE]
    bin_sensors_topics = [None, None, TOPIC_ANNOUNCE]
    battery_powered = True

if model_id == MODEL_SHELLYDW2_ID or dev_id_prefix == MODEL_SHELLYDW2_PREFIX:
    model = MODEL_SHELLYDW2
    sensors = [
        SENSOR_LUX,
        SENSOR_BATTERY,
        SENSOR_TILT,
        SENSOR_TEMPERATURE,
        SENSOR_IP,
        SENSOR_TEMPERATURE_F,
    ]
    sensors_entity_categories = [
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
        None,
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
        None,
    ]
    sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        None,
        STATE_CLASS_MEASUREMENT,
    ]
    sensors_enabled = [True, True, True, True, False, True]
    sensors_device_classes = [
        DEVICE_CLASS_ILLUMINANCE,
        DEVICE_CLASS_BATTERY,
        None,
        DEVICE_CLASS_TEMPERATURE,
        None,
        DEVICE_CLASS_TEMPERATURE,
    ]
    sensors_units = [
        UNIT_LUX,
        UNIT_PERCENT,
        UNIT_DEGREE,
        UNIT_CELSIUS,
        None,
        UNIT_FAHRENHEIT,
    ]
    sensors_tpls = [
        TPL_LUX,
        TPL_BATTERY,
        TPL_TILT,
        TPL_TEMPERATURE,
        TPL_IP,
        TPL_TEMPERATURE,
    ]
    sensors_topics = [None, None, None, None, TOPIC_ANNOUNCE, TOPIC_TEMPERATURE]
    bin_sensors = [SENSOR_OPENING, SENSOR_VIBRATION, SENSOR_FIRMWARE_UPDATE]
    bin_sensors_entity_categories = [None, None, ENTITY_CATEGORY_DIAGNOSTIC]
    bin_sensors_enabled = [True, True, True]
    bin_sensors_device_classes = [
        DEVICE_CLASS_OPENING,
        DEVICE_CLASS_VIBRATION,
        DEVICE_CLASS_UPDATE,
    ]
    bin_sensors_pl = [PL_OPEN_CLOSE, PL_1_0, None]
    bin_sensors_tpls = [None, None, TPL_NEW_FIRMWARE_FROM_ANNOUNCE]
    bin_sensors_topics = [None, None, TOPIC_ANNOUNCE]
    battery_powered = True

if model_id == MODEL_SHELLYSMOKE_ID or dev_id_prefix == MODEL_SHELLYSMOKE_PREFIX:
    model = MODEL_SHELLYSMOKE
    sensors = [
        SENSOR_TEMPERATURE,
        SENSOR_BATTERY,
        SENSOR_IP,
    ]
    sensors_entity_categories = [
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [STATE_CLASS_MEASUREMENT, STATE_CLASS_MEASUREMENT, None]
    sensors_enabled = [True, True, False]
    sensors_device_classes = [
        DEVICE_CLASS_TEMPERATURE,
        DEVICE_CLASS_BATTERY,
        None,
    ]
    sensors_units = [UNIT_CELSIUS, UNIT_PERCENT, UNIT_DBM, None, None, None]
    sensors_tpls = [
        TPL_TEMPERATURE,
        TPL_BATTERY,
        TPL_IP,
    ]
    sensors_topics = [None, None, TOPIC_ANNOUNCE]
    bin_sensors = [SENSOR_SMOKE, SENSOR_FIRMWARE_UPDATE]
    bin_sensors_entity_categories = [None, ENTITY_CATEGORY_DIAGNOSTIC]
    bin_sensors_enabled = [True, True]
    bin_sensors_device_classes = [DEVICE_CLASS_SMOKE, DEVICE_CLASS_UPDATE]
    bin_sensors_pl = [PL_TRUE_FALSE, None]
    bin_sensors_tpls = [None, TPL_NEW_FIRMWARE_FROM_INFO]
    bin_sensors_topics = [None, TOPIC_INFO]
    battery_powered = True

if model_id == MODEL_SHELLYSENSE_ID or dev_id_prefix == MODEL_SHELLYSENSE_PREFIX:
    model = MODEL_SHELLYSENSE
    sensors = [
        SENSOR_TEMPERATURE,
        SENSOR_HUMIDITY,
        SENSOR_LUX,
        SENSOR_BATTERY,
        SENSOR_RSSI,
        SENSOR_SSID,
        SENSOR_UPTIME,
        SENSOR_IP,
    ]
    sensors_entity_categories = [
        None,
        None,
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        None,
        None,
        None,
    ]
    sensors_enabled = [True, True, True, True, False, False, False, False]
    sensors_device_classes = [
        DEVICE_CLASS_TEMPERATURE,
        DEVICE_CLASS_HUMIDITY,
        DEVICE_CLASS_ILLUMINANCE,
        DEVICE_CLASS_BATTERY,
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
    ]
    sensors_units = [
        UNIT_CELSIUS,
        UNIT_PERCENT,
        UNIT_LUX,
        UNIT_PERCENT,
        UNIT_DBM,
        None,
        None,
        None,
    ]
    sensors_tpls = [
        TPL_TEMPERATURE,
        TPL_HUMIDITY,
        TPL_LUX,
        TPL_BATTERY,
        TPL_RSSI,
        TPL_SSID,
        TPL_UPTIME,
        TPL_IP,
    ]
    sensors_topics = [
        None,
        None,
        None,
        None,
        TOPIC_INFO,
        TOPIC_INFO,
        TOPIC_INFO,
        TOPIC_ANNOUNCE,
    ]
    bin_sensors = [SENSOR_MOTION, SENSOR_CHARGER, SENSOR_FIRMWARE_UPDATE]
    bin_sensors_entity_categories = [
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    bin_sensors_enabled = [True, True, True]
    bin_sensors_device_classes = [
        DEVICE_CLASS_MOTION,
        DEVICE_CLASS_BATTERY_CHARGING,
        DEVICE_CLASS_UPDATE,
    ]
    bin_sensors_pl = [PL_TRUE_FALSE, PL_TRUE_FALSE, None]
    bin_sensors_tpls = [None, None, TPL_NEW_FIRMWARE_FROM_ANNOUNCE]
    bin_sensors_topics = [None, None, TOPIC_ANNOUNCE]
    battery_powered = True

if model_id == MODEL_SHELLYRGBW2_ID or dev_id_prefix == MODEL_SHELLYRGBW2_PREFIX:
    if mode not in (LIGHT_COLOR, LIGHT_WHITE):
        raise ValueError(f"mode value {mode} is not valid, check script configuration")

    model = MODEL_SHELLYRGBW2

    inputs = 1
    rgbw_lights = 1
    white_lights = 4

    bin_sensors = [
        SENSOR_INPUT_0,
        SENSOR_LONGPUSH_0,
        SENSOR_SHORTPUSH_0,
        SENSOR_FIRMWARE_UPDATE,
    ]
    bin_sensors_entity_categories = [None, None, None, ENTITY_CATEGORY_DIAGNOSTIC]
    bin_sensors_enabled = [False, True, True, True]
    bin_sensors_device_classes = [None, None, None, DEVICE_CLASS_UPDATE]
    bin_sensors_pl = [PL_1_0, None, None, None]
    bin_sensors_topics = [
        TOPIC_INPUT_0,
        TOPIC_INPUT_EVENT_0,
        TOPIC_INPUT_EVENT_0,
        TOPIC_INFO,
    ]
    bin_sensors_tpls = [None, TPL_LONGPUSH, TPL_SHORTPUSH, TPL_NEW_FIRMWARE_FROM_INFO]
    inputs_types = [VALUE_BUTTON_LONG_PRESS, VALUE_BUTTON_SHORT_PRESS]
    lights_bin_sensors = [SENSOR_OVERPOWER]
    lights_bin_sensors_device_classes = [DEVICE_CLASS_PROBLEM]
    lights_bin_sensors_pl = [None]
    lights_bin_sensors_topics = [None]
    lights_bin_sensors_tpls = [TPL_OVERPOWER]
    lights_sensors = [SENSOR_POWER, SENSOR_ENERGY]
    lights_sensors_entity_categories = [None, None]
    lights_sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_TOTAL_INCREASING,
    ]
    lights_sensors_device_classes = [DEVICE_CLASS_POWER, DEVICE_CLASS_ENERGY]
    lights_sensors_tpls = [TPL_POWER, TPL_ENERGY_WMIN]
    lights_sensors_units = [UNIT_WATT, UNIT_KWH]
    sensors = [SENSOR_RSSI, SENSOR_SSID, SENSOR_UPTIME, SENSOR_IP]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [STATE_CLASS_MEASUREMENT, None, None, None]
    sensors_enabled = [False, False, False, False]
    sensors_device_classes = [
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
    ]
    sensors_topics = [TOPIC_INFO, TOPIC_INFO, TOPIC_INFO, TOPIC_ANNOUNCE]
    sensors_tpls = [TPL_RSSI, TPL_SSID, TPL_UPTIME, TPL_IP]
    sensors_units = [UNIT_DBM, None, None, None]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLYDIMMER_ID or dev_id_prefix == MODEL_SHELLYDIMMER_PREFIX:
    model = MODEL_SHELLYDIMMER
    white_lights = 1
    inputs = 2
    inputs_types = [VALUE_BUTTON_LONG_PRESS, VALUE_BUTTON_SHORT_PRESS]
    sensors = [SENSOR_TEMPERATURE, SENSOR_RSSI, SENSOR_SSID, SENSOR_UPTIME, SENSOR_IP]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        None,
        None,
        None,
    ]
    sensors_enabled = [True, False, False, False, False]
    sensors_device_classes = [
        DEVICE_CLASS_TEMPERATURE,
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
    ]
    sensors_units = [UNIT_CELSIUS, UNIT_DBM, None, None, None]
    sensors_tpls = [TPL_TEMPERATURE, TPL_RSSI, TPL_SSID, TPL_UPTIME, TPL_IP]
    sensors_topics = [None, TOPIC_INFO, TOPIC_INFO, TOPIC_INFO, TOPIC_ANNOUNCE]
    bin_sensors = [
        SENSOR_OVERTEMPERATURE,
        SENSOR_OVERLOAD,
        SENSOR_LOADERROR,
        SENSOR_INPUT_0,
        SENSOR_INPUT_1,
        SENSOR_LONGPUSH_0,
        SENSOR_LONGPUSH_1,
        SENSOR_SHORTPUSH_0,
        SENSOR_SHORTPUSH_1,
        SENSOR_FIRMWARE_UPDATE,
    ]
    bin_sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        None,
        None,
        None,
        None,
        None,
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    bin_sensors_enabled = [
        True,
        True,
        False,
        False,
        False,
        True,
        True,
        True,
        True,
        True,
    ]
    bin_sensors_device_classes = [
        DEVICE_CLASS_PROBLEM,
        DEVICE_CLASS_PROBLEM,
        DEVICE_CLASS_PROBLEM,
        None,
        None,
        None,
        None,
        None,
        None,
        DEVICE_CLASS_UPDATE,
    ]
    bin_sensors_pl = [
        PL_1_0,
        PL_1_0,
        PL_1_0,
        PL_1_0,
        PL_1_0,
        None,
        None,
        None,
        None,
        None,
    ]
    bin_sensors_tpls = [
        None,
        None,
        None,
        None,
        None,
        TPL_LONGPUSH,
        TPL_LONGPUSH,
        TPL_SHORTPUSH,
        TPL_SHORTPUSH,
        TPL_NEW_FIRMWARE_FROM_INFO,
    ]
    bin_sensors_topics = [
        None,
        None,
        None,
        TOPIC_INPUT_0,
        TOPIC_INPUT_1,
        TOPIC_INPUT_EVENT_0,
        TOPIC_INPUT_EVENT_1,
        TOPIC_INPUT_EVENT_0,
        TOPIC_INPUT_EVENT_1,
        TOPIC_INFO,
    ]
    lights_sensors = [SENSOR_POWER, SENSOR_ENERGY, SENSOR_OVERPOWER_VALUE]
    lights_sensors_entity_categories = [None, None, ENTITY_CATEGORY_DIAGNOSTIC]
    lights_sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_TOTAL_INCREASING,
        None,
    ]
    lights_sensors_units = [UNIT_WATT, UNIT_KWH, UNIT_WATT]
    lights_sensors_device_classes = [
        DEVICE_CLASS_POWER,
        DEVICE_CLASS_ENERGY,
        DEVICE_CLASS_POWER,
    ]
    lights_sensors_tpls = [TPL_POWER, TPL_ENERGY_WMIN, TPL_POWER]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLYDIMMER2_ID or dev_id_prefix == MODEL_SHELLYDIMMER2_PREFIX:
    model = MODEL_SHELLYDIMMER2
    inputs = 2
    inputs_types = [VALUE_BUTTON_LONG_PRESS, VALUE_BUTTON_SHORT_PRESS]
    white_lights = 1
    sensors = [SENSOR_TEMPERATURE, SENSOR_RSSI, SENSOR_SSID, SENSOR_UPTIME, SENSOR_IP]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        None,
        None,
        None,
    ]
    sensors_enabled = [True, False, False, False, False]
    sensors_device_classes = [
        DEVICE_CLASS_TEMPERATURE,
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
    ]
    sensors_units = [UNIT_CELSIUS, UNIT_DBM, None, None, None]
    sensors_tpls = [TPL_TEMPERATURE, TPL_RSSI, TPL_SSID, TPL_UPTIME, TPL_IP]
    sensors_topics = [None, TOPIC_INFO, TOPIC_INFO, TOPIC_INFO, TOPIC_ANNOUNCE]
    bin_sensors = [
        SENSOR_OVERTEMPERATURE,
        SENSOR_OVERLOAD,
        SENSOR_LOADERROR,
        SENSOR_INPUT_0,
        SENSOR_INPUT_1,
        SENSOR_LONGPUSH_0,
        SENSOR_LONGPUSH_1,
        SENSOR_SHORTPUSH_0,
        SENSOR_SHORTPUSH_1,
        SENSOR_FIRMWARE_UPDATE,
    ]
    bin_sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        None,
        None,
        None,
        None,
        None,
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    bin_sensors_enabled = [
        True,
        True,
        False,
        False,
        False,
        True,
        True,
        True,
        True,
        True,
    ]
    bin_sensors_device_classes = [
        DEVICE_CLASS_PROBLEM,
        DEVICE_CLASS_PROBLEM,
        DEVICE_CLASS_PROBLEM,
        None,
        None,
        None,
        None,
        None,
        None,
        DEVICE_CLASS_UPDATE,
    ]
    bin_sensors_pl = [
        PL_1_0,
        PL_1_0,
        PL_1_0,
        PL_1_0,
        PL_1_0,
        None,
        None,
        None,
        None,
        None,
    ]
    bin_sensors_tpls = [
        None,
        None,
        None,
        None,
        None,
        TPL_LONGPUSH,
        TPL_LONGPUSH,
        TPL_SHORTPUSH,
        TPL_SHORTPUSH,
        TPL_NEW_FIRMWARE_FROM_INFO,
    ]
    bin_sensors_topics = [
        None,
        None,
        None,
        TOPIC_INPUT_0,
        TOPIC_INPUT_1,
        TOPIC_INPUT_EVENT_0,
        TOPIC_INPUT_EVENT_1,
        TOPIC_INPUT_EVENT_0,
        TOPIC_INPUT_EVENT_1,
        TOPIC_INFO,
    ]
    lights_sensors = [SENSOR_POWER, SENSOR_ENERGY, SENSOR_OVERPOWER_VALUE]
    lights_sensors_entity_categories = [None, None, ENTITY_CATEGORY_DIAGNOSTIC]
    lights_sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_TOTAL_INCREASING,
        None,
    ]
    lights_sensors_units = [UNIT_WATT, UNIT_KWH, UNIT_WATT]
    lights_sensors_device_classes = [
        DEVICE_CLASS_POWER,
        DEVICE_CLASS_ENERGY,
        DEVICE_CLASS_POWER,
    ]
    lights_sensors_tpls = [TPL_POWER, TPL_ENERGY_WMIN, TPL_POWER]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLYBULB_ID or dev_id_prefix == MODEL_SHELLYBULB_PREFIX:
    model = MODEL_SHELLYBULB
    rgbw_lights = 1
    bin_sensors = [SENSOR_FIRMWARE_UPDATE]
    bin_sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC]
    bin_sensors_enabled = [True]
    bin_sensors_device_classes = [DEVICE_CLASS_UPDATE]
    bin_sensors_tpls = [TPL_NEW_FIRMWARE_FROM_INFO]
    bin_sensors_topics = [TOPIC_INFO]
    sensors = [SENSOR_RSSI, SENSOR_SSID, SENSOR_UPTIME, SENSOR_IP]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [STATE_CLASS_MEASUREMENT, None, None, None]
    sensors_enabled = [False, False, False, False]
    sensors_units = [UNIT_DBM, None, None, None]
    sensors_device_classes = [
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
    ]
    sensors_tpls = [TPL_RSSI, TPL_SSID, TPL_UPTIME, TPL_IP]
    sensors_topics = [TOPIC_INFO, TOPIC_INFO, TOPIC_INFO, TOPIC_ANNOUNCE]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLYBULBRGBW_ID or dev_id_prefix == MODEL_SHELLYBULBRGBW_PREFIX:
    model = MODEL_SHELLYBULBRGBW
    rgbw_lights = 1
    lights_sensors = [SENSOR_ENERGY, SENSOR_POWER]
    lights_sensors_entity_categories = [None, None]
    lights_sensors_state_classes = [
        STATE_CLASS_TOTAL_INCREASING,
        STATE_CLASS_MEASUREMENT,
    ]
    lights_sensors_units = [UNIT_KWH, UNIT_WATT]
    lights_sensors_device_classes = [DEVICE_CLASS_ENERGY, DEVICE_CLASS_POWER]
    lights_sensors_tpls = [TPL_ENERGY_WMIN, TPL_POWER]
    bin_sensors = [SENSOR_FIRMWARE_UPDATE]
    bin_sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC]
    bin_sensors_enabled = [True]
    bin_sensors_device_classes = [DEVICE_CLASS_UPDATE]
    bin_sensors_tpls = [TPL_NEW_FIRMWARE_FROM_INFO]
    bin_sensors_topics = [TOPIC_INFO]
    sensors = [SENSOR_RSSI, SENSOR_SSID, SENSOR_UPTIME, SENSOR_IP]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [STATE_CLASS_MEASUREMENT, None, None, None]
    sensors_enabled = [False, False, False, False]
    sensors_units = [UNIT_DBM, None, None, None]
    sensors_device_classes = [
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
    ]
    sensors_tpls = [TPL_RSSI, TPL_SSID, TPL_UPTIME, TPL_IP]
    sensors_topics = [TOPIC_INFO, TOPIC_INFO, TOPIC_INFO, TOPIC_ANNOUNCE]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLYDUO_ID or dev_id_prefix == MODEL_SHELLYDUO_PREFIX:
    model = MODEL_SHELLYDUO
    white_lights = 1
    lights_sensors = [SENSOR_ENERGY, SENSOR_POWER]
    lights_sensors_entity_categories = [None, None]
    lights_sensors_state_classes = [
        STATE_CLASS_TOTAL_INCREASING,
        STATE_CLASS_MEASUREMENT,
    ]
    lights_sensors_units = [UNIT_KWH, UNIT_WATT]
    lights_sensors_device_classes = [DEVICE_CLASS_ENERGY, DEVICE_CLASS_POWER]
    lights_sensors_tpls = [TPL_ENERGY_WMIN, TPL_POWER]
    bin_sensors = [SENSOR_FIRMWARE_UPDATE]
    bin_sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC]
    bin_sensors_enabled = [True]
    bin_sensors_device_classes = [DEVICE_CLASS_UPDATE]
    bin_sensors_tpls = [TPL_NEW_FIRMWARE_FROM_INFO]
    bin_sensors_topics = [TOPIC_INFO]
    sensors = [SENSOR_RSSI, SENSOR_SSID, SENSOR_UPTIME, SENSOR_IP]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [STATE_CLASS_MEASUREMENT, None, None, None]
    sensors_enabled = [False, False, False, False]
    sensors_units = [UNIT_DBM, None, None, None]
    sensors_device_classes = [
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
    ]
    sensors_tpls = [TPL_RSSI, TPL_SSID, TPL_UPTIME, TPL_IP]
    sensors_topics = [TOPIC_INFO, TOPIC_INFO, TOPIC_INFO, TOPIC_ANNOUNCE]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLYVINTAGE_ID or dev_id_prefix == MODEL_SHELLYVINTAGE_PREFIX:
    model = MODEL_SHELLYVINTAGE
    white_lights = 1
    lights_sensors = [SENSOR_ENERGY, SENSOR_POWER]
    lights_sensors_entity_categories = [None, None]
    lights_sensors_state_classes = [
        STATE_CLASS_TOTAL_INCREASING,
        STATE_CLASS_MEASUREMENT,
    ]
    lights_sensors_units = [UNIT_KWH, UNIT_WATT]
    lights_sensors_device_classes = [DEVICE_CLASS_ENERGY, DEVICE_CLASS_POWER]
    lights_sensors_tpls = [TPL_ENERGY_WMIN, TPL_POWER]
    bin_sensors = [SENSOR_FIRMWARE_UPDATE]
    bin_sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC]
    bin_sensors_enabled = [True]
    bin_sensors_device_classes = [DEVICE_CLASS_UPDATE]
    bin_sensors_tpls = [TPL_NEW_FIRMWARE_FROM_INFO]
    bin_sensors_topics = [TOPIC_INFO]
    sensors = [SENSOR_RSSI, SENSOR_SSID, SENSOR_UPTIME, SENSOR_IP]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [STATE_CLASS_MEASUREMENT, None, None, None]
    sensors_enabled = [False, False, False, False]
    sensors_units = [UNIT_DBM, None, None, None]
    sensors_device_classes = [
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
    ]
    sensors_tpls = [TPL_RSSI, TPL_SSID, TPL_UPTIME, TPL_IP]
    sensors_topics = [TOPIC_INFO, TOPIC_INFO, TOPIC_INFO, TOPIC_ANNOUNCE]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLYEM_ID or dev_id_prefix == MODEL_SHELLYEM_PREFIX:
    model = MODEL_SHELLYEM
    relays = 1
    meters = 2
    relays_bin_sensors = [SENSOR_OVERPOWER]
    relays_bin_sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC]
    relays_bin_sensors_pl = [None]
    relays_bin_sensors_topics = [TOPIC_RELAY]
    relays_bin_sensors_tpls = [TPL_OVERPOWER_RELAY]
    relays_bin_sensors_device_classes = [DEVICE_CLASS_PROBLEM]
    meters_sensors = [
        SENSOR_POWER,
        SENSOR_REACTIVE_POWER,
        SENSOR_VOLTAGE,
        SENSOR_ENERGY,
        SENSOR_RETURNED_ENERGY,
        SENSOR_TOTAL,
        SENSOR_TOTAL_RETURNED,
    ]
    meters_sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_TOTAL_INCREASING,
        STATE_CLASS_TOTAL_INCREASING,
        STATE_CLASS_TOTAL_INCREASING,
        STATE_CLASS_TOTAL_INCREASING,
    ]
    meters_sensors_units = [
        UNIT_WATT,
        UNIT_VAR,
        UNIT_VOLT,
        UNIT_KWH,
        UNIT_KWH,
        UNIT_KWH,
        UNIT_KWH,
    ]
    meters_sensors_device_classes = [
        DEVICE_CLASS_POWER,
        None,
        DEVICE_CLASS_VOLTAGE,
        DEVICE_CLASS_ENERGY,
        DEVICE_CLASS_ENERGY,
        DEVICE_CLASS_ENERGY,
        DEVICE_CLASS_ENERGY,
    ]
    meters_sensors_tpls = [
        TPL_POWER,
        TPL_POWER,
        TPL_VOLTAGE,
        TPL_ENERGY_WMIN,
        TPL_ENERGY_WMIN,
        TPL_ENERGY_WH,
        TPL_ENERGY_WH,
    ]
    bin_sensors = [SENSOR_FIRMWARE_UPDATE]
    bin_sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC]
    bin_sensors_enabled = [True]
    bin_sensors_device_classes = [DEVICE_CLASS_UPDATE]
    bin_sensors_tpls = [TPL_NEW_FIRMWARE_FROM_INFO]
    bin_sensors_topics = [TOPIC_INFO]
    sensors = [SENSOR_RSSI, SENSOR_SSID, SENSOR_UPTIME, SENSOR_IP]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [STATE_CLASS_MEASUREMENT, None, None, None]
    sensors_enabled = [False, False, False, False]
    sensors_units = [UNIT_DBM, None, None, None]
    sensors_device_classes = [
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
    ]
    sensors_tpls = [TPL_RSSI, TPL_SSID, TPL_UPTIME, TPL_IP]
    sensors_topics = [TOPIC_INFO, TOPIC_INFO, TOPIC_INFO, TOPIC_ANNOUNCE]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLY3EM_ID or dev_id_prefix == MODEL_SHELLY3EM_PREFIX:
    model = MODEL_SHELLY3EM
    relays = 1
    meters = 3
    relays_bin_sensors = [SENSOR_OVERPOWER]
    relays_bin_sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC]
    relays_bin_sensors_pl = [None]
    relays_bin_sensors_topics = [TOPIC_RELAY]
    relays_bin_sensors_tpls = [TPL_OVERPOWER_RELAY]
    relays_bin_sensors_device_classes = [DEVICE_CLASS_PROBLEM]
    meters_sensors = [
        SENSOR_CURRENT,
        SENSOR_POWER,
        SENSOR_POWER_FACTOR,
        SENSOR_VOLTAGE,
        SENSOR_ENERGY,
        SENSOR_RETURNED_ENERGY,
        SENSOR_TOTAL,
        SENSOR_TOTAL_RETURNED,
    ]
    meters_sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_TOTAL_INCREASING,
        STATE_CLASS_TOTAL_INCREASING,
        STATE_CLASS_TOTAL_INCREASING,
        STATE_CLASS_TOTAL_INCREASING,
    ]
    meters_sensors_units = [
        UNIT_AMPERE,
        UNIT_WATT,
        UNIT_PERCENT,
        UNIT_VOLT,
        UNIT_KWH,
        UNIT_KWH,
        UNIT_KWH,
        UNIT_KWH,
    ]
    meters_sensors_device_classes = [
        DEVICE_CLASS_CURRENT,
        DEVICE_CLASS_POWER,
        DEVICE_CLASS_POWER_FACTOR,
        DEVICE_CLASS_VOLTAGE,
        DEVICE_CLASS_ENERGY,
        DEVICE_CLASS_ENERGY,
        DEVICE_CLASS_ENERGY,
        DEVICE_CLASS_ENERGY,
    ]
    meters_sensors_tpls = [
        TPL_CURRENT,
        TPL_POWER,
        TPL_POWER_FACTOR,
        TPL_VOLTAGE,
        TPL_ENERGY_WMIN,
        TPL_ENERGY_WMIN,
        TPL_ENERGY_WH,
        TPL_ENERGY_WH,
    ]
    bin_sensors = [SENSOR_FIRMWARE_UPDATE]
    bin_sensors_entity_categories = [ENTITY_CATEGORY_DIAGNOSTIC]
    bin_sensors_enabled = [True]
    bin_sensors_device_classes = [DEVICE_CLASS_UPDATE]
    bin_sensors_tpls = [TPL_NEW_FIRMWARE_FROM_INFO]
    bin_sensors_topics = [TOPIC_INFO]
    sensors = [SENSOR_RSSI, SENSOR_SSID, SENSOR_UPTIME, SENSOR_IP]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [STATE_CLASS_MEASUREMENT, None, None, None]
    sensors_enabled = [False, False, False, False]
    sensors_units = [UNIT_DBM, None, None, None]
    sensors_device_classes = [
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
    ]
    sensors_tpls = [TPL_RSSI, TPL_SSID, TPL_UPTIME, TPL_IP]
    sensors_topics = [TOPIC_INFO, TOPIC_INFO, TOPIC_INFO, TOPIC_ANNOUNCE]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLYFLOOD_ID or dev_id_prefix == MODEL_SHELLYFLOOD_PREFIX:
    model = MODEL_SHELLYFLOOD
    sensors = [SENSOR_TEMPERATURE, SENSOR_BATTERY, SENSOR_IP, SENSOR_TEMPERATURE_F]
    sensors_entity_categories = [
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        None,
    ]
    sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        None,
        STATE_CLASS_MEASUREMENT,
    ]
    sensors_enabled = [True, True, False, True]
    sensors_device_classes = [
        DEVICE_CLASS_TEMPERATURE,
        DEVICE_CLASS_BATTERY,
        None,
        DEVICE_CLASS_TEMPERATURE,
    ]
    sensors_units = [UNIT_CELSIUS, UNIT_PERCENT, None, UNIT_FAHRENHEIT]
    sensors_tpls = [TPL_TEMPERATURE, TPL_BATTERY, TPL_IP, TPL_TEMPERATURE]
    sensors_topics = [None, None, TOPIC_ANNOUNCE, None, TOPIC_TEMPERATURE]
    bin_sensors = [SENSOR_FLOOD, SENSOR_FIRMWARE_UPDATE]
    bin_sensors_entity_categories = [None, ENTITY_CATEGORY_DIAGNOSTIC]
    bin_sensors_enabled = [True, True]
    bin_sensors_device_classes = [DEVICE_CLASS_MOISTURE, DEVICE_CLASS_UPDATE]
    bin_sensors_pl = [PL_TRUE_FALSE, None]
    bin_sensors_tpls = [None, TPL_NEW_FIRMWARE_FROM_ANNOUNCE]
    bin_sensors_topics = [None, TOPIC_ANNOUNCE]
    battery_powered = True

if model_id == MODEL_SHELLYI3_ID or dev_id_prefix == MODEL_SHELLYI3_PREFIX:
    model = MODEL_SHELLYI3
    inputs = 3
    inputs_types = [
        VALUE_BUTTON_LONG_PRESS,
        VALUE_BUTTON_SHORT_PRESS,
        VALUE_BUTTON_DOUBLE_PRESS,
        VALUE_BUTTON_TRIPLE_PRESS,
        VALUE_BUTTON_SHORT_LONG_PRESS,
        VALUE_BUTTON_LONG_SHORT_PRESS,
    ]
    bin_sensors = [
        SENSOR_INPUT_0,
        SENSOR_INPUT_1,
        SENSOR_INPUT_2,
        SENSOR_SHORTPUSH_0,
        SENSOR_DOUBLE_SHORTPUSH_0,
        SENSOR_TRIPLE_SHORTPUSH_0,
        SENSOR_LONGPUSH_0,
        SENSOR_SHORTPUSH_1,
        SENSOR_DOUBLE_SHORTPUSH_1,
        SENSOR_TRIPLE_SHORTPUSH_1,
        SENSOR_LONGPUSH_1,
        SENSOR_SHORTPUSH_2,
        SENSOR_DOUBLE_SHORTPUSH_2,
        SENSOR_TRIPLE_SHORTPUSH_2,
        SENSOR_LONGPUSH_2,
        SENSOR_SHORTPUSH_LONGPUSH_0,
        SENSOR_SHORTPUSH_LONGPUSH_1,
        SENSOR_SHORTPUSH_LONGPUSH_2,
        SENSOR_LONGPUSH_SHORTPUSH_0,
        SENSOR_LONGPUSH_SHORTPUSH_1,
        SENSOR_LONGPUSH_SHORTPUSH_2,
        SENSOR_FIRMWARE_UPDATE,
    ]
    bin_sensors_entity_categories = [
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    bin_sensors_enabled = [
        False,
        False,
        False,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
        True,
    ]
    bin_sensors_device_classes = [
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        DEVICE_CLASS_UPDATE,
    ]
    bin_sensors_tpls = [
        None,
        None,
        None,
        TPL_SHORTPUSH,
        TPL_DOUBLE_SHORTPUSH,
        TPL_TRIPLE_SHORTPUSH,
        TPL_LONGPUSH,
        TPL_SHORTPUSH,
        TPL_DOUBLE_SHORTPUSH,
        TPL_TRIPLE_SHORTPUSH,
        TPL_LONGPUSH,
        TPL_SHORTPUSH,
        TPL_DOUBLE_SHORTPUSH,
        TPL_TRIPLE_SHORTPUSH,
        TPL_LONGPUSH,
        TPL_SHORTPUSH_LONGPUSH,
        TPL_SHORTPUSH_LONGPUSH,
        TPL_SHORTPUSH_LONGPUSH,
        TPL_LONGPUSH_SHORTPUSH,
        TPL_LONGPUSH_SHORTPUSH,
        TPL_LONGPUSH_SHORTPUSH,
        TPL_NEW_FIRMWARE_FROM_INFO,
    ]
    bin_sensors_topics = [
        TOPIC_INPUT_0,
        TOPIC_INPUT_1,
        TOPIC_INPUT_2,
        TOPIC_INPUT_EVENT_0,
        TOPIC_INPUT_EVENT_0,
        TOPIC_INPUT_EVENT_0,
        TOPIC_INPUT_EVENT_0,
        TOPIC_INPUT_EVENT_1,
        TOPIC_INPUT_EVENT_1,
        TOPIC_INPUT_EVENT_1,
        TOPIC_INPUT_EVENT_1,
        TOPIC_INPUT_EVENT_2,
        TOPIC_INPUT_EVENT_2,
        TOPIC_INPUT_EVENT_2,
        TOPIC_INPUT_EVENT_2,
        TOPIC_INPUT_EVENT_0,
        TOPIC_INPUT_EVENT_1,
        TOPIC_INPUT_EVENT_2,
        TOPIC_INPUT_EVENT_0,
        TOPIC_INPUT_EVENT_1,
        TOPIC_INPUT_EVENT_2,
        TOPIC_INFO,
    ]
    bin_sensors_pl = [
        PL_1_0,
        PL_1_0,
        PL_1_0,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
        None,
    ]
    sensors = [
        SENSOR_RSSI,
        SENSOR_SSID,
        SENSOR_UPTIME,
        SENSOR_IP,
        SENSOR_TEMPERATURE_STATUS,
    ]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [STATE_CLASS_MEASUREMENT, None, None, None, None]
    sensors_enabled = [False, False, False, False, True]
    sensors_units = [UNIT_DBM, None, None, None, None]
    sensors_device_classes = [
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        DEVICE_CLASS_TIMESTAMP,
        None,
        None,
    ]
    sensors_tpls = [
        TPL_RSSI,
        TPL_SSID,
        TPL_UPTIME,
        TPL_IP,
        TPL_TEMPERATURE_STATUS,
    ]
    sensors_topics = [
        TOPIC_INFO,
        TOPIC_INFO,
        TOPIC_INFO,
        TOPIC_ANNOUNCE,
        TOPIC_TEMPERATURE_STATUS,
    ]
    buttons = {
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        }
    }

if model_id == MODEL_SHELLYVALVE_ID:
    model = MODEL_SHELLYVALVE
    battery_powered = True

    climate_entity_option = {
        KEY_MIN_TEMP: 4,
        KEY_MAX_TEMP: 31,
        KEY_MODES: ["heat"],
        KEY_PRECISION: 0.1,
    }
    sensors = [
        SENSOR_BATTERY,
        SENSOR_RSSI,
        SENSOR_IP,
        SENSOR_SSID,
        SENSOR_LAST_RESTART,
    ]
    sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    sensors_state_classes = [
        STATE_CLASS_MEASUREMENT,
        STATE_CLASS_MEASUREMENT,
        None,
        None,
        None,
    ]
    sensors_enabled = [True, False, False, False, False]
    sensors_device_classes = [
        DEVICE_CLASS_BATTERY,
        DEVICE_CLASS_SIGNAL_STRENGTH,
        None,
        None,
        DEVICE_CLASS_TIMESTAMP,
    ]
    sensors_units = [UNIT_PERCENT, UNIT_DBM, None, None, None]
    sensors_tpls = [
        TPL_BATTERY_FROM_JSON,
        TPL_RSSI,
        TPL_IP_FROM_INFO,
        TPL_SSID,
        TPL_UPTIME,
    ]
    sensors_topics = [
        TOPIC_STATUS,
        TOPIC_INFO,
        TOPIC_INFO,
        TOPIC_INFO,
        TOPIC_INFO,
    ]
    bin_sensors = [
        SENSOR_FIRMWARE_UPDATE,
        SENSOR_CHARGER,
        SENSOR_CLOUD,
    ]
    bin_sensors_entity_categories = [
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
        ENTITY_CATEGORY_DIAGNOSTIC,
    ]
    bin_sensors_enabled = [True, True, False]
    bin_sensors_device_classes = [
        DEVICE_CLASS_UPDATE,
        DEVICE_CLASS_BATTERY_CHARGING,
        DEVICE_CLASS_CONNECTIVITY,
    ]
    bin_sensors_pl = [None, None, None]
    bin_sensors_tpls = [
        TPL_NEW_FIRMWARE_FROM_INFO,
        TPL_CHARGER,
        TPL_CLOUD,
    ]
    bin_sensors_topics = [
        TOPIC_INFO,
        TOPIC_INFO,
        TOPIC_INFO,
    ]
    buttons = {
        BUTTON_RESTART: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_RESTART,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_RESTART,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        },
        BUTTON_UPDATE_FIRMWARE: {
            ATTR_TOPIC: TOPIC_COMMAND,
            ATTR_PAYLOAD: PL_UPDATE_FIRMWARE,
            ATTR_ENABLED: True,
            ATTR_DEVICE_CLASS: DEVICE_CLASS_UPDATE,
            ATTR_ENTITY_CATEGORY: ENTITY_CATEGORY_CONFIG,
        },
    }

# buttons
for button, button_options in buttons.items():
    device_config = get_device_config(dev_id)
    if ignore_device_model:
        device_name = clean_name(dev_id)
    else:
        device_name = f"{model} {dev_id.split('-')[-1]}"
    unique_id = f"{dev_id}-{button}".lower()
    config_topic = f"{disc_prefix}/button/{dev_id}-{button}/config".encode(
        "ascii", "ignore"
    ).decode("utf-8")
    default_topic = f"shellies/{dev_id}/"
    availability_topic = "~online"
    command_topic = f"~{button_options[ATTR_TOPIC]}"
    button_name = f"{device_name} {clean_name(button)}"
    expire_after = device_config.get(CONF_EXPIRE_AFTER, EXPIRE_AFTER_FOR_SHELLY_VALVE)

    payload = {
        KEY_NAME: button_name,
        KEY_COMMAND_TOPIC: command_topic,
        KEY_PAYLOAD_PRESS: button_options[ATTR_PAYLOAD],
        KEY_ENABLED_BY_DEFAULT: str(button_options[ATTR_ENABLED]),
        KEY_ENTITY_CATEGORY: button_options[ATTR_ENTITY_CATEGORY],
        KEY_AVAILABILITY_TOPIC: availability_topic,
        KEY_PAYLOAD_AVAILABLE: VALUE_TRUE,
        KEY_PAYLOAD_NOT_AVAILABLE: VALUE_FALSE,
        KEY_UNIQUE_ID: unique_id,
        KEY_QOS: qos,
        KEY_DEVICE: {
            KEY_CONNECTIONS: [[KEY_MAC, format_mac(mac)]],
            KEY_NAME: device_name,
            KEY_MODEL: model,
            KEY_SW_VERSION: fw_ver,
            KEY_MANUFACTURER: ATTR_MANUFACTURER,
            KEY_CONFIGURATION_URL: f"http://{host}/",
        },
        "~": default_topic,
    }
    if button_options.get(ATTR_DEVICE_CLASS):
        payload[KEY_DEVICE_CLASS] = button_options[ATTR_DEVICE_CLASS]
    if button_options.get(ATTR_ICON):
        payload[KEY_ICON] = button_options[ATTR_ICON]
    if dev_id.lower() in ignored:
        payload = ""
    mqtt_publish(config_topic, payload, retain)

# climate entities
if climate_entity_option:
    device_config = get_device_config(dev_id)
    if ignore_device_model:
        device_name = clean_name(dev_id)
    else:
        device_name = f"{model} {dev_id.split('-')[-1]}"
    default_topic = f"shellies/{dev_id}/"
    info_topic = "~info"
    temperature_command_topic = "~thermostat/0/command/target_t"
    availability_topic = "~online"
    unique_id = f"{dev_id}".lower()
    config_topic = f"{disc_prefix}/climate/{dev_id}/config".encode(
        "ascii", "ignore"
    ).decode("utf-8")
    expire_after = device_config.get(CONF_EXPIRE_AFTER, EXPIRE_AFTER_FOR_SHELLY_VALVE)
    payload = {
        KEY_NAME: device_name,
        KEY_ACTION_TOPIC: info_topic,
        KEY_ACTION_TEMPLATE: TPL_ACTION_TEMPLATE.format(
            min_temp=climate_entity_option[KEY_MIN_TEMP]
        ),
        KEY_CURRENT_TEMPERATURE_TOPIC: info_topic,
        KEY_CURRENT_TEMPERATURE_TEMPLATE: TPL_CURRENT_TEMPERATURE,
        KEY_TEMPERATURE_STATE_TOPIC: info_topic,
        KEY_TEMPERATURE_STATE_TEMPLATE: TPL_TARGET_TEMPERATURE,
        KEY_TEMPERATURE_COMMAND_TOPIC: temperature_command_topic,
        KEY_TEMPERATURE_COMMAND_TEMPLATE: TPL_SET_TARGET_TEMPERATURE,
        KEY_MODE_STATE_TOPIC: info_topic,
        KEY_MODE_STATE_TEMPLATE: "heat",
        KEY_EXPIRE_AFTER: expire_after,
        KEY_UNIQUE_ID: unique_id,
        KEY_OPTIMISTIC: VALUE_FALSE,
        KEY_QOS: qos,
        KEY_DEVICE: {
            KEY_CONNECTIONS: [[KEY_MAC, format_mac(mac)]],
            KEY_NAME: device_name,
            KEY_MODEL: model,
            KEY_SW_VERSION: fw_ver,
            KEY_MANUFACTURER: ATTR_MANUFACTURER,
            KEY_CONFIGURATION_URL: f"http://{host}/",
        },
        "~": default_topic,
    }
    payload.update(climate_entity_option)
    if dev_id.lower() in ignored:
        payload = ""
    mqtt_publish(config_topic, payload, retain)

# rollers
for roller_id in range(rollers):
    device_config = get_device_config(dev_id)
    if device_config.get(CONF_POSITION_TEMPLATE):
        position_template = device_config[CONF_POSITION_TEMPLATE]
    else:
        position_template = TPL_POSITION
    set_position_template = device_config.get(CONF_SET_POSITION_TEMPLATE, None)
    if ignore_device_model:
        device_name = clean_name(dev_id)
    else:
        device_name = f"{model} {dev_id.split('-')[-1]}"
    if device_config.get(f"roller-{roller_id}-name"):
        roller_name = device_config[f"roller-{roller_id}-name"]
    else:
        roller_name = f"{device_name} Roller {roller_id}"
    device_class = None
    if device_config.get(f"roller-{roller_id}-class"):
        if device_config[f"roller-{roller_id}-class"] in ROLLER_DEVICE_CLASSES:
            device_class = device_config[f"roller-{roller_id}-class"]
        else:
            wrong_class = device_config[f"roller-{roller_id}-class"]
            logger.error(
                f"{wrong_class} is the wrong roller class, the default value None was used"
            )  # noqa: F821
    default_topic = f"shellies/{dev_id}/"
    state_topic = f"~roller/{roller_id}"
    command_topic = f"{state_topic}/command"
    position_topic = f"{state_topic}/pos"
    set_position_topic = f"{state_topic}/command/pos"
    availability_topic = "~online"
    unique_id = f"{dev_id}-roller-{roller_id}".lower()
    config_topic = f"{disc_prefix}/cover/{dev_id}-roller-{roller_id}/config".encode(
        "ascii", "ignore"
    ).decode("utf-8")
    if roller_mode:
        payload = {
            KEY_NAME: roller_name,
            KEY_COMMAND_TOPIC: command_topic,
            KEY_POSITION_TOPIC: position_topic,
            KEY_STATE_TOPIC: state_topic,
            KEY_STATE_CLOSING: VALUE_CLOSE,
            KEY_STATE_OPENING: VALUE_OPEN,
            KEY_STATE_STOPPED: VALUE_STOP,
            KEY_POSITION_TEMPLATE: position_template,
            KEY_SET_POSITION_TOPIC: set_position_topic,
            KEY_PAYLOAD_OPEN: VALUE_OPEN,
            KEY_PAYLOAD_CLOSE: VALUE_CLOSE,
            KEY_PAYLOAD_STOP: VALUE_STOP,
            KEY_AVAILABILITY_TOPIC: availability_topic,
            KEY_PAYLOAD_AVAILABLE: VALUE_TRUE,
            KEY_PAYLOAD_NOT_AVAILABLE: VALUE_FALSE,
            KEY_UNIQUE_ID: unique_id,
            KEY_OPTIMISTIC: VALUE_FALSE,
            KEY_QOS: qos,
            KEY_DEVICE: {
                KEY_CONNECTIONS: [[KEY_MAC, format_mac(mac)]],
                KEY_NAME: device_name,
                KEY_MODEL: model,
                KEY_SW_VERSION: fw_ver,
                KEY_MANUFACTURER: ATTR_MANUFACTURER,
                KEY_CONFIGURATION_URL: f"http://{host}/",
            },
            "~": default_topic,
        }
        if set_position_template:
            payload[KEY_SET_POSITION_TEMPLATE] = set_position_template
        if device_class:
            payload[KEY_DEVICE_CLASS] = device_class
    else:
        payload = ""
    if dev_id.lower() in ignored:
        payload = ""
    mqtt_publish(config_topic, payload, retain)

# relays
for relay_id in range(relays):
    device_config = get_device_config(dev_id)
    if ignore_device_model:
        device_name = clean_name(dev_id)
    else:
        device_name = f"{model} {dev_id.split('-')[-1]}"
    if device_config.get(f"relay-{relay_id}-name"):
        relay_name = device_config[f"relay-{relay_id}-name"]
    else:
        relay_name = f"{device_name} Relay {relay_id}"
    default_topic = f"shellies/{dev_id}/"
    state_topic = f"~relay/{relay_id}"
    command_topic = f"{state_topic}/command"
    availability_topic = "~online"
    unique_id = f"{dev_id}-relay-{relay_id}".lower()
    config_component = COMP_SWITCH
    if device_config.get(f"relay-{relay_id}"):
        config_component = device_config[f"relay-{relay_id}"]
    for component in relay_components:
        config_topic = (
            f"{disc_prefix}/{component}/{dev_id}-relay-{relay_id}/config".encode(
                "ascii", "ignore"
            ).decode("utf-8")
        )
        if component == config_component and not roller_mode:
            payload = {
                KEY_NAME: relay_name,
                KEY_COMMAND_TOPIC: command_topic,
                KEY_STATE_TOPIC: state_topic,
                KEY_PAYLOAD_OFF: VALUE_OFF,
                KEY_PAYLOAD_ON: VALUE_ON,
                KEY_AVAILABILITY_TOPIC: availability_topic,
                KEY_PAYLOAD_AVAILABLE: VALUE_TRUE,
                KEY_PAYLOAD_NOT_AVAILABLE: VALUE_FALSE,
                KEY_UNIQUE_ID: unique_id,
                KEY_QOS: qos,
                KEY_DEVICE: {
                    KEY_CONNECTIONS: [[KEY_MAC, format_mac(mac)]],
                    KEY_NAME: device_name,
                    KEY_MODEL: model,
                    KEY_SW_VERSION: fw_ver,
                    KEY_MANUFACTURER: ATTR_MANUFACTURER,
                    KEY_CONFIGURATION_URL: f"http://{host}/",
                },
                "~": default_topic,
            }
        else:
            payload = ""
        if dev_id.lower() in ignored:
            payload = ""
        mqtt_publish(config_topic, payload, retain)

    # relay's sensors
    if relay_id == relays - 1:
        for sensor_id in range(len(relays_sensors)):
            device_config = get_device_config(dev_id)
            force_update = False
            if isinstance(device_config.get(CONF_FORCE_UPDATE_SENSORS), bool):
                force_update = device_config.get(CONF_FORCE_UPDATE_SENSORS)
            unique_id = f"{dev_id}-relay-{relays_sensors[sensor_id]}".lower()
            config_topic = f"{disc_prefix}/sensor/{dev_id}-{relays_sensors[sensor_id]}/config".encode(
                "ascii", "ignore"
            ).decode(
                "utf-8"
            )
            if device_config.get(f"relay-{relay_id}-name"):
                sensor_name = f"{device_config[f'relay-{relay_id}-name']} {clean_name(relays_sensors[sensor_id])}"
            else:
                sensor_name = f"{device_name} {clean_name(relays_sensors[sensor_id])}"
            state_topic = f"~relay/{relays_sensors[sensor_id]}"
            if model == MODEL_SHELLY2 or roller_mode:
                payload = {
                    KEY_NAME: sensor_name,
                    KEY_STATE_TOPIC: state_topic,
                    KEY_UNIT: relays_sensors_units[sensor_id],
                    KEY_VALUE_TEMPLATE: relays_sensors_tpls[sensor_id],
                    KEY_DEVICE_CLASS: relays_sensors_device_classes[sensor_id],
                    KEY_AVAILABILITY_TOPIC: availability_topic,
                    KEY_PAYLOAD_AVAILABLE: VALUE_TRUE,
                    KEY_PAYLOAD_NOT_AVAILABLE: VALUE_FALSE,
                    KEY_FORCE_UPDATE: str(force_update),
                    KEY_UNIQUE_ID: unique_id,
                    KEY_QOS: qos,
                    KEY_DEVICE: {
                        KEY_CONNECTIONS: [[KEY_MAC, format_mac(mac)]],
                        KEY_NAME: device_name,
                        KEY_MODEL: model,
                        KEY_SW_VERSION: fw_ver,
                        KEY_MANUFACTURER: ATTR_MANUFACTURER,
                        KEY_CONFIGURATION_URL: f"http://{host}/",
                    },
                    "~": default_topic,
                }
                if relays_sensors_state_classes[sensor_id]:
                    payload[KEY_STATE_CLASS] = relays_sensors_state_classes[sensor_id]
            else:
                payload = ""
            if dev_id.lower() in ignored:
                payload = ""

            mqtt_publish(config_topic, payload, retain)

    # relay's sensors
    for sensor_id in range(len(relays_sensors)):
        device_config = get_device_config(dev_id)
        force_update = False
        if isinstance(device_config.get(CONF_FORCE_UPDATE_SENSORS), bool):
            force_update = device_config.get(CONF_FORCE_UPDATE_SENSORS)
        unique_id = f"{dev_id}-relay-{relays_sensors[sensor_id]}-{relay_id}".lower()
        config_topic = f"{disc_prefix}/sensor/{dev_id}-{relays_sensors[sensor_id]}-{relay_id}/config".encode(
            "ascii", "ignore"
        ).decode(
            "utf-8"
        )
        if device_config.get(f"relay-{relay_id}-name"):
            sensor_name = f"{device_config[f'relay-{relay_id}-name']} {clean_name(relays_sensors[sensor_id])}"
        else:
            sensor_name = (
                f"{device_name} {clean_name(relays_sensors[sensor_id])} {relay_id}"
            )
        state_topic = f"~relay/{relay_id}/{relays_sensors[sensor_id]}"
        if model != MODEL_SHELLY2 and not roller_mode:
            payload = {
                KEY_NAME: sensor_name,
                KEY_STATE_TOPIC: state_topic,
                KEY_UNIT: relays_sensors_units[sensor_id],
                KEY_VALUE_TEMPLATE: relays_sensors_tpls[sensor_id],
                KEY_DEVICE_CLASS: relays_sensors_device_classes[sensor_id],
                KEY_AVAILABILITY_TOPIC: availability_topic,
                KEY_PAYLOAD_AVAILABLE: VALUE_TRUE,
                KEY_PAYLOAD_NOT_AVAILABLE: VALUE_FALSE,
                KEY_FORCE_UPDATE: str(force_update),
                KEY_UNIQUE_ID: unique_id,
                KEY_QOS: qos,
                KEY_DEVICE: {
                    KEY_CONNECTIONS: [[KEY_MAC, format_mac(mac)]],
                    KEY_NAME: device_name,
                    KEY_MODEL: model,
                    KEY_SW_VERSION: fw_ver,
                    KEY_MANUFACTURER: ATTR_MANUFACTURER,
                    KEY_CONFIGURATION_URL: f"http://{host}/",
                },
                "~": default_topic,
            }
            if relays_sensors_state_classes[sensor_id]:
                payload[KEY_STATE_CLASS] = relays_sensors_state_classes[sensor_id]
        else:
            payload = ""
        if dev_id.lower() in ignored:
            payload = ""
        mqtt_publish(config_topic, payload, retain)

    # relay's binary sensors
    for bin_sensor_id in range(len(relays_bin_sensors)):
        device_config = get_device_config(dev_id)
        push_off_delay = True
        if isinstance(device_config.get(CONF_PUSH_OFF_DELAY), bool):
            push_off_delay = device_config.get(CONF_PUSH_OFF_DELAY)
        unique_id = f"{dev_id}-{relays_bin_sensors[bin_sensor_id]}-{relay_id}".lower()
        config_topic = f"{disc_prefix}/binary_sensor/{dev_id}-{relays_bin_sensors[bin_sensor_id]}-{relay_id}/config".encode(
            "ascii", "ignore"
        ).decode(
            "utf-8"
        )
        if device_config.get(f"relay-{relay_id}-name"):
            sensor_name = f"{device_config[f'relay-{relay_id}-name']} {clean_name(relays_bin_sensors[bin_sensor_id])}"
        else:
            sensor_name = f"{device_name} {clean_name(relays_bin_sensors[bin_sensor_id])} {relay_id}"
        if relays_bin_sensors_topics and relays_bin_sensors_topics[bin_sensor_id]:
            state_topic = f"~{relays_bin_sensors_topics[bin_sensor_id]}/{relay_id}"
        else:
            state_topic = f"~{relays_bin_sensors[bin_sensor_id]}/{relay_id}"
        if not roller_mode:
            payload = {
                KEY_NAME: sensor_name,
                KEY_STATE_TOPIC: state_topic,
                KEY_AVAILABILITY_TOPIC: availability_topic,
                KEY_PAYLOAD_AVAILABLE: VALUE_TRUE,
                KEY_PAYLOAD_NOT_AVAILABLE: VALUE_FALSE,
                KEY_UNIQUE_ID: unique_id,
                KEY_QOS: qos,
                KEY_DEVICE: {
                    KEY_CONNECTIONS: [[KEY_MAC, format_mac(mac)]],
                    KEY_NAME: device_name,
                    KEY_MODEL: model,
                    KEY_SW_VERSION: fw_ver,
                    KEY_MANUFACTURER: ATTR_MANUFACTURER,
                    KEY_CONFIGURATION_URL: f"http://{host}/",
                },
                "~": default_topic,
            }
            if (
                relays_bin_sensors[bin_sensor_id]
                in (
                    SENSOR_LONGPUSH,
                    SENSOR_LONGPUSH_0,
                    SENSOR_LONGPUSH_1,
                    SENSOR_LONGPUSH_2,
                    SENSOR_SHORTPUSH,
                    SENSOR_SHORTPUSH_0,
                    SENSOR_SHORTPUSH_1,
                    SENSOR_SHORTPUSH_2,
                    SENSOR_DOUBLE_SHORTPUSH,
                    SENSOR_DOUBLE_SHORTPUSH_0,
                    SENSOR_DOUBLE_SHORTPUSH_1,
                    SENSOR_DOUBLE_SHORTPUSH_2,
                    SENSOR_TRIPLE_SHORTPUSH,
                    SENSOR_TRIPLE_SHORTPUSH_0,
                    SENSOR_TRIPLE_SHORTPUSH_1,
                    SENSOR_TRIPLE_SHORTPUSH_2,
                )
                and push_off_delay
            ):
                payload[KEY_OFF_DELAY] = OFF_DELAY
            if relays_bin_sensors_entity_categories[bin_sensor_id]:
                payload[KEY_ENTITY_CATEGORY] = relays_bin_sensors_entity_categories[
                    bin_sensor_id
                ]
            if relays_bin_sensors_tpls[bin_sensor_id]:
                payload[KEY_VALUE_TEMPLATE] = relays_bin_sensors_tpls[bin_sensor_id]
            else:
                payload[KEY_PAYLOAD_ON] = relays_bin_sensors_pl[bin_sensor_id][VALUE_ON]
                payload[KEY_PAYLOAD_OFF] = relays_bin_sensors_pl[bin_sensor_id][
                    VALUE_OFF
                ]
            if relays_bin_sensors_device_classes[bin_sensor_id]:
                payload[KEY_DEVICE_CLASS] = relays_bin_sensors_device_classes[
                    bin_sensor_id
                ]
            if (
                model
                in (
                    MODEL_SHELLY1PM,
                    MODEL_SHELLY2,
                    MODEL_SHELLY25,
                    MODEL_SHELLY4PRO,
                    MODEL_SHELLYPLUG,
                    MODEL_SHELLYPLUG_S,
                    MODEL_SHELLYPLUG_US,
                )
                and relays_bin_sensors[bin_sensor_id] == SENSOR_OVERPOWER
            ):
                payload[
                    KEY_JSON_ATTRIBUTES_TOPIC
                ] = f"~{relays_bin_sensors_topics[bin_sensor_id]}/{relay_id}/{TOPIC_OVERPOWER_VALUE}"
                payload[KEY_JSON_ATTRIBUTES_TEMPLATE] = TPL_OVERPOWER_VALUE_TO_JSON
        else:
            payload = ""
        if dev_id.lower() in ignored:
            payload = ""
        mqtt_publish(config_topic, payload, retain)

# sensors
for sensor_id in range(len(sensors)):
    device_config = get_device_config(dev_id)
    force_update = False
    use_fahrenheit = device_config.get(CONF_USE_FAHRENHEIT)
    if isinstance(device_config.get(CONF_FORCE_UPDATE_SENSORS), bool):
        force_update = device_config.get(CONF_FORCE_UPDATE_SENSORS)
    if ignore_device_model:
        device_name = clean_name(dev_id)
    else:
        device_name = f"{model} {dev_id.split('-')[-1]}"
    unique_id = f"{dev_id}-{sensors[sensor_id]}".lower()
    config_topic = f"{disc_prefix}/sensor/{dev_id}-{sensors[sensor_id]}/config".encode(
        "ascii", "ignore"
    ).decode("utf-8")
    default_topic = f"shellies/{dev_id}/"
    availability_topic = "~online"
    if sensors[sensor_id] in (SENSOR_RSSI, SENSOR_SSID, SENSOR_ADC, SENSOR_IP):
        sensor_name = f"{device_name} {sensors[sensor_id].upper()}"
    elif sensors[sensor_id] == SENSOR_UPTIME:
        sensor_name = f"{device_name} Last Restart"
    else:
        sensor_name = f"{device_name} {clean_name(sensors[sensor_id])}"
    if sensors[sensor_id] == SENSOR_TEMPERATURE_F:
        sensor_name = f"{device_name} Temperature"
    if sensors_topics[sensor_id]:
        state_topic = f"~{sensors_topics[sensor_id]}"
    elif relays > 0 or white_lights > 0:
        state_topic = f"~{sensors[sensor_id]}"
    else:
        state_topic = f"~sensor/{sensors[sensor_id]}"

    config_component = COMP_SWITCH
    if (
        model
        in (
            MODEL_SHELLYBUTTON1,
            MODEL_SHELLYMOTION,
            MODEL_SHELLYSENSE,
            MODEL_SHELLYVALVE,
        )
        and device_config.get(CONF_POWERED) == ATTR_POWER_AC
    ):
        battery_powered = False
        no_battery_sensor = True
    if battery_powered:
        if model == MODEL_SHELLYMOTION:
            expire_after = device_config.get(
                CONF_EXPIRE_AFTER, EXPIRE_AFTER_FOR_SHELLY_MOTION
            )
        elif model == MODEL_SHELLYVALVE:
            expire_after = device_config.get(
                CONF_EXPIRE_AFTER, EXPIRE_AFTER_FOR_SHELLY_VALVE
            )
        else:
            expire_after = device_config.get(
                CONF_EXPIRE_AFTER, EXPIRE_AFTER_FOR_BATTERY_POWERED
            )

        if device_config.get(CONF_POWERED) == ATTR_POWER_AC:
            no_battery_sensor = True
            expire_after = device_config.get(
                CONF_EXPIRE_AFTER, EXPIRE_AFTER_FOR_AC_POWERED
            )
        if not isinstance(expire_after, int):
            raise TypeError(
                f"expire_after value {expire_after} is not an integer, check script configuration"
            )
    payload = {
        KEY_NAME: sensor_name,
        KEY_STATE_TOPIC: state_topic,
        KEY_FORCE_UPDATE: str(force_update),
        KEY_ENABLED_BY_DEFAULT: str(sensors_enabled[sensor_id]),
        KEY_UNIQUE_ID: unique_id,
        KEY_QOS: qos,
        KEY_DEVICE: {
            KEY_CONNECTIONS: [[KEY_MAC, format_mac(mac)]],
            KEY_NAME: device_name,
            KEY_MODEL: model,
            KEY_SW_VERSION: fw_ver,
            KEY_MANUFACTURER: ATTR_MANUFACTURER,
            KEY_CONFIGURATION_URL: f"http://{host}/",
        },
        "~": default_topic,
    }
    if sensors_entity_categories[sensor_id]:
        payload[KEY_ENTITY_CATEGORY] = sensors_entity_categories[sensor_id]
    if sensors_state_classes[sensor_id]:
        payload[KEY_STATE_CLASS] = sensors_state_classes[sensor_id]
    if model == MODEL_SHELLYDW2 and sensors[sensor_id] == SENSOR_LUX:
        payload[KEY_JSON_ATTRIBUTES_TOPIC] = f"~sensor/{SENSOR_ILLUMINATION}"
        payload[KEY_JSON_ATTRIBUTES_TEMPLATE] = TPL_ILLUMINATION_TO_JSON
    if sensors_units[sensor_id]:
        payload[KEY_UNIT] = sensors_units[sensor_id]
    if sensors_device_classes[sensor_id]:
        payload[KEY_DEVICE_CLASS] = sensors_device_classes[sensor_id]
    if sensors_tpls[sensor_id]:
        payload[KEY_VALUE_TEMPLATE] = sensors_tpls[sensor_id]
    if sensors[sensor_id] == SENSOR_SSID:
        payload[KEY_ICON] = "mdi:wifi"
    elif sensors[sensor_id] == SENSOR_TEMPERATURE_STATUS:
        payload[KEY_ICON] = "mdi:thermometer"
    if battery_powered:
        payload[KEY_EXPIRE_AFTER] = expire_after
    else:
        payload[KEY_AVAILABILITY_TOPIC] = availability_topic
        payload[KEY_PAYLOAD_AVAILABLE] = VALUE_TRUE
        payload[KEY_PAYLOAD_NOT_AVAILABLE] = VALUE_FALSE
    if (
        model in (MODEL_SHELLYBUTTON1, MODEL_SHELLYSENSE, MODEL_SHELLYHT)
        and sensors[sensor_id] in (SENSOR_RSSI, SENSOR_SSID, SENSOR_UPTIME)
        and device_config.get(CONF_POWERED) != ATTR_POWER_AC
    ):
        payload = ""
    if no_battery_sensor and sensors[sensor_id] == SENSOR_BATTERY:
        payload = ""
    if use_fahrenheit and sensors[sensor_id] == SENSOR_TEMPERATURE:
        payload = ""
    if not use_fahrenheit and sensors[sensor_id] == SENSOR_TEMPERATURE_F:
        payload = ""
    if dev_id.lower() in ignored:
        payload = ""
    mqtt_publish(config_topic, payload, retain)

# inputs
for input_id in range(inputs):
    if ignore_device_model:
        device_name = clean_name(dev_id)
    else:
        device_name = f"{model} {dev_id.split('-')[-1]}"
    config_topic = f"{disc_prefix}/device_automation/{dev_id}-input-{input_id}/button_release/config".encode(
        "ascii", "ignore"
    ).decode(
        "utf-8"
    )
    topic = f"shellies/{dev_id}/input/{input_id}"
    payload = {
        KEY_AUTOMATION_TYPE: VALUE_TRIGGER,
        KEY_TOPIC: topic,
        KEY_PAYLOAD: "0",
        KEY_QOS: qos,
        KEY_DEVICE: {
            KEY_CONNECTIONS: [[KEY_MAC, format_mac(mac)]],
            KEY_NAME: device_name,
            KEY_MODEL: model,
            KEY_SW_VERSION: fw_ver,
            KEY_MANUFACTURER: ATTR_MANUFACTURER,
            KEY_CONFIGURATION_URL: f"http://{host}/",
        },
        KEY_TYPE: VALUE_BUTTON_SHORT_RELEASE,
        KEY_SUBTYPE: f"button_{input_id + 1}",
    }
    if dev_id.lower() in ignored:
        payload = ""
    mqtt_publish(config_topic, payload, retain)

    topic = f"shellies/{dev_id}/input_event/{input_id}"
    for event in inputs_types:
        config_topic = f"{disc_prefix}/device_automation/{dev_id}-input-{input_id}/{event}/config".encode(
            "ascii", "ignore"
        ).decode(
            "utf-8"
        )
        payload = {
            KEY_AUTOMATION_TYPE: VALUE_TRIGGER,
            KEY_TOPIC: topic,
            KEY_PAYLOAD: DEVICE_TRIGGERS_MAP[event],
            KEY_VALUE_TEMPLATE: "{{value_json.event}}",
            KEY_QOS: qos,
            KEY_DEVICE: {
                KEY_CONNECTIONS: [[KEY_MAC, format_mac(mac)]],
                KEY_NAME: device_name,
                KEY_MODEL: model,
                KEY_SW_VERSION: fw_ver,
                KEY_MANUFACTURER: ATTR_MANUFACTURER,
                KEY_CONFIGURATION_URL: f"http://{host}/",
            },
            KEY_TYPE: event,
            KEY_SUBTYPE: f"button_{input_id + 1}",
        }
        if dev_id.lower() in ignored:
            payload = ""
        mqtt_publish(config_topic, payload, retain)

# external temperature sensors
for sensor_id in range(ext_temp_sensors):
    device_config = get_device_config(dev_id)
    force_update = False
    if isinstance(device_config.get(CONF_FORCE_UPDATE_SENSORS), bool):
        force_update = device_config.get(CONF_FORCE_UPDATE_SENSORS)
    if ignore_device_model:
        device_name = clean_name(dev_id)
    else:
        device_name = f"{model} {dev_id.split('-')[-1]}"
    unique_id = f"{dev_id}-ext-temperature-{sensor_id}".lower()
    config_topic = (
        f"{disc_prefix}/sensor/{dev_id}-ext-temperature-{sensor_id}/config".encode(
            "ascii", "ignore"
        ).decode("utf-8")
    )
    default_topic = f"shellies/{dev_id}/"
    availability_topic = "~online"
    sensor_name = f"{device_name} External Temperature {sensor_id}"
    state_topic = f"~{SENSOR_EXT_TEMPERATURE}/{sensor_id}"
    if device_config.get(f"ext-temperature-{sensor_id}"):
        payload = {
            KEY_NAME: sensor_name,
            KEY_STATE_TOPIC: state_topic,
            KEY_VALUE_TEMPLATE: TPL_TEMPERATURE_EXT,
            KEY_STATE_CLASS: STATE_CLASS_MEASUREMENT,
            KEY_UNIT: UNIT_CELSIUS,
            KEY_DEVICE_CLASS: SENSOR_TEMPERATURE,
            KEY_FORCE_UPDATE: str(force_update),
            KEY_AVAILABILITY_TOPIC: availability_topic,
            KEY_PAYLOAD_AVAILABLE: VALUE_TRUE,
            KEY_PAYLOAD_NOT_AVAILABLE: VALUE_FALSE,
            KEY_UNIQUE_ID: unique_id,
            KEY_QOS: qos,
            KEY_DEVICE: {
                KEY_CONNECTIONS: [[KEY_MAC, format_mac(mac)]],
                KEY_NAME: device_name,
                KEY_MODEL: model,
                KEY_SW_VERSION: fw_ver,
                KEY_MANUFACTURER: ATTR_MANUFACTURER,
                KEY_CONFIGURATION_URL: f"http://{host}/",
            },
            "~": default_topic,
        }
    else:
        payload = ""
    if dev_id.lower() in ignored:
        payload = ""
    mqtt_publish(config_topic, payload, retain)

# external humidity sensors
for sensor_id in range(ext_humi_sensors):
    device_config = get_device_config(dev_id)
    force_update = False
    if isinstance(device_config.get(CONF_FORCE_UPDATE_SENSORS), bool):
        force_update = device_config.get(CONF_FORCE_UPDATE_SENSORS)
    if ignore_device_model:
        device_name = clean_name(dev_id)
    else:
        device_name = f"{model} {dev_id.split('-')[-1]}"
    unique_id = f"{dev_id}-ext-humidity-{sensor_id}".lower()
    config_topic = (
        f"{disc_prefix}/sensor/{dev_id}-ext-humidity-{sensor_id}/config".encode(
            "ascii", "ignore"
        ).decode("utf-8")
    )
    default_topic = f"shellies/{dev_id}/"
    availability_topic = "~online"
    sensor_name = f"{device_name} External Humidity {sensor_id}"
    state_topic = f"~{SENSOR_EXT_HUMIDITY}/{sensor_id}"
    if device_config.get(f"ext-temperature-{sensor_id}"):
        payload = {
            KEY_NAME: sensor_name,
            KEY_STATE_TOPIC: state_topic,
            KEY_VALUE_TEMPLATE: TPL_HUMIDITY_EXT,
            KEY_STATE_CLASS: STATE_CLASS_MEASUREMENT,
            KEY_UNIT: UNIT_PERCENT,
            KEY_DEVICE_CLASS: SENSOR_HUMIDITY,
            KEY_FORCE_UPDATE: str(force_update),
            KEY_AVAILABILITY_TOPIC: availability_topic,
            KEY_PAYLOAD_AVAILABLE: VALUE_TRUE,
            KEY_PAYLOAD_NOT_AVAILABLE: VALUE_FALSE,
            KEY_UNIQUE_ID: unique_id,
            KEY_QOS: qos,
            KEY_DEVICE: {
                KEY_CONNECTIONS: [[KEY_MAC, format_mac(mac)]],
                KEY_NAME: device_name,
                KEY_MODEL: model,
                KEY_SW_VERSION: fw_ver,
                KEY_MANUFACTURER: ATTR_MANUFACTURER,
                KEY_CONFIGURATION_URL: f"http://{host}/",
            },
            "~": default_topic,
        }
    else:
        payload = ""
    if dev_id.lower() in ignored:
        payload = ""
    mqtt_publish(config_topic, payload, retain)

# binary sensors
for bin_sensor_id in range(len(bin_sensors)):
    device_config = get_device_config(dev_id)
    push_off_delay = True
    if isinstance(device_config.get(CONF_PUSH_OFF_DELAY), bool):
        push_off_delay = device_config.get(CONF_PUSH_OFF_DELAY)
    if (
        model
        in (
            MODEL_SHELLYBUTTON1,
            MODEL_SHELLYMOTION,
            MODEL_SHELLYSENSE,
            MODEL_SHELLYVALVE,
        )
        and device_config.get(CONF_POWERED) == ATTR_POWER_AC
    ):
        battery_powered = False
    if battery_powered:
        if model == MODEL_SHELLYMOTION:
            expire_after = device_config.get(
                CONF_EXPIRE_AFTER, EXPIRE_AFTER_FOR_SHELLY_MOTION
            )
        elif model == MODEL_SHELLYVALVE:
            expire_after = device_config.get(
                CONF_EXPIRE_AFTER, EXPIRE_AFTER_FOR_SHELLY_VALVE
            )
        else:
            expire_after = device_config.get(
                CONF_EXPIRE_AFTER, EXPIRE_AFTER_FOR_BATTERY_POWERED
            )
        if device_config.get(CONF_POWERED) == ATTR_POWER_AC:
            no_battery_sensor = True
            expire_after = device_config.get(
                CONF_EXPIRE_AFTER, EXPIRE_AFTER_FOR_AC_POWERED
            )
        if not isinstance(expire_after, int):
            raise TypeError(
                f"expire_after value {expire_after} is not an integer, check your configuration"
            )
    if ignore_device_model:
        device_name = clean_name(dev_id)
    else:
        device_name = f"{model} {dev_id.split('-')[-1]}"
    unique_id = f"{dev_id}-{bin_sensors[bin_sensor_id].replace(' ', '-').replace('/', '-')}".lower()
    config_topic = f"{disc_prefix}/binary_sensor/{dev_id}-{bin_sensors[bin_sensor_id].replace(' ', '-').replace('/', '-')}/config".encode(
        "ascii", "ignore"
    ).decode(
        "utf-8"
    )
    default_topic = f"shellies/{dev_id}/"
    availability_topic = "~online"
    if bin_sensors[bin_sensor_id] == SENSOR_EXT_SWITCH:
        sensor_name = f"{device_name} External Switch"
    else:
        sensor_name = (
            f"{device_name} {clean_name(bin_sensors[bin_sensor_id].replace('/', ' '))}"
        )
    if bin_sensors_topics[bin_sensor_id]:
        state_topic = f"~{bin_sensors_topics[bin_sensor_id]}"
    elif relays > 0 or white_lights > 0:
        state_topic = f"~{bin_sensors[bin_sensor_id]}"
    elif bin_sensors[bin_sensor_id] == SENSOR_OPENING:
        state_topic = "~sensor/state"
    else:
        state_topic = f"~sensor/{bin_sensors[bin_sensor_id]}"
    payload = {
        KEY_NAME: sensor_name,
        KEY_STATE_TOPIC: state_topic,
        KEY_ENABLED_BY_DEFAULT: str(bin_sensors_enabled[bin_sensor_id]),
        KEY_UNIQUE_ID: unique_id,
        KEY_QOS: qos,
        KEY_DEVICE: {
            KEY_CONNECTIONS: [[KEY_MAC, format_mac(mac)]],
            KEY_NAME: device_name,
            KEY_MODEL: model,
            KEY_SW_VERSION: fw_ver,
            KEY_MANUFACTURER: ATTR_MANUFACTURER,
            KEY_CONFIGURATION_URL: f"http://{host}/",
        },
        "~": default_topic,
    }
    if bin_sensors_entity_categories[bin_sensor_id]:
        payload[KEY_ENTITY_CATEGORY] = bin_sensors_entity_categories[bin_sensor_id]
    if bin_sensors_tpls[bin_sensor_id]:
        payload[KEY_VALUE_TEMPLATE] = bin_sensors_tpls[bin_sensor_id]
    else:
        payload[KEY_PAYLOAD_ON] = bin_sensors_pl[bin_sensor_id][VALUE_ON]
        payload[KEY_PAYLOAD_OFF] = bin_sensors_pl[bin_sensor_id][VALUE_OFF]
    if battery_powered:
        payload[KEY_EXPIRE_AFTER] = expire_after
    else:
        payload[KEY_AVAILABILITY_TOPIC] = availability_topic
        payload[KEY_PAYLOAD_AVAILABLE] = VALUE_TRUE
        payload[KEY_PAYLOAD_NOT_AVAILABLE] = VALUE_FALSE
    if bin_sensors_device_classes[bin_sensor_id]:
        payload[KEY_DEVICE_CLASS] = bin_sensors_device_classes[bin_sensor_id]
    if (
        bin_sensors[bin_sensor_id]
        in (
            SENSOR_LONGPUSH,
            SENSOR_LONGPUSH_0,
            SENSOR_LONGPUSH_1,
            SENSOR_LONGPUSH_2,
            SENSOR_SHORTPUSH,
            SENSOR_SHORTPUSH_0,
            SENSOR_SHORTPUSH_1,
            SENSOR_SHORTPUSH_2,
            SENSOR_DOUBLE_SHORTPUSH,
            SENSOR_DOUBLE_SHORTPUSH_0,
            SENSOR_DOUBLE_SHORTPUSH_1,
            SENSOR_DOUBLE_SHORTPUSH_2,
            SENSOR_TRIPLE_SHORTPUSH,
            SENSOR_TRIPLE_SHORTPUSH_0,
            SENSOR_TRIPLE_SHORTPUSH_1,
            SENSOR_TRIPLE_SHORTPUSH_2,
        )
        and push_off_delay
    ):
        payload[KEY_OFF_DELAY] = OFF_DELAY
    if (
        model == MODEL_SHELLYRGBW2
        and mode == LIGHT_WHITE
        and bin_sensors[bin_sensor_id] == SENSOR_OVERPOWER
    ):
        payload = ""
    if (
        model in (MODEL_SHELLYDW, MODEL_SHELLYDW2)
        and bin_sensors[bin_sensor_id] == SENSOR_OPENING
    ):
        payload[KEY_FORCE_UPDATE] = str(True)
    if model == MODEL_SHELLYGAS and bin_sensors[bin_sensor_id] == SENSOR_GAS:
        payload[KEY_JSON_ATTRIBUTES_TOPIC] = state_topic
        payload[KEY_JSON_ATTRIBUTES_TEMPLATE] = TPL_GAS_TO_JSON
    if (
        bin_sensors[bin_sensor_id] == SENSOR_FIRMWARE_UPDATE
        and bin_sensors_tpls[bin_sensor_id] == TPL_NEW_FIRMWARE_FROM_INFO
    ):
        payload[KEY_JSON_ATTRIBUTES_TOPIC] = f"~{TOPIC_INFO}"
        payload[KEY_JSON_ATTRIBUTES_TEMPLATE] = TPL_UPDATE_TO_JSON
    if (
        model == MODEL_SHELLY1
        and bin_sensors[bin_sensor_id] == SENSOR_EXT_SWITCH
        and not device_config.get(CONF_EXT_SWITCH)
    ):
        payload = ""
    if (
        model == MODEL_SHELLYHT
        and bin_sensors[bin_sensor_id] == SENSOR_CLOUD
        and device_config.get(CONF_POWERED) != ATTR_POWER_AC
    ):
        payload = ""
    if dev_id.lower() in ignored:
        payload = ""
    mqtt_publish(config_topic, payload, retain)

# color lights
for light_id in range(rgbw_lights):
    device_config = get_device_config(dev_id)
    if ignore_device_model:
        device_name = clean_name(dev_id)
    else:
        device_name = f"{model} {dev_id.split('-')[-1]}"
    if device_config.get(f"light-{light_id}-name"):
        light_name = device_config[f"light-{light_id}-name"]
    else:
        light_name = f"{device_name} Light {light_id}"
    default_topic = f"shellies/{dev_id}/"
    state_topic = f"~color/{light_id}/status"
    command_topic = f"~color/{light_id}/set"
    availability_topic = "~online"
    unique_id = f"{dev_id}-light-{light_id}".lower()
    config_topic = f"{disc_prefix}/light/{dev_id}-{light_id}/config".encode(
        "ascii", "ignore"
    ).decode("utf-8")
    if mode == LIGHT_COLOR and model == MODEL_SHELLYRGBW2:
        payload = (
            '{"schema":"template",'
            '"name":"' + light_name + '",'
            '"cmd_t":"' + command_topic + '",'
            '"stat_t":"' + state_topic + '",'
            '"avty_t":"' + availability_topic + '",'
            '"pl_avail":"true",'
            '"pl_not_avail":"false",'
            '"fx_list":["Off", "Meteor Shower", "Gradual Change", "Flash"],'
            '"cmd_on_tpl":"{\\"turn\\":\\"on\\"{%if brightness is defined%},\\"gain\\":{{brightness|float|multiply(0.3922)|round}}{%endif%}{%if red is defined and green is defined and blue is defined%},\\"red\\":{{red}},\\"green\\":{{green}},\\"blue\\":{{blue}}{%endif%}{%if white_value is defined%},\\"white\\":{{white_value}}{%endif%}{%if effect is defined%}{%if effect==\\"Meteor Shower\\"%}\\"effect\\":1{%elif effect==\\"Gradual Change\\"%}\\"effect\\":2{%elif effect==\\"Flash\\"%}\\"effect\\":3{%else%}\\"effect\\":0{%endif%}{%else%}\\"effect\\":0{%endif%}{%if transition is defined%},\\"transition\\":{{min(transition|multiply(1000),'
            + str(MAX_TRANSITION)
            + ')}}{%endif%}}",'
            '"cmd_off_tpl":"{\\"turn\\":\\"off\\"{%if transition is defined%},\\"transition\\":{{min(transition|multiply(1000),'
            + str(MAX_TRANSITION)
            + ')}}{%endif%}}",'
            '"stat_tpl":"{%if value_json.ison%}on{%else%}off{%endif%}",'
            '"bri_tpl":"{{value_json.gain|float|multiply(2.55)|round}}",'
            '"r_tpl":"{{value_json.red}}",'
            '"g_tpl":"{{value_json.green}}",'
            '"b_tpl":"{{value_json.blue}}",'
            '"whit_val_tpl":"{{value_json.white}}",'
            '"fx_tpl":"{%if value_json.effect==1%}Meteor Shower{%elif value_json.effect==2%}Gradual Change{%elif value_json.effect==3%}Flash{%else%}Off{%endif%}",'
            '"uniq_id":"' + unique_id + '",'
            '"qos":"' + str(qos) + '",'
            '"dev": {"ids":["' + mac + '"],'
            '"cns":[["' + KEY_MAC + '","' + format_mac(mac) + '"]],'
            '"name":"' + device_name + '",'
            '"mdl":"' + model + '",'
            '"sw":"' + fw_ver + '",'
            '"mf":"' + ATTR_MANUFACTURER + '"},'
            '"~":"' + default_topic + '"}'
        )
    elif model in (MODEL_SHELLYBULB, MODEL_SHELLYBULBRGBW):
        payload = (
            '{"schema":"template",'
            '"name":"' + light_name + '",'
            '"cmd_t":"' + command_topic + '",'
            '"stat_t":"' + state_topic + '",'
            '"avty_t":"' + availability_topic + '",'
            '"pl_avail":"true",'
            '"pl_not_avail":"false",'
            '"fx_list":["Off", "Meteor Shower", "Gradual Change", "Breath", "Flash", "On/Off Gradual", "Red/Green Change"],'
            '"cmd_on_tpl":"{\\"turn\\":\\"on\\",\\"mode\\":\\"color\\",{%if red is defined and green is defined and blue is defined%}\\"red\\":{{red}},\\"green\\":{{green}},\\"blue\\":{{blue}},{%endif%}{%if white_value is defined%}\\"white\\":{{white_value}},{%endif%}{%if brightness is defined%}\\"gain\\":{{brightness|float|multiply(0.3922)|round}},{%endif%}{%if effect is defined%}{%if effect == \\"Meteor Shower\\"%}\\"effect\\":1{%elif effect == \\"Gradual Change\\"%}\\"effect\\":2{%elif effect == \\"Breath\\"%}\\"effect\\":3{%elif effect == \\"Flash\\"%}\\"effect\\":4{%elif effect == \\"On/Off Gradual\\"%}\\"effect\\":5{%elif effect == \\"Red/Green Change\\"%}\\"effect\\":6{%else%}\\"effect\\":0{%endif%}{%else%}\\"effect\\":0{%endif%}{%if transition is defined%},\\"transition\\":{{min(transition|multiply(1000),'
            + str(MAX_TRANSITION)
            + ')}}{%endif%}}",'
            '"cmd_off_tpl":"{\\"turn\\":\\"off\\",\\"mode\\":\\"color\\",\\"effect\\": 0{%if transition is defined%},\\"transition\\":{{min(transition|multiply(1000),'
            + str(MAX_TRANSITION)
            + ')}}{%endif%}}",'
            '"stat_tpl":"{%if value_json.ison==true and value_json.mode==\\"color\\"%}on{%else%}off{%endif%}",'
            '"bri_tpl":"{{value_json.gain|float|multiply(2.55)|round}}",'
            '"r_tpl":"{{value_json.red}}",'
            '"g_tpl":"{{value_json.green}}",'
            '"b_tpl":"{{value_json.blue}}",'
            '"whit_val_tpl":"{{value_json.white}}",'
            '"fx_tpl":"{%if value_json.effect==1%}Meteor Shower{%elif value_json.effect==2%}Gradual Change{%elif value_json.effect==3%}Breath{%elif value_json.effect==4%}Flash{%elif value_json.effect==5%}On/Off Gradual{%elif value_json.effect==6%}Red/Green Change{%else%}Off{%endif%}",'
            '"uniq_id":"' + unique_id + '",'
            '"qos":"' + str(qos) + '",'
            '"dev": {"ids":["' + mac + '"],'
            '"cns":[["' + KEY_MAC + '","' + format_mac(mac) + '"]],'
            '"name":"' + device_name + '",'
            '"mdl":"' + model + '",'
            '"sw":"' + fw_ver + '",'
            '"mf":"' + ATTR_MANUFACTURER + '"},'
            '"~":"' + default_topic + '"}'
        )
    else:
        payload = ""
    if dev_id.lower() in ignored:
        payload = ""
    mqtt_publish(config_topic, payload, retain)

    # color light's binary sensors
    for bin_sensor_id in range(len(lights_bin_sensors)):
        sensor_name = (
            f"{device_name} {clean_name(lights_bin_sensors[bin_sensor_id])} {light_id}"
        )
        config_topic = f"{disc_prefix}/binary_sensor/{dev_id}-color-{lights_bin_sensors[bin_sensor_id]}-{light_id}/config".encode(
            "ascii", "ignore"
        ).decode(
            "utf-8"
        )
        unique_id = (
            f"{dev_id}-color-{lights_bin_sensors[bin_sensor_id]}-{light_id}".lower()
        )
        if lights_bin_sensors[bin_sensor_id] == SENSOR_INPUT:
            state_topic = f"~{lights_bin_sensors[bin_sensor_id]}/{light_id}"
        else:
            state_topic = f"~color/{light_id}/status"
        if mode == LIGHT_COLOR:
            payload = {
                KEY_NAME: sensor_name,
                KEY_STATE_TOPIC: state_topic,
                KEY_AVAILABILITY_TOPIC: availability_topic,
                KEY_PAYLOAD_AVAILABLE: VALUE_TRUE,
                KEY_PAYLOAD_NOT_AVAILABLE: VALUE_FALSE,
                KEY_UNIQUE_ID: unique_id,
                KEY_QOS: qos,
                KEY_DEVICE: {
                    KEY_CONNECTIONS: [[KEY_MAC, format_mac(mac)]],
                    KEY_NAME: device_name,
                    KEY_MODEL: model,
                    KEY_SW_VERSION: fw_ver,
                    KEY_MANUFACTURER: ATTR_MANUFACTURER,
                    KEY_CONFIGURATION_URL: f"http://{host}/",
                },
                "~": default_topic,
            }
            if (
                lights_bin_sensors_device_classes
                and lights_bin_sensors_device_classes[bin_sensor_id]
            ):
                payload[KEY_DEVICE_CLASS] = lights_bin_sensors_device_classes[
                    bin_sensor_id
                ]
            if lights_bin_sensors_tpls and lights_bin_sensors_tpls[bin_sensor_id]:
                payload[KEY_VALUE_TEMPLATE] = lights_bin_sensors_tpls[bin_sensor_id]
            else:
                payload[KEY_PAYLOAD_ON] = lights_bin_sensors_pl[bin_sensor_id][VALUE_ON]
                payload[KEY_PAYLOAD_OFF] = lights_bin_sensors_pl[bin_sensor_id][
                    VALUE_OFF
                ]
        else:
            payload = ""
        if dev_id.lower() in ignored:
            payload = ""
        mqtt_publish(config_topic, payload, retain)

    # color light's sensors
    for sensor_id in range(len(lights_sensors)):
        device_config = get_device_config(dev_id)
        force_update = False
        if isinstance(device_config.get(CONF_FORCE_UPDATE_SENSORS), bool):
            force_update = device_config.get(CONF_FORCE_UPDATE_SENSORS)
        unique_id = f"{dev_id}-color-{lights_sensors[sensor_id]}-{light_id}".lower()
        config_topic = f"{disc_prefix}/sensor/{dev_id}-color-{lights_sensors[sensor_id]}-{light_id}/config".encode(
            "ascii", "ignore"
        ).decode(
            "utf-8"
        )
        sensor_name = (
            f"{device_name} {clean_name(lights_sensors[sensor_id])} {light_id}"
        )
        if model == MODEL_SHELLYBULBRGBW:
            state_topic = f"~light/{light_id}/{lights_sensors[sensor_id]}"
        elif model == MODEL_SHELLYRGBW2:
            state_topic = f"~color/{light_id}/{lights_sensors[sensor_id]}"
        else:
            state_topic = f"~color/{light_id}/status"
        if mode == LIGHT_COLOR:
            payload = {
                KEY_NAME: sensor_name,
                KEY_STATE_TOPIC: state_topic,
                KEY_UNIT: lights_sensors_units[sensor_id],
                KEY_VALUE_TEMPLATE: lights_sensors_tpls[sensor_id],
                KEY_DEVICE_CLASS: lights_sensors_device_classes[sensor_id],
                KEY_AVAILABILITY_TOPIC: availability_topic,
                KEY_PAYLOAD_AVAILABLE: VALUE_TRUE,
                KEY_PAYLOAD_NOT_AVAILABLE: VALUE_FALSE,
                KEY_FORCE_UPDATE: str(force_update),
                KEY_UNIQUE_ID: unique_id,
                KEY_QOS: qos,
                KEY_DEVICE: {
                    KEY_CONNECTIONS: [[KEY_MAC, format_mac(mac)]],
                    KEY_NAME: device_name,
                    KEY_MODEL: model,
                    KEY_SW_VERSION: fw_ver,
                    KEY_MANUFACTURER: ATTR_MANUFACTURER,
                    KEY_CONFIGURATION_URL: f"http://{host}/",
                },
                "~": default_topic,
            }
            if lights_sensors_state_classes[sensor_id]:
                payload[KEY_STATE_CLASS] = lights_sensors_state_classes[sensor_id]
            if lights_sensors_entity_categories[sensor_id]:
                payload[KEY_ENTITY_CATEGORY] = lights_sensors_entity_categories[
                    sensor_id
                ]
        else:
            payload = ""
        if dev_id.lower() in ignored:
            payload = ""
        mqtt_publish(config_topic, payload, retain)

# white lights
for light_id in range(white_lights):
    device_config = get_device_config(dev_id)
    if ignore_device_model:
        device_name = clean_name(dev_id)
    else:
        device_name = f"{model} {dev_id.split('-')[-1]}"
    if device_config.get(f"light-{light_id}-name"):
        light_name = device_config[f"light-{light_id}-name"]
    else:
        light_name = f"{device_name} Light {light_id}"
    default_topic = f"shellies/{dev_id}/"
    if model in (
        MODEL_SHELLYDIMMER,
        MODEL_SHELLYDIMMER2,
        MODEL_SHELLYDUO,
        MODEL_SHELLYVINTAGE,
    ):
        state_topic = f"~light/{light_id}/status"
        command_topic = f"~light/{light_id}/set"
        unique_id = f"{dev_id}-light-{light_id}".lower()
        config_topic = f"{disc_prefix}/light/{dev_id}-{light_id}/config".encode(
            "ascii", "ignore"
        ).decode("utf-8")
    else:
        state_topic = f"~white/{light_id}/status"
        command_topic = f"~white/{light_id}/set"
        unique_id = f"{dev_id}-light-white-{light_id}".lower()
        config_topic = f"{disc_prefix}/light/{dev_id}-white-{light_id}/config".encode(
            "ascii", "ignore"
        ).decode("utf-8")
    availability_topic = "~online"
    if mode == LIGHT_WHITE and model == MODEL_SHELLYRGBW2:
        payload = (
            '{"schema":"template",'
            '"name":"' + light_name + '",'
            '"cmd_t":"' + command_topic + '",'
            '"stat_t":"' + state_topic + '",'
            '"avty_t":"' + availability_topic + '",'
            '"pl_avail":"true",'
            '"pl_not_avail":"false",'
            '"cmd_on_tpl":"{\\"turn\\":\\"on\\"{%if brightness is defined%},\\"brightness\\":{{brightness|float|multiply(0.3922)|round}}{%endif%}{%if white_value is defined%},\\"white\\":{{white_value}}{%endif%}{%if effect is defined%},\\"effect\\":{{effect}}{%endif%}{%if transition is defined%},\\"transition\\":{{min(transition|multiply(1000),'
            + str(MAX_TRANSITION)
            + ')}}{%endif%}}",'
            '"cmd_off_tpl":"{\\"turn\\":\\"off\\"{%if transition is defined%},\\"transition\\":{{min(transition|multiply(1000),'
            + str(MAX_TRANSITION)
            + ')}}{%endif%}}",'
            '"stat_tpl":"{%if value_json.ison%}on{%else%}off{%endif%}",'
            '"bri_tpl":"{{value_json.brightness|float|multiply(2.55)|round}}",'
            '"uniq_id":"' + unique_id + '",'
            '"qos":"' + str(qos) + '",'
            '"dev": {"ids":["' + mac + '"],'
            '"cns":[["' + KEY_MAC + '","' + format_mac(mac) + '"]],'
            '"name":"' + device_name + '",'
            '"mdl":"' + model + '",'
            '"sw":"' + fw_ver + '",'
            '"mf":"' + ATTR_MANUFACTURER + '"},'
            '"~":"' + default_topic + '"}'
        )
    elif model in (MODEL_SHELLYDIMMER, MODEL_SHELLYDIMMER2):
        payload = (
            '{"schema":"template",'
            '"name":"' + light_name + '",'
            '"cmd_t":"' + command_topic + '",'
            '"stat_t":"' + state_topic + '",'
            '"avty_t":"' + availability_topic + '",'
            '"pl_avail":"true",'
            '"pl_not_avail":"false",'
            '"cmd_on_tpl":"{\\"turn\\":\\"on\\"{%if brightness is defined%},\\"brightness\\":{{brightness|float|multiply(0.3922)|round}}{%endif%}{%if transition is defined%},\\"transition\\":{{min(transition|multiply(1000),'
            + str(MAX_TRANSITION)
            + ')}}{%endif%}}",'
            '"cmd_off_tpl":"{\\"turn\\":\\"off\\"{%if transition is defined%},\\"transition\\":{{min(transition|multiply(1000),'
            + str(MAX_TRANSITION)
            + ')}}{%endif%}}",'
            '"stat_tpl":"{%if value_json.ison%}on{%else%}off{%endif%}",'
            '"bri_tpl":"{{value_json.brightness|float|multiply(2.55)|round}}",'
            '"uniq_id":"' + unique_id + '",'
            '"qos":"' + str(qos) + '",'
            '"dev": {"ids":["' + mac + '"],'
            '"cns":[["' + KEY_MAC + '","' + format_mac(mac) + '"]],'
            '"name":"' + device_name + '",'
            '"mdl":"' + model + '",'
            '"sw":"' + fw_ver + '",'
            '"mf":"' + ATTR_MANUFACTURER + '"},'
            '"~":"' + default_topic + '"}'
        )
    elif model == MODEL_SHELLYDUO:
        payload = (
            '{"schema":"template",'
            '"name":"' + light_name + '",'
            '"cmd_t":"' + command_topic + '",'
            '"stat_t":"' + state_topic + '",'
            '"avty_t":"' + availability_topic + '",'
            '"pl_avail":"true",'
            '"pl_not_avail":"false",'
            '"cmd_on_tpl":"{\\"turn\\":\\"on\\"{%if brightness is defined%},\\"brightness\\":{{brightness|float|multiply(0.3922)|round}}{%endif%}{%if color_temp is defined%},\\"temp\\":{{(1000000/(color_temp|int))|round(0,\\"floor\\")}}{%endif%}{%if transition is defined%},\\"transition\\":{{min(transition|multiply(1000),'
            + str(MAX_TRANSITION)
            + ')}}{%endif%}}",'
            '"cmd_off_tpl":"{\\"turn\\":\\"off\\"{%if transition is defined%},\\"transition\\":{{min(transition|multiply(1000),'
            + str(MAX_TRANSITION)
            + ')}}{%endif%}}",'
            '"stat_tpl":"{%if value_json.ison%}on{%else%}off{%endif%}",'
            '"bri_tpl":"{{value_json.brightness|float|multiply(2.55)|round}}",'
            '"clr_temp_tpl":"{{((1000000/(value_json.temp|int,2700)|max)|round(0,\\"floor\\"))}}",'
            '"max_mireds":370,'
            '"min_mireds":153,'
            '"uniq_id":"' + unique_id + '",'
            '"qos":"' + str(qos) + '",'
            '"dev": {"ids":["' + mac + '"],'
            '"cns":[["' + KEY_MAC + '","' + format_mac(mac) + '"]],'
            '"name":"' + device_name + '",'
            '"mdl":"' + model + '",'
            '"sw":"' + fw_ver + '",'
            '"mf":"' + ATTR_MANUFACTURER + '"},'
            '"~":"' + default_topic + '"}'
        )
    elif model == MODEL_SHELLYVINTAGE:
        payload = (
            '{"schema":"template",'
            '"name":"' + light_name + '",'
            '"cmd_t":"' + command_topic + '",'
            '"stat_t":"' + state_topic + '",'
            '"avty_t":"' + availability_topic + '",'
            '"pl_avail":"true",'
            '"pl_not_avail":"false",'
            '"cmd_on_tpl":"{\\"turn\\":\\"on\\"{%if brightness is defined%},\\"brightness\\":{{brightness|float|multiply(0.3922)|round}}{%endif%}{%if transition is defined%},\\"transition\\":{{min(transition|multiply(1000),'
            + str(MAX_TRANSITION)
            + ')}}{%endif%}}",'
            '"cmd_off_tpl":"{\\"turn\\":\\"off\\"{%if transition is defined%},\\"transition\\":{{min(transition,'
            + str(MAX_TRANSITION)
            + ')|multiply(1000)}}{%endif%}}",'
            '"stat_tpl":"{%if value_json.ison%}on{%else%}off{%endif%}",'
            '"bri_tpl":"{{value_json.brightness|float|multiply(2.55)|round}}",'
            '"uniq_id":"' + unique_id + '",'
            '"qos":"' + str(qos) + '",'
            '"dev": {"ids":["' + mac + '"],'
            '"cns":[["' + KEY_MAC + '","' + format_mac(mac) + '"]],'
            '"name":"' + device_name + '",'
            '"mdl":"' + model + '",'
            '"sw":"' + fw_ver + '",'
            '"mf":"' + ATTR_MANUFACTURER + '"},'
            '"~":"' + default_topic + '"}'
        )
    else:
        payload = ""
    if dev_id.lower() in ignored:
        payload = ""
    mqtt_publish(config_topic, payload, retain)

    # white light's binary sensors
    for bin_sensor_id in range(len(lights_bin_sensors)):
        if (
            lights_bin_sensors[bin_sensor_id] == SENSOR_INPUT and light_id == 0
        ) or lights_bin_sensors[bin_sensor_id] != SENSOR_INPUT:
            unique_id = (
                f"{dev_id}-white-{lights_bin_sensors[bin_sensor_id]}-{light_id}".lower()
            )
            config_topic = f"{disc_prefix}/binary_sensor/{dev_id}-white-{lights_bin_sensors[bin_sensor_id]}-{light_id}/config".encode(
                "ascii", "ignore"
            ).decode(
                "utf-8"
            )
            if lights_bin_sensors[bin_sensor_id] == SENSOR_INPUT:
                state_topic = f"~{lights_bin_sensors[bin_sensor_id]}/{light_id}"
            else:
                state_topic = f"~white/{light_id}/status"
            sensor_name = f"{device_name} {clean_name(lights_bin_sensors[bin_sensor_id])} {light_id}"
            if mode != LIGHT_COLOR:
                payload = {
                    KEY_NAME: sensor_name,
                    KEY_STATE_TOPIC: state_topic,
                    KEY_AVAILABILITY_TOPIC: availability_topic,
                    KEY_PAYLOAD_AVAILABLE: VALUE_TRUE,
                    KEY_PAYLOAD_NOT_AVAILABLE: VALUE_FALSE,
                    KEY_UNIQUE_ID: unique_id,
                    KEY_QOS: qos,
                    KEY_DEVICE: {
                        KEY_CONNECTIONS: [[KEY_MAC, format_mac(mac)]],
                        KEY_NAME: device_name,
                        KEY_MODEL: model,
                        KEY_SW_VERSION: fw_ver,
                        KEY_MANUFACTURER: ATTR_MANUFACTURER,
                        KEY_CONFIGURATION_URL: f"http://{host}/",
                    },
                    "~": default_topic,
                }
                if (
                    lights_bin_sensors_device_classes
                    and lights_bin_sensors_device_classes[bin_sensor_id]
                ):
                    payload[KEY_DEVICE_CLASS] = lights_bin_sensors_device_classes[
                        bin_sensor_id
                    ]
                if lights_bin_sensors_tpls and lights_bin_sensors_tpls[bin_sensor_id]:
                    payload[KEY_VALUE_TEMPLATE] = lights_bin_sensors_tpls[bin_sensor_id]
                else:
                    payload[KEY_PAYLOAD_ON] = lights_bin_sensors_pl[bin_sensor_id][
                        VALUE_ON
                    ]
                    payload[KEY_PAYLOAD_OFF] = lights_bin_sensors_pl[bin_sensor_id][
                        VALUE_OFF
                    ]
            else:
                payload = ""
            if dev_id.lower() in ignored:
                payload = ""
            mqtt_publish(config_topic, payload, retain)

    # white light's sensors
    for sensor_id in range(len(lights_sensors)):
        device_config = get_device_config(dev_id)
        force_update = False
        if isinstance(device_config.get(CONF_FORCE_UPDATE_SENSORS), bool):
            force_update = device_config.get(CONF_FORCE_UPDATE_SENSORS)
        unique_id = f"{dev_id}-white-{lights_sensors[sensor_id]}-{light_id}".lower()
        config_topic = f"{disc_prefix}/sensor/{dev_id}-white-{lights_sensors[sensor_id]}-{light_id}/config".encode(
            "ascii", "ignore"
        ).decode(
            "utf-8"
        )
        sensor_name = (
            f"{device_name} {clean_name(lights_sensors[sensor_id])} {light_id}"
        )
        if model in (
            MODEL_SHELLYDIMMER,
            MODEL_SHELLYDIMMER2,
            MODEL_SHELLYDUO,
            MODEL_SHELLYVINTAGE,
        ):
            state_topic = f"~light/{light_id}/{lights_sensors[sensor_id]}"
        elif model == MODEL_SHELLYRGBW2:
            state_topic = f"~white/{light_id}/{lights_sensors[sensor_id]}"
        else:
            state_topic = f"~white/{light_id}/status"
        if (
            model
            in (
                MODEL_SHELLYDIMMER,
                MODEL_SHELLYDIMMER2,
                MODEL_SHELLYDUO,
                MODEL_SHELLYVINTAGE,
                MODEL_SHELLYRGBW2,
            )
            and mode != LIGHT_COLOR
        ):
            payload = {
                KEY_NAME: sensor_name,
                KEY_STATE_TOPIC: state_topic,
                KEY_UNIT: lights_sensors_units[sensor_id],
                KEY_VALUE_TEMPLATE: lights_sensors_tpls[sensor_id],
                KEY_DEVICE_CLASS: lights_sensors_device_classes[sensor_id],
                KEY_AVAILABILITY_TOPIC: availability_topic,
                KEY_PAYLOAD_AVAILABLE: VALUE_TRUE,
                KEY_PAYLOAD_NOT_AVAILABLE: VALUE_FALSE,
                KEY_FORCE_UPDATE: str(force_update),
                KEY_UNIQUE_ID: unique_id,
                KEY_QOS: qos,
                KEY_DEVICE: {
                    KEY_CONNECTIONS: [[KEY_MAC, format_mac(mac)]],
                    KEY_NAME: device_name,
                    KEY_MODEL: model,
                    KEY_SW_VERSION: fw_ver,
                    KEY_MANUFACTURER: ATTR_MANUFACTURER,
                    KEY_CONFIGURATION_URL: f"http://{host}/",
                },
                "~": default_topic,
            }
            if lights_sensors_entity_categories[sensor_id]:
                payload[KEY_ENTITY_CATEGORY] = lights_sensors_entity_categories[
                    sensor_id
                ]
            if lights_sensors_state_classes[sensor_id]:
                payload[KEY_STATE_CLASS] = lights_sensors_state_classes[sensor_id]
        else:
            payload = ""
        if dev_id.lower() in ignored:
            payload = ""
        mqtt_publish(config_topic, payload, retain)

# meters
for meter_id in range(meters):
    device_config = get_device_config(dev_id)
    force_update = False
    if isinstance(device_config.get(CONF_FORCE_UPDATE_SENSORS), bool):
        force_update = device_config.get(CONF_FORCE_UPDATE_SENSORS)
    if ignore_device_model:
        device_name = clean_name(dev_id)
    else:
        device_name = f"{model} {dev_id.split('-')[-1]}"
    default_topic = f"shellies/{dev_id}/"
    availability_topic = "~online"
    for sensor_id in range(len(meters_sensors)):
        unique_id = f"{dev_id}-emeter-{meters_sensors[sensor_id]}-{meter_id}".lower()
        config_topic = f"{disc_prefix}/sensor/{dev_id}-emeter-{meters_sensors[sensor_id]}-{meter_id}/config".encode(
            "ascii", "ignore"
        ).decode(
            "utf-8"
        )
        sensor_name = (
            f"{device_name} Meter {clean_name(meters_sensors[sensor_id])} {meter_id}"
        )
        state_topic = f"~emeter/{meter_id}/{meters_sensors[sensor_id]}"
        payload = {
            KEY_NAME: sensor_name,
            KEY_STATE_TOPIC: state_topic,
            KEY_UNIT: meters_sensors_units[sensor_id],
            KEY_VALUE_TEMPLATE: meters_sensors_tpls[sensor_id],
            KEY_AVAILABILITY_TOPIC: availability_topic,
            KEY_PAYLOAD_AVAILABLE: VALUE_TRUE,
            KEY_PAYLOAD_NOT_AVAILABLE: VALUE_FALSE,
            KEY_FORCE_UPDATE: str(force_update),
            KEY_UNIQUE_ID: unique_id,
            KEY_QOS: qos,
            KEY_DEVICE: {
                KEY_CONNECTIONS: [[KEY_MAC, format_mac(mac)]],
                KEY_NAME: device_name,
                KEY_MODEL: model,
                KEY_SW_VERSION: fw_ver,
                KEY_MANUFACTURER: ATTR_MANUFACTURER,
                KEY_CONFIGURATION_URL: f"http://{host}/",
            },
            "~": default_topic,
        }
        if meters_sensors_state_classes[sensor_id]:
            payload[KEY_STATE_CLASS] = meters_sensors_state_classes[sensor_id]
        if meters_sensors_device_classes and meters_sensors_device_classes[sensor_id]:
            payload[KEY_DEVICE_CLASS] = meters_sensors_device_classes[sensor_id]
        if dev_id.lower() in ignored:
            payload = ""
        mqtt_publish(config_topic, payload, retain)
