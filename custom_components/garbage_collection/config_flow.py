"""Adds config flow for GarbageCollection."""
import logging
import uuid
from collections import OrderedDict
from typing import Any, Dict, Optional

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import ATTR_HIDDEN, CONF_ENTITIES, CONF_NAME, WEEKDAYS
from homeassistant.core import HomeAssistant, callback

from . import const, helpers

_LOGGER = logging.getLogger(__name__)


class GarbageCollectionShared:
    """Store configuration for both YAML and config_flow."""

    def __init__(self, data):
        """Create class attributes and set initial values."""
        self._data = data.copy()
        self.hass: HomeAssistant = None
        self.name: Optional[str] = None
        self.errors: Dict = {}
        self.data_schema: OrderedDict = OrderedDict()
        self._defaults = {
            const.CONF_FREQUENCY: const.DEFAULT_FREQUENCY,
            const.CONF_ICON_NORMAL: const.DEFAULT_ICON_NORMAL,
            const.CONF_ICON_TODAY: const.DEFAULT_ICON_TODAY,
            const.CONF_ICON_TOMORROW: const.DEFAULT_ICON_TOMORROW,
            const.CONF_VERBOSE_STATE: const.DEFAULT_VERBOSE_STATE,
            ATTR_HIDDEN: False,
            const.CONF_MANUAL: False,
            const.CONF_FIRST_MONTH: const.DEFAULT_FIRST_MONTH,
            const.CONF_LAST_MONTH: const.DEFAULT_LAST_MONTH,
            const.CONF_PERIOD: const.DEFAULT_PERIOD,
            const.CONF_FIRST_WEEK: const.DEFAULT_FIRST_WEEK,
            const.CONF_VERBOSE_FORMAT: const.DEFAULT_VERBOSE_FORMAT,
            const.CONF_DATE_FORMAT: const.DEFAULT_DATE_FORMAT,
        }

    def update_data(self, user_input: Dict) -> None:
        """Remove empty fields, and fields that should not be stored in the config."""
        self._data.update(user_input)
        for key, value in user_input.items():
            if value == "":
                del self._data[key]
        if CONF_NAME in self._data:
            self.name = self._data[CONF_NAME]
            del self._data[CONF_NAME]

    def required(self, key: str, options: Optional[Dict]) -> vol.Required:
        """Return vol.Required."""
        if isinstance(options, Dict) and key in options:
            suggested_value = options[key]
        elif key in self._data:
            suggested_value = self._data[key]
        elif key in self._defaults:
            suggested_value = self._defaults[key]
        else:
            return vol.Required(key)
        return vol.Required(key, description={"suggested_value": suggested_value})

    def optional(self, key: str, options: Optional[Dict]) -> vol.Optional:
        """Return vol.Optional."""
        if isinstance(options, Dict) and key in options:
            suggested_value = options[key]
        elif key in self._data:
            suggested_value = self._data[key]
        elif key in self._defaults:
            suggested_value = self._defaults[key]
        else:
            return vol.Optional(key)
        return vol.Optional(key, description={"suggested_value": suggested_value})

    def step1_frequency(self, user_input: Dict, options: bool = False) -> bool:
        """Step 1 - choose frequency and common parameters."""
        self.errors.clear()
        if user_input is not None:
            try:
                cv.icon(
                    user_input.get(const.CONF_ICON_NORMAL, const.DEFAULT_ICON_NORMAL)
                )
                cv.icon(user_input.get(const.CONF_ICON_TODAY, const.DEFAULT_ICON_TODAY))
                cv.icon(
                    user_input.get(
                        const.CONF_ICON_TOMORROW, const.DEFAULT_ICON_TOMORROW
                    )
                )
            except vol.Invalid:
                self.errors["base"] = "icon"
            try:
                helpers.time_text(user_input.get(const.CONF_EXPIRE_AFTER))
            except vol.Invalid:
                self.errors["base"] = "time"
            if not self.errors:
                self.update_data(user_input)
                return True
        self.data_schema.clear()
        # Do not show name for Options_Flow. The name cannot be changed here
        if not options:
            self.data_schema[self.required(CONF_NAME, user_input)] = str
        self.data_schema[self.required(const.CONF_FREQUENCY, user_input)] = vol.In(
            const.FREQUENCY_OPTIONS
        )
        self.data_schema[self.optional(const.CONF_ICON_NORMAL, user_input)] = str
        self.data_schema[self.optional(const.CONF_ICON_TODAY, user_input)] = str
        self.data_schema[self.optional(const.CONF_ICON_TOMORROW, user_input)] = str
        self.data_schema[self.optional(const.CONF_EXPIRE_AFTER, user_input)] = str
        self.data_schema[self.optional(const.CONF_VERBOSE_STATE, user_input)] = bool
        self.data_schema[self.optional(ATTR_HIDDEN, user_input)] = bool
        self.data_schema[self.optional(const.CONF_MANUAL, user_input)] = bool
        return False

    def step2_detail(self, user_input: Dict) -> bool:
        """Step 2 - enter detail that depend on frequency."""
        self.errors.clear()
        # Skip second step on blank frequency
        if self._data[
            const.CONF_FREQUENCY
        ] in const.BLANK_FREQUENCY and not self._data.get(
            const.CONF_VERBOSE_STATE, False
        ):
            return True
        if user_input is not None and user_input:
            # Validation
            if user_input.get(const.CONF_FREQUENCY) in const.ANNUAL_FREQUENCY:
                # "annual"
                try:
                    helpers.month_day_text(user_input.get(const.CONF_DATE, ""))
                except vol.Invalid:
                    self.errors["base"] = "month_day"
            if user_input.get(const.CONF_FREQUENCY) in const.DAILY_FREQUENCY:
                # "every-n-days"
                try:
                    cv.date(user_input.get(const.CONF_FIRST_DATE, ""))
                except vol.Invalid:
                    self.errors["base"] = "date"
            if not self.errors:
                self.update_data(user_input)
                return True
        self.data_schema.clear()
        # Build form
        if self._data[const.CONF_FREQUENCY] in const.ANNUAL_FREQUENCY:
            # "annual"
            self.data_schema[self.required(const.CONF_DATE, user_input)] = str
        elif self._data[const.CONF_FREQUENCY] in const.GROUP_FREQUENCY:
            # "group"
            entities = self.hass.data[const.DOMAIN][const.SENSOR_PLATFORM]
            entity_ids = {
                entity: entity
                for entity in entities
                if entities[entity].unique_id != self._data["unique_id"]
            }
            self.data_schema[
                self.required(CONF_ENTITIES, user_input)
            ] = cv.multi_select(entity_ids)
        elif self._data[const.CONF_FREQUENCY] not in const.BLANK_FREQUENCY:
            # everything else except "blank" and every-n-days
            if self._data[const.CONF_FREQUENCY] not in const.DAILY_FREQUENCY:
                weekdays_dict = {weekday: weekday for weekday in WEEKDAYS}
                self.data_schema[
                    self.required(const.CONF_COLLECTION_DAYS, user_input)
                ] = cv.multi_select(weekdays_dict)
            # everything else except "blank"
            self.data_schema[
                self.optional(const.CONF_FIRST_MONTH, user_input)
            ] = vol.In(const.MONTH_OPTIONS)
            self.data_schema[self.optional(const.CONF_LAST_MONTH, user_input)] = vol.In(
                const.MONTH_OPTIONS
            )
            if self._data[const.CONF_FREQUENCY] in const.MONTHLY_FREQUENCY:
                # "monthly"
                self.data_schema[
                    self.optional(const.CONF_WEEKDAY_ORDER_NUMBER, user_input)
                ] = vol.All(
                    cv.multi_select(
                        {"1": "1st", "2": "2nd", "3": "3rd", "4": "4th", "5": "5th"}
                    ),
                )
                self.data_schema[
                    self.optional(const.CONF_FORCE_WEEK_NUMBERS, user_input)
                ] = bool
            if self._data[const.CONF_FREQUENCY] in const.WEEKLY_DAILY_MONTHLY:
                # "every-n-weeks", "every-n-days", "monthly"
                self.data_schema[
                    self.required(const.CONF_PERIOD, user_input)
                ] = vol.All(vol.Coerce(int), vol.Range(min=1, max=365))
            if self._data[const.CONF_FREQUENCY] in const.WEEKLY_FREQUENCY_X:
                # every-n-weeks
                self.data_schema[
                    self.required(const.CONF_FIRST_WEEK, user_input)
                ] = vol.All(vol.Coerce(int), vol.Range(min=1, max=52))
            if self._data[const.CONF_FREQUENCY] in const.DAILY_FREQUENCY:
                # every-n-days
                self.data_schema[self.required(const.CONF_FIRST_DATE, user_input)] = str
        if self._data.get(const.CONF_VERBOSE_STATE, False):
            # "verbose_state"
            self.data_schema[
                self.required(const.CONF_VERBOSE_FORMAT, user_input)
            ] = cv.string
            self.data_schema[
                self.required(const.CONF_DATE_FORMAT, user_input)
            ] = cv.string
        return False

    @property
    def frequency(self):
        """Return the collection frequency."""
        try:
            return self._data[const.CONF_FREQUENCY]
        except KeyError:
            return None

    @property
    def data(self):
        """Return whole data store."""
        return self._data


