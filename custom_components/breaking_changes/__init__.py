"""
Component to show with breaking_changes.

For more details about this component, please refer to
https://github.com/custom-components/breaking_changes
"""
import logging
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.helpers import discovery
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from integrationhelper import Throttle, WebClient
from pyhaversion import LocalVersion, PyPiVersion

from .const import (
    CONF_NAME,
    CONF_SCAN_INTERVAL,
    DEFAULT_NAME,
    DOMAIN,
    DOMAIN_DATA,
    INTERVAL,
    ISSUE_URL,
    PLATFORMS,
    STARTUP,
    URL,
    VERSION,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
                vol.Optional(CONF_SCAN_INTERVAL): cv.positive_int,
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass, config):
    """Set up this component."""

    # Print startup message
    startup = STARTUP.format(name=DOMAIN, version=VERSION, issueurl=ISSUE_URL)
    _LOGGER.info(startup)

    throttle = Throttle()

    # Create DATA dict
    hass.data[DOMAIN_DATA] = {}
    hass.data[DOMAIN_DATA]["throttle"] = throttle
    hass.data[DOMAIN_DATA]["components"] = ["homeassistant"]
    hass.data[DOMAIN_DATA]["potential"] = {}

    throttle.interval = timedelta(
        seconds=config[DOMAIN].get(CONF_SCAN_INTERVAL, INTERVAL)
    )

    # Load platforms
    for platform in PLATFORMS:
        # Get platform specific configuration
        platform_config = config[DOMAIN]

        hass.async_create_task(
            discovery.async_load_platform(
                hass, platform, DOMAIN, platform_config, config
            )
        )

    return True


async def update_data(hass):
    """Update data."""
    throttle = hass.data[DOMAIN_DATA]["throttle"]
    if throttle.throttle:
        return

    versions = set()
    integrations = set()
    covered = set()
    changes = []

    hass.data[DOMAIN_DATA]["potential"] = {}

    session = async_get_clientsession(hass)
    webclient = WebClient(session)
    localversion = LocalVersion(hass.loop, session)
    pypiversion = PyPiVersion(hass.loop, session)
    throttle.set_last_run()

    try:
        await localversion.get_version()
        currentversion = localversion.version.split(".")[1]

        await pypiversion.get_version()
        remoteversion = pypiversion.version.split(".")[1]
    except Exception:  # pylint: disable=broad-except
        _LOGGER.warning("Could not get version data.")
        return

    if currentversion == remoteversion:
        _LOGGER.debug(
            "Current version is %s and remote version is %s skipping update",
            currentversion,
            remoteversion,
        )
        return

    for integration in hass.config.components or []:
        if "." in integration:
            integration = integration.split(".")[0]
        integrations.add(integration)

    _LOGGER.debug("Loaded components - %s", integrations)

    try:
        _LOGGER.debug("Running update")
        request = await webclient.async_get_json(
            URL.format(currentversion, remoteversion)
        )
        _LOGGER.debug(request)

        for change in request or []:
            if change["pull"] in covered:
                continue

            if change["integration"] in integrations:
                data = {
                    "title": change["title"],
                    "integration": change["integration"],
                    "prlink": change["prlink"],
                    "doclink": change["doclink"],
                    "description": change["description"],
                }

                changes.append(data)
                covered.add(change["pull"])

                if change["homeassistant"] not in versions:
                    versions.add(change["homeassistant"])

        hass.data[DOMAIN_DATA]["potential"]["changes"] = changes
        hass.data[DOMAIN_DATA]["potential"]["versions"] = versions
    except Exception as error:  # pylint: disable=broad-except
        _LOGGER.error("Could not update data - %s", error)
