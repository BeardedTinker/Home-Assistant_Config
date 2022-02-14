"""Component to integrate with garbage_colection."""

import logging
from datetime import timedelta
from typing import Any, Dict

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import voluptuous as vol
from dateutil.relativedelta import relativedelta
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    ATTR_HIDDEN,
    CONF_ENTITIES,
    CONF_ENTITY_ID,
    CONF_NAME,
    WEEKDAYS,
)
from homeassistant.core import Config, HomeAssistant, ServiceCall

from . import const

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)

SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(const.CONF_FREQUENCY): vol.In(const.FREQUENCY_OPTIONS),
        vol.Optional(const.CONF_ICON_NORMAL): cv.icon,
        vol.Optional(const.CONF_ICON_TODAY): cv.icon,
        vol.Optional(const.CONF_ICON_TOMORROW): cv.icon,
        vol.Optional(const.CONF_EXPIRE_AFTER): const.time_text,
        vol.Optional(const.CONF_VERBOSE_STATE): cv.boolean,
        vol.Optional(ATTR_HIDDEN): cv.boolean,
        vol.Optional(const.CONF_MANUAL): cv.boolean,
        vol.Optional(const.CONF_DATE): const.month_day_text,
        vol.Optional(CONF_ENTITIES): cv.entity_ids,
        vol.Optional(const.CONF_COLLECTION_DAYS): vol.All(
            cv.ensure_list, [vol.In(WEEKDAYS)]
        ),
        vol.Optional(const.CONF_FIRST_MONTH): vol.In(const.MONTH_OPTIONS),
        vol.Optional(const.CONF_LAST_MONTH): vol.In(const.MONTH_OPTIONS),
        vol.Optional(const.CONF_WEEKDAY_ORDER_NUMBER): vol.All(
            cv.ensure_list, [vol.All(vol.Coerce(int), vol.Range(min=1, max=5))]
        ),
        vol.Optional(const.CONF_WEEK_ORDER_NUMBER): vol.All(
            cv.ensure_list, [vol.All(vol.Coerce(int), vol.Range(min=1, max=5))]
        ),
        vol.Optional(const.CONF_PERIOD): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=365)
        ),
        vol.Optional(const.CONF_FIRST_WEEK): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=52)
        ),
        vol.Optional(const.CONF_FIRST_DATE): cv.date,
        vol.Optional(const.CONF_VERBOSE_FORMAT): cv.string,
        vol.Optional(const.CONF_DATE_FORMAT): cv.string,
    },
    extra=vol.ALLOW_EXTRA,
)

CONFIG_SCHEMA = vol.Schema(
    {
        const.DOMAIN: vol.Schema(
            {vol.Optional(const.CONF_SENSORS): vol.All(cv.ensure_list, [SENSOR_SCHEMA])}
        )
    },
    extra=vol.ALLOW_EXTRA,
)

COLLECT_NOW_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITY_ID): vol.All(cv.ensure_list, [cv.string]),
        vol.Optional(const.ATTR_LAST_COLLECTION): cv.datetime,
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
        vol.Required(const.CONF_DATE): cv.date,
    }
)

OFFSET_DATE_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_ENTITY_ID): vol.All(cv.ensure_list, [cv.string]),
        vol.Required(const.CONF_DATE): cv.date,
        vol.Required(const.CONF_OFFSET): vol.All(
            vol.Coerce(int), vol.Range(min=-31, max=31)
        ),
    }
)


