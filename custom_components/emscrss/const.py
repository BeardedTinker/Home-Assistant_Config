"""Constants for emscrss."""
# Base component constants
NAME = "EMSC Earthquake RSS Feed"
DOMAIN = "emscrss"
DOMAIN_DATA = f"{DOMAIN}_data"
VERSION = "0.1"
ATTRIBUTION = "Data provided by https://www.emsc-csem.org/service/rss/"
ISSUE_URL = "https://github.com/msekoranja/emsc-hacs-repository/issues"

# Icons
ICON = "mdi:alert"

# Platforms
SENSOR = "sensor"
PLATFORMS = [SENSOR]

# Configuration and options

# Defaults
DEFAULT_NAME = DOMAIN


STARTUP_MESSAGE = f"""
-------------------------------------------------------------------
{NAME}
Version: {VERSION}
This is a custom integration!
If you have any issues with this you need to open an issue here:
{ISSUE_URL}
-------------------------------------------------------------------
"""
