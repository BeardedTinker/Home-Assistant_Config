"""Constants for breaking_changes."""
# Base component constants
DOMAIN = "breaking_changes"
DOMAIN_DATA = "{}_data".format(DOMAIN)
VERSION = "0.4.1"
PLATFORMS = ["sensor"]
ISSUE_URL = "https://github.com/custom-components/breaking_changes/issues"

STARTUP = """
-------------------------------------------------------------------
{name}
Version: {version}
This is a custom component
If you have any issues with this you need to open an issue here:
{issueurl}
-------------------------------------------------------------------
"""

# Operational
URL = "https://hachanges.entrypoint.xyz/{0}-{1}/json"

# Icons
ICON = "mdi:package-up"

# Configuration
CONF_NAME = "name"
CONF_SCAN_INTERVAL = "scan_interval"

# Defaults
DEFAULT_NAME = "Potential breaking changes"

# Interval in seconds
INTERVAL = 60