async def async_setup(hass: HomeAssistant, config: Config) -> bool:
    """Set up this component using YAML."""

    async def handle_add_date(call: ServiceCall) -> None:
        """Handle the add_date service call."""
        for entity_id in call.data.get(CONF_ENTITY_ID):
            collection_date = call.data.get(const.CONF_DATE)
            _LOGGER.debug("called add_date %s from %s", collection_date, entity_id)
            try:
                entity = hass.data[const.DOMAIN][const.SENSOR_PLATFORM][entity_id]
                await entity.add_date(collection_date)
            except KeyError as err:
                _LOGGER.error("Failed adding date for %s - %s", entity_id, err)

    async def handle_remove_date(call: ServiceCall) -> None:
        """Handle the remove_date service call."""
        for entity_id in call.data.get(CONF_ENTITY_ID):
            collection_date = call.data.get(const.CONF_DATE)
            _LOGGER.debug("called remove_date %s from %s", collection_date, entity_id)
            try:
                entity = hass.data[const.DOMAIN][const.SENSOR_PLATFORM][entity_id]
                await entity.remove_date(collection_date)
            except KeyError as err:
                _LOGGER.error("Failed removing date for %s - %s", entity_id, err)

    async def handle_offset_date(call: ServiceCall) -> None:
        """Handle the offset_date service call."""
        for entity_id in call.data.get(CONF_ENTITY_ID):
            offset = call.data.get(const.CONF_OFFSET)
            collection_date = call.data.get(const.CONF_DATE)
            _LOGGER.debug(
                "called offset_date %s by %d days for %s",
                collection_date,
                offset,
                entity_id,
            )
            try:
                new_date = collection_date + relativedelta(days=offset)
            except TypeError as err:
                _LOGGER.error("Failed to offset the date - %s", err)
                break
            try:
                entity = hass.data[const.DOMAIN][const.SENSOR_PLATFORM][entity_id]
                await entity.remove_date(collection_date)
                await entity.add_date(new_date)
            except KeyError as err:
                _LOGGER.error("Failed ofsetting date for %s - %s", entity_id, err)

    async def handle_update_state(call: ServiceCall) -> None:
        """Handle the update_state service call."""
        for entity_id in call.data.get(CONF_ENTITY_ID):
            _LOGGER.debug("called update_state for %s", entity_id)
            try:
                entity = hass.data[const.DOMAIN][const.SENSOR_PLATFORM][entity_id]
                await entity.async_update_state()
            except KeyError as err:
                _LOGGER.error("Failed updating state for %s - %s", entity_id, err)

    async def handle_collect_garbage(call: ServiceCall) -> None:
        """Handle the collect_garbage service call."""
        for entity_id in call.data.get(CONF_ENTITY_ID):
            last_collection = call.data.get(const.ATTR_LAST_COLLECTION)
            _LOGGER.debug("called collect_garbage for %s", entity_id)
            try:
                entity = hass.data[const.DOMAIN][const.SENSOR_PLATFORM][entity_id]
                if last_collection is None:
                    entity.last_collection = dt_util.now()
                else:
                    entity.last_collection = dt_util.as_local(last_collection)
                await entity.async_update_state()
            except KeyError as err:
                _LOGGER.error(
                    "Failed setting last collection for %s - %s", entity_id, err
                )

    if const.DOMAIN not in hass.services.async_services():
        hass.services.async_register(
            const.DOMAIN,
            "collect_garbage",
            handle_collect_garbage,
            schema=COLLECT_NOW_SCHEMA,
        )
        hass.services.async_register(
            const.DOMAIN,
            "update_state",
            handle_update_state,
            schema=UPDATE_STATE_SCHEMA,
        )
        hass.services.async_register(
            const.DOMAIN, "add_date", handle_add_date, schema=ADD_REMOVE_DATE_SCHEMA
        )
        hass.services.async_register(
            const.DOMAIN,
            "remove_date",
            handle_remove_date,
            schema=ADD_REMOVE_DATE_SCHEMA,
        )
        hass.services.async_register(
            const.DOMAIN, "offset_date", handle_offset_date, schema=OFFSET_DATE_SCHEMA
        )
    else:
        _LOGGER.debug("Services already registered")

    if config.get(const.DOMAIN) is None:
        # We get here if the integration is set up using config flow
        return True

    platform_config = config[const.DOMAIN].get(const.CONF_SENSORS, {})
    # If platform is not enabled, skip.
    if not platform_config:
        return False

    for entry in hass.config_entries.async_entries(const.DOMAIN):
        if entry.source == SOURCE_IMPORT:
            _LOGGER.error(
                "garbage_collection already imported. "
                "Remove it from configuration.yaml now!"
            )
            return True
    for entry in platform_config:
        _LOGGER.debug(
            "Importing %s(%s) from YAML configuration",
            entry[CONF_NAME],
            entry[const.CONF_FREQUENCY],
        )
        # Import YAML to ConfigFlow
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                const.DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=entry,
            )
        )
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    _LOGGER.debug(
        "Setting %s (%s) from ConfigFlow",
        config_entry.title,
        config_entry.data[const.CONF_FREQUENCY],
    )
    # Backward compatibility - clean-up (can be removed later?)
    config_entry.options = {}
    config_entry.add_update_listener(update_listener)
    # Add sensor
    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(
            config_entry, const.SENSOR_PLATFORM
        )
    )
    return True


