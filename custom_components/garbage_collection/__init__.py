"""Component to integrate with garbage_colection."""

import logging
from datetime import timedelta

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import voluptuous as vol
from dateutil.relativedelta import relativedelta
from homeassistant import config_entries
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME
from homeassistant.helpers import discovery

from .const import (
    ATTR_LAST_COLLECTION,
    CONF_DATE,
    CONF_FREQUENCY,
    CONF_OFFSET,
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
        vol.Required(CONF_ENTITY_ID): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(ATTR_LAST_COLLECTION): cv.datetime,
    }
)

UPDATE_STATE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITY_ID): vol.All(cv.ensure_list, [cv.string]),
    }
)

ADD_REMOVE_DATE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITY_ID): vol.All(cv.ensure_list, [cv.string]),
        vol.Required(CONF_DATE): cv.date,
    }
)

OFFSET_DATE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITY_ID): vol.All(cv.ensure_list, [cv.string]),
        vol.Required(CONF_DATE): cv.date,
        vol.Required(CONF_OFFSET): vol.All(vol.Coerce(int), vol.Range(min=-31, max=31)),
    }
)


async def async_setup(hass, config):
    """Set up this component using YAML."""

    async def handle_add_date(call):
        """Handle the add_date service call."""
        for entity_id in call.data.get(CONF_ENTITY_ID):
            collection_date = call.data.get(CONF_DATE)
            _LOGGER.debug("called add_date %s from %s", collection_date, entity_id)
            try:
                entity = hass.data[DOMAIN][SENSOR_PLATFORM][entity_id]
                await entity.add_date(collection_date)
            except Exception as err:
                _LOGGER.error("Failed adding date for %s - %s", entity_id, err)

    async def handle_remove_date(call):
        """Handle the remove_date service call."""
        for entity_id in call.data.get(CONF_ENTITY_ID):
            collection_date = call.data.get(CONF_DATE)
            _LOGGER.debug("called remove_date %s from %s", collection_date, entity_id)
            try:
                entity = hass.data[DOMAIN][SENSOR_PLATFORM][entity_id]
                await entity.remove_date(collection_date)
            except Exception as err:
                _LOGGER.error("Failed removing date for %s - %s", entity_id, err)

    async def handle_offset_date(call):
        """Handle the offset_date service call."""
        for entity_id in call.data.get(CONF_ENTITY_ID):
            offset = call.data.get(CONF_OFFSET)
            collection_date = call.data.get(CONF_DATE)
            _LOGGER.debug(
                "called offset_date %s by %d days for %s",
                collection_date,
                offset,
                entity_id,
            )
            try:
                new_date = collection_date + relativedelta(days=offset)
            except Exception as err:
                _LOGGER.error("Failed to offset the date - %s", err)
                break
            try:
                entity = hass.data[DOMAIN][SENSOR_PLATFORM][entity_id]
                await entity.remove_date(collection_date)
                await entity.add_date(new_date)
            except Exception as err:
                _LOGGER.error("Failed ofsetting date for %s - %s", entity_id, err)

    async def handle_update_state(call):
        """Handle the update_state service call."""
        for entity_id in call.data.get(CONF_ENTITY_ID):
            _LOGGER.debug("called update_state for %s", entity_id)
            try:
                entity = hass.data[DOMAIN][SENSOR_PLATFORM][entity_id]
                await entity.async_update_state()
            except Exception as err:
                _LOGGER.error("Failed updating state for %s - %s", entity_id, err)

    async def handle_collect_garbage(call):
        """Handle the collect_garbage service call."""
        for entity_id in call.data.get(CONF_ENTITY_ID):
            last_collection = call.data.get(ATTR_LAST_COLLECTION)
            _LOGGER.debug("called collect_garbage for %s", entity_id)
            try:
                entity = hass.data[DOMAIN][SENSOR_PLATFORM][entity_id]
                if last_collection is None:
                    entity.last_collection = dt_util.now()
                else:
                    entity.last_collection = dt_util.as_local(last_collection)
                await entity.async_update_state()
            except Exception as err:
                _LOGGER.error(
                    "Failed setting last collection for %s - %s", entity_id, err
                )

    if DOMAIN not in hass.services.async_services():
        hass.services.async_register(
            DOMAIN, "collect_garbage", handle_collect_garbage, schema=COLLECT_NOW_SCHEMA
        )
        hass.services.async_register(
            DOMAIN, "update_state", handle_update_state, schema=UPDATE_STATE_SCHEMA
        )
        hass.services.async_register(
            DOMAIN, "add_date", handle_add_date, schema=ADD_REMOVE_DATE_SCHEMA
        )
        hass.services.async_register(
            DOMAIN, "remove_date", handle_remove_date, schema=ADD_REMOVE_DATE_SCHEMA
        )
        hass.services.async_register(
            DOMAIN, "offset_date", handle_offset_date, schema=OFFSET_DATE_SCHEMA
        )
    else:
        _LOGGER.debug("Services already registered")

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
