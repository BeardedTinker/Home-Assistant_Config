"""Component to integrate with garbage_colection."""
from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from types import MappingProxyType
from typing import Any, Dict

import homeassistant.helpers.config_validation as cv
import homeassistant.util.dt as dt_util
import voluptuous as vol
from dateutil.relativedelta import relativedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_HIDDEN, CONF_ENTITIES, CONF_ENTITY_ID, WEEKDAYS
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.typing import ConfigType

from . import const, helpers

MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)

_LOGGER = logging.getLogger(__name__)

months = [m["value"] for m in const.MONTH_OPTIONS]
frequencies = [f["value"] for f in const.FREQUENCY_OPTIONS]

SENSOR_SCHEMA = vol.Schema(
    {
        vol.Required(const.CONF_FREQUENCY): vol.In(frequencies),
        vol.Optional(const.CONF_ICON_NORMAL): cv.icon,
        vol.Optional(const.CONF_ICON_TODAY): cv.icon,
        vol.Optional(const.CONF_ICON_TOMORROW): cv.icon,
        vol.Optional(const.CONF_EXPIRE_AFTER): helpers.time_text,
        vol.Optional(const.CONF_VERBOSE_STATE): cv.boolean,
        vol.Optional(ATTR_HIDDEN): cv.boolean,
        vol.Optional(const.CONF_MANUAL): cv.boolean,
        vol.Optional(const.CONF_DATE): helpers.month_day_text,
        vol.Optional(CONF_ENTITIES): cv.entity_ids,
        vol.Optional(const.CONF_COLLECTION_DAYS): vol.All(
            cv.ensure_list, [vol.In(WEEKDAYS)]
        ),
        vol.Optional(const.CONF_FIRST_MONTH): vol.In(months),
        vol.Optional(const.CONF_LAST_MONTH): vol.In(months),
        vol.Optional(const.CONF_WEEKDAY_ORDER_NUMBER): vol.All(
            cv.ensure_list, [vol.All(vol.Coerce(int), vol.Range(min=1, max=5))]
        ),
        vol.Optional(const.CONF_WEEK_ORDER_NUMBER): vol.All(
            cv.ensure_list, [vol.All(vol.Coerce(int), vol.Range(min=1, max=5))]
        ),
        vol.Optional(const.CONF_PERIOD): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=1000)
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


async def async_setup(hass: HomeAssistant, _: ConfigType) -> bool:
    """Set up platform - register services, inicialize data structure."""

    async def handle_add_date(call: ServiceCall) -> None:
        """Handle the add_date service call."""
        entity_ids = call.data.get(CONF_ENTITY_ID, [])
        collection_date = call.data.get(const.CONF_DATE)
        for entity_id in entity_ids:
            _LOGGER.debug("called add_date %s from %s", collection_date, entity_id)
            try:
                entity = hass.data[const.DOMAIN][const.SENSOR_PLATFORM][entity_id]
                await entity.add_date(collection_date)
            except KeyError as err:
                _LOGGER.error(
                    "Failed adding date %s to %s (%s)",
                    collection_date,
                    entity_id,
                    err,
                )

    async def handle_remove_date(call: ServiceCall) -> None:
        """Handle the remove_date service call."""
        entity_ids = call.data.get(CONF_ENTITY_ID, [])
        collection_date = call.data.get(const.CONF_DATE)
        for entity_id in entity_ids:
            _LOGGER.debug("called remove_date %s from %s", collection_date, entity_id)
            try:
                entity = hass.data[const.DOMAIN][const.SENSOR_PLATFORM][entity_id]
                await entity.remove_date(collection_date)
            except KeyError as err:
                _LOGGER.error(
                    "Failed removing date %s from %s (%s)",
                    collection_date,
                    entity_id,
                    err,
                )

    async def handle_offset_date(call: ServiceCall) -> None:
        """Handle the offset_date service call."""
        entity_ids = call.data.get(CONF_ENTITY_ID, [])
        offset = call.data.get(const.CONF_OFFSET)
        collection_date = call.data.get(const.CONF_DATE)
        for entity_id in entity_ids:
            _LOGGER.debug(
                "called offset_date %s by %d days for %s",
                collection_date,
                offset,
                entity_id,
            )
            try:
                new_date = collection_date + relativedelta(
                    days=offset
                )  # pyright: reportOptionalOperand=false
                entity = hass.data[const.DOMAIN][const.SENSOR_PLATFORM][entity_id]
                await asyncio.gather(
                    entity.remove_date(collection_date), entity.add_date(new_date)
                )
            except (TypeError, KeyError) as err:
                _LOGGER.error("Failed ofsetting date for %s - %s", entity_id, err)
                break

    async def handle_update_state(call: ServiceCall) -> None:
        """Handle the update_state service call."""
        entity_ids = call.data.get(CONF_ENTITY_ID, [])
        for entity_id in entity_ids:
            _LOGGER.debug("called update_state for %s", entity_id)
            try:
                entity = hass.data[const.DOMAIN][const.SENSOR_PLATFORM][entity_id]
                entity.update_state()
            except KeyError as err:
                _LOGGER.error("Failed updating state for %s - %s", entity_id, err)

    async def handle_collect_garbage(call: ServiceCall) -> None:
        """Handle the collect_garbage service call."""
        entity_ids = call.data.get(CONF_ENTITY_ID, [])
        last_collection = call.data.get(const.ATTR_LAST_COLLECTION, helpers.now())
        for entity_id in entity_ids:
            _LOGGER.debug("called collect_garbage for %s", entity_id)
            try:
                entity = hass.data[const.DOMAIN][const.SENSOR_PLATFORM][entity_id]
                entity.last_collection = dt_util.as_local(last_collection)
                entity.update_state()
            except KeyError as err:
                _LOGGER.error(
                    "Failed setting last collection for %s - %s", entity_id, err
                )

    hass.data.setdefault(const.DOMAIN, {})
    hass.data[const.DOMAIN].setdefault(const.SENSOR_PLATFORM, {})
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
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Set up this integration using UI."""
    _LOGGER.debug(
        "Setting %s (%s) from ConfigFlow",
        config_entry.title,
        config_entry.options[const.CONF_FREQUENCY],
    )
    config_entry.add_update_listener(update_listener)
    # Add sensor
    hass.async_create_task(
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


async def async_migrate_entry(_: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.info(
        "Migrating %s from version %s", config_entry.title, config_entry.version
    )
    new_data: Dict[str, Any] = {**config_entry.data}
    new_options: Dict[str, Any] = {**config_entry.options}
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
    if config_entry.version <= 4:
        if const.CONF_WEEKDAY_ORDER_NUMBER in new_data:
            new_data[const.CONF_WEEKDAY_ORDER_NUMBER] = list(
                map(str, new_data[const.CONF_WEEKDAY_ORDER_NUMBER])
            )
        if const.CONF_WEEKDAY_ORDER_NUMBER in new_options:
            new_options[const.CONF_WEEKDAY_ORDER_NUMBER] = list(
                map(str, new_options[const.CONF_WEEKDAY_ORDER_NUMBER])
            )
    if config_entry.version <= 5:
        for conf in [
            const.CONF_FREQUENCY,
            const.CONF_ICON_NORMAL,
            const.CONF_ICON_TODAY,
            const.CONF_ICON_TOMORROW,
            const.CONF_MANUAL,
            const.CONF_OFFSET,
            const.CONF_EXPIRE_AFTER,
            const.CONF_VERBOSE_STATE,
            const.CONF_FIRST_MONTH,
            const.CONF_LAST_MONTH,
            const.CONF_COLLECTION_DAYS,
            const.CONF_WEEKDAY_ORDER_NUMBER,
            const.CONF_FORCE_WEEK_NUMBERS,
            const.CONF_WEEK_ORDER_NUMBER,
            const.CONF_DATE,
            const.CONF_PERIOD,
            const.CONF_FIRST_WEEK,
            const.CONF_FIRST_DATE,
            const.CONF_SENSORS,
            const.CONF_VERBOSE_FORMAT,
            const.CONF_DATE_FORMAT,
        ]:
            if conf in new_data:
                new_options[conf] = new_data.get(conf)
                del new_data[conf]
        if (
            const.CONF_EXPIRE_AFTER in new_options
            and len(new_options[const.CONF_EXPIRE_AFTER]) == 5
        ):
            new_options[const.CONF_EXPIRE_AFTER] = (
                new_options[const.CONF_EXPIRE_AFTER] + ":00"
            )
    config_entry.version = const.CONFIG_VERSION
    config_entry.data = MappingProxyType({**new_data})
    config_entry.options = MappingProxyType({**new_options})
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


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener - to re-create device after options update."""
    await hass.config_entries.async_forward_entry_unload(entry, const.SENSOR_PLATFORM)
    hass.async_add_job(
        hass.config_entries.async_forward_entry_setup(entry, const.SENSOR_PLATFORM)
    )