async def async_remove_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> None:
    """Handle removal of an entry."""
    try:
        await hass.config_entries.async_forward_entry_unload(
            config_entry, const.SENSOR_PLATFORM
        )
        _LOGGER.info(
            "Successfully removed sensor from the garbage_collection integration"
        )
    except ValueError:
        pass


async def async_migrate_entry(_, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.info(
        "Migrating %s from version %s", config_entry.title, config_entry.version
    )
    new_data = {**config_entry.data}
    new_options = {**config_entry.options}
    removed_data: Dict[str, Any] = {}
    removed_options: Dict[str, Any] = {}
    _LOGGER.debug("new_data %s", new_data)
    _LOGGER.debug("new_options %s", new_options)
    if config_entry.version == 1:
        to_remove = [
            "offset",
            "move_country_holidays",
            "holiday_in_week_move",
            "holiday_pop_named",
            "holiday_move_offset",
            "prov",
            "state",
            "observed",
            "exclude_dates",
            "include_dates",
        ]
        for remove in to_remove:
            if remove in new_data:
                removed_data[remove] = new_data[remove]
                del new_data[remove]
            if remove in new_options:
                removed_options[remove] = new_options[remove]
                del new_options[remove]
        if new_data.get(const.CONF_FREQUENCY) in const.MONTHLY_FREQUENCY:
            if const.CONF_WEEK_ORDER_NUMBER in new_data:
                new_data[const.CONF_WEEKDAY_ORDER_NUMBER] = new_data[
                    const.CONF_WEEK_ORDER_NUMBER
                ]
                new_data[const.CONF_FORCE_WEEK_NUMBERS] = True
                del new_data[const.CONF_WEEK_ORDER_NUMBER]
            else:
                new_data[const.CONF_FORCE_WEEK_NUMBERS] = False
            _LOGGER.info("Updated data config for week_order_number")
        if new_options.get(const.CONF_FREQUENCY) in const.MONTHLY_FREQUENCY:
            if const.CONF_WEEK_ORDER_NUMBER in new_options:
                new_options[const.CONF_WEEKDAY_ORDER_NUMBER] = new_options[
                    const.CONF_WEEK_ORDER_NUMBER
                ]
                new_options[const.CONF_FORCE_WEEK_NUMBERS] = True
                del new_options[const.CONF_WEEK_ORDER_NUMBER]
                _LOGGER.info("Updated options config for week_order_number")
            else:
                new_options[const.CONF_FORCE_WEEK_NUMBERS] = False
    config_entry.version = const.VERSION
    config_entry.data = {**new_data}
    config_entry.options = {**new_options}
    if removed_data:
        _LOGGER.error(
            "Removed data config %s. "
            "Please check the documentation how to configure the functionality.",
            removed_data,
        )
    if removed_options:
        _LOGGER.error(
            "Removed options config %s. "
            "Please check the documentation how to configure the functionality.",
            removed_options,
        )
    _LOGGER.info(
        "%s migration to version %s successful",
        config_entry.title,
        config_entry.version,
    )
    return True


async def update_listener(hass, entry):
    """Update listener."""
    # The OptionsFlow saves data to options.
    # Move them back to data and clean options (dirty, but not sure how else to do that)
    if len(entry.options) > 0:
        entry.data = entry.options
        entry.options = {}
    await hass.config_entries.async_forward_entry_unload(entry, const.SENSOR_PLATFORM)
    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(entry, const.SENSOR_PLATFORM)
    )
