"""Component to integrate with garbage_colection."""

import logging
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME
from homeassistant.helpers import discovery

from .const import (
    ATTR_LAST_COLLECTION,
    CONF_FREQUENCY,
    CONF_SENSORS,
    DOMAIN,
    SENSOR_PLATFORM,
    configuration,
)

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)

config_definition = configuration()

SENSOR_SCHEMA = vol.Schema(config_definition.compile_schema())

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {vol.Optional(CONF_SENSORS): vol.All(cv.ensure_list, [SENSOR_SCHEMA])}
        )
    },
    extra=vol.ALLOW_EXTRA,
)

COLLECT_NOW_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITY_ID): cv.string,
        vol.Optional(ATTR_LAST_COLLECTION): cv.datetime,
    }
)


async def async_setup(hass, config):
    """Set up this component using YAML."""

    def handle_collect_garbage(call):
        """Handle the service call."""
        entity_id = call.data.get(CONF_ENTITY_ID)
        last_collection = call.data.get(ATTR_LAST_COLLECTION)
        _LOGGER.debug("called collect_garbage for %s", entity_id)
        try:
            entity = hass.data[DOMAIN][SENSOR_PLATFORM][entity_id]
            if last_collection is None:
                entity.last_collection = dt_util.now()
            else:
                entity.last_collection = dt_util.as_local(last_collection)
        except Exception as err:
            _LOGGER.error("Failed setting last collection for %s - %s", entity_id, err)
        hass.services.call("homeassistant", "update_entity", {"entity_id": entity_id})

    if DOMAIN not in hass.services.async_services():
        hass.services.async_register(
            DOMAIN, "collect_garbage", handle_collect_garbage, schema=COLLECT_NOW_SCHEMA
        )
    else:
        _LOGGER.debug("Service already registered")

    if config.get(DOMAIN) is None:
        # We get here if the integration is set up using config flow
        return True

    platform_config = config[DOMAIN].get(CONF_SENSORS, {})
    # If platform is not enabled, skip.
    if not platform_config:
        return False

    for entry in platform_config:
        _LOGGER.debug(
            "Setting %s(%s) from YAML configuration",
            entry[CONF_NAME],
            entry[CONF_FREQUENCY],
        )
        # If entry is not enabled, skip.
        # if not entry[CONF_ENABLED]:
        #     continue
        hass.async_create_task(
            discovery.async_load_platform(hass, SENSOR_PLATFORM, DOMAIN, entry, config)
        )
    hass.async_create_task(
        hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_IMPORT}, data={}
        )
    )
    return True


async def async_setup_entry(hass, config_entry):
    """Set up this integration using UI."""
    if config_entry.source == config_entries.SOURCE_IMPORT:
        # We get here if the integration is set up using YAML
        hass.async_create_task(hass.config_entries.async_remove(config_entry.entry_id))
        return False
    _LOGGER.debug(
        "Setting %s (%s) from ConfigFlow",
        config_entry.title,
        config_entry.data[CONF_FREQUENCY],
    )
    # Backward compatibility - clean-up (can be removed later?)
    config_entry.options = {}
    config_entry.add_update_listener(update_listener)
    # Add sensor
    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(config_entry, SENSOR_PLATFORM)
    )
    return True


async def async_remove_entry(hass, config_entry):
    """Handle removal of an entry."""
    try:
        await hass.config_entries.async_forward_entry_unload(
            config_entry, SENSOR_PLATFORM
        )
        _LOGGER.info(
            "Successfully removed sensor from the garbage_collection integration"
        )
    except ValueError:
        pass


async def update_listener(hass, entry):
    """Update listener."""
    # The OptionsFlow saves data to options.
    # Move them back to data and clean options (dirty, but not sure how else to do that)
    if len(entry.options) > 0:
        entry.data = entry.options
        entry.options = {}
    await hass.config_entries.async_forward_entry_unload(entry, SENSOR_PLATFORM)
    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(entry, SENSOR_PLATFORM)
    )