@config_entries.HANDLERS.register(const.DOMAIN)
class GarbageCollectionFlowHandler(config_entries.ConfigFlow):
    """Config flow for garbage_collection."""

    VERSION = const.VERSION
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize."""
        self.shared_class = GarbageCollectionShared({"unique_id": str(uuid.uuid4())})

    async def async_step_user(
        self, user_input: Dict = {}
    ):  # pylint: disable=dangerous-default-value
        """Step 1 - set general parameters."""
        next_step = self.shared_class.step1_frequency(user_input)
        if next_step:
            return await self.async_step_detail()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                self.shared_class.data_schema, extra=vol.ALLOW_EXTRA
            ),
            errors=self.shared_class.errors,
        )

    async def async_step_detail(
        self, user_input: Dict = {}
    ):  # pylint: disable=dangerous-default-value
        """Step 2 - enter detail depending on frequency."""
        self.shared_class.hass = self.hass
        next_step = self.shared_class.step2_detail(user_input)
        if next_step:
            return self.async_create_entry(
                title=self.shared_class.name, data=self.shared_class.data
            )
        return self.async_show_form(
            step_id="detail",
            data_schema=vol.Schema(
                self.shared_class.data_schema, extra=vol.ALLOW_EXTRA
            ),
            errors=self.shared_class.errors,
        )

    async def async_step_import(
        self, user_input: Dict
    ):  # pylint: disable=unused-argument
        """Import config from configuration.yaml."""
        _LOGGER.info("Importing config for %s", user_input)
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
        removed_data: Dict[str, Any] = {}
        for remove in to_remove:
            if remove in user_input:
                removed_data[remove] = user_input[remove]
                del user_input[remove]
        if user_input.get(const.CONF_FREQUENCY) in const.MONTHLY_FREQUENCY:
            if const.CONF_WEEK_ORDER_NUMBER in user_input:
                user_input[const.CONF_WEEKDAY_ORDER_NUMBER] = list(
                    map(str, user_input[const.CONF_WEEK_ORDER_NUMBER])
                )
                user_input[const.CONF_FORCE_WEEK_NUMBERS] = True
                del user_input[const.CONF_WEEK_ORDER_NUMBER]
                _LOGGER.debug("Updated data config for week_order_number")
            else:
                user_input[const.CONF_WEEKDAY_ORDER_NUMBER] = list(
                    map(str, user_input[const.CONF_WEEKDAY_ORDER_NUMBER])
                )
                user_input[const.CONF_FORCE_WEEK_NUMBERS] = False
        if removed_data:
            _LOGGER.error(
                "Removed obsolete config values: %s. "
                "Please check the documentation how to configure the functionality.",
                removed_data,
            )
        self.shared_class.update_data(user_input)
        return self.async_create_entry(
            title=self.shared_class.name, data=self.shared_class.data
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Return options flow handler, or empty options flow if no unique_id."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Options flow handler."""

    def __init__(self, config_entry):
        """Create and initualize class variables."""
        self.shared_class = GarbageCollectionShared(config_entry.data)

    async def async_step_init(self, user_input: Optional[Dict] = None):
        """Set genral parameters."""
        next_step = self.shared_class.step1_frequency(user_input, options=True)
        if next_step:
            return await self.async_step_detail()
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(self.shared_class.data_schema),
            errors=self.shared_class.errors,
        )

    async def async_step_detail(
        self, user_input: Dict = {}
    ):  # pylint: disable=dangerous-default-value
        """Step 2 - annual or group (no week days)."""
        self.shared_class.hass = self.hass
        next_step = self.shared_class.step2_detail(user_input)
        if next_step:
            return self.async_create_entry(title="", data=self.shared_class.data)
        return self.async_show_form(
            step_id="detail",
            data_schema=vol.Schema(self.shared_class.data_schema),
            errors=self.shared_class.errors,
        )
