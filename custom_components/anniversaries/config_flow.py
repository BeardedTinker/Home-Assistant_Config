""" Config flow """
from collections import OrderedDict
from homeassistant.core import callback
import voluptuous as vol
from homeassistant import config_entries
from datetime import datetime
import uuid

from .const import (
    DOMAIN,
    DEFAULT_ICON_NORMAL,
    DEFAULT_ICON_SOON,
    DEFAULT_ICON_TODAY,
    DEFAULT_DATE_FORMAT,
    DEFAULT_SOON,
    DEFAULT_HALF_ANNIVERSARY,
    DEFAULT_UNIT_OF_MEASUREMENT,
    DEFAULT_ID_PREFIX,
    DEFAULT_ONE_TIME,
    CONF_ICON_NORMAL,
    CONF_ICON_TODAY,
    CONF_ICON_SOON,
    CONF_DATE,
    CONF_DATE_FORMAT,
    CONF_SOON,
    CONF_HALF_ANNIVERSARY,
    CONF_UNIT_OF_MEASUREMENT,
    CONF_ID_PREFIX,
    CONF_ONE_TIME,
)

from homeassistant.const import CONF_NAME


@config_entries.HANDLERS.register(DOMAIN)
class AnniversariesFlowHandler(config_entries.ConfigFlow):
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        self._errors = {}
        self._data = {}
        self._data["unique_id"] = str(uuid.uuid4())

    async def async_step_user(self, user_input=None):   # pylint: disable=unused-argument
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            if is_not_date(user_input[CONF_DATE], user_input[CONF_ONE_TIME]):
                self._errors["base"] = "invalid_date"
            if self._errors == {}:
                self.init_info = user_input
                return await self.async_step_icons()
        return await self._show_user_form(user_input)

    async def async_step_icons(self, user_input=None):
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title=self._data["name"], data=self._data)
        return await self._show_icon_form(user_input)

    async def _show_user_form(self, user_input):
        name = ""
        date = ""
        one_time = DEFAULT_ONE_TIME
        half_anniversary = DEFAULT_HALF_ANNIVERSARY
        date_format = DEFAULT_DATE_FORMAT
        unit_of_measurement = DEFAULT_UNIT_OF_MEASUREMENT
        id_prefix = DEFAULT_ID_PREFIX
        if user_input is not None:
            if CONF_NAME in user_input:
                name = user_input[CONF_NAME]
            if CONF_DATE in user_input:
                date = user_input[CONF_DATE]
            if CONF_ONE_TIME in user_input:
                one_time = user_input[CONF_ONE_TIME]
            if CONF_HALF_ANNIVERSARY in user_input:
                half_anniversary = user_input[CONF_HALF_ANNIVERSARY]
            if CONF_DATE_FORMAT in user_input:
                date_format = user_input[CONF_DATE_FORMAT]
            if CONF_UNIT_OF_MEASUREMENT in user_input:
                unit_of_measurement = user_input[CONF_UNIT_OF_MEASUREMENT]
            if CONF_ID_PREFIX in user_input:
                id_prefix = user_input[CONF_ID_PREFIX]
        data_schema = OrderedDict()
        data_schema[vol.Required(CONF_NAME, default=name)] = str
        data_schema[vol.Required(CONF_DATE, default=date)] = str
        data_schema[vol.Required(CONF_ONE_TIME, default=one_time)] = bool
        data_schema[vol.Required(CONF_HALF_ANNIVERSARY, default=half_anniversary)] = bool
        data_schema[vol.Required(CONF_DATE_FORMAT, default=date_format)] = str
        data_schema[vol.Required(CONF_UNIT_OF_MEASUREMENT, default=unit_of_measurement)] = str
        data_schema[vol.Optional(CONF_ID_PREFIX, default=id_prefix)] = str
        return self.async_show_form(step_id="user", data_schema=vol.Schema(data_schema), errors=self._errors)

    async def _show_icon_form(self, user_input):
        icon_normal = DEFAULT_ICON_NORMAL
        icon_today = DEFAULT_ICON_TODAY
        days_as_soon = DEFAULT_SOON
        icon_soon = DEFAULT_ICON_SOON
        if user_input is not None:
            if CONF_ICON_NORMAL in user_input:
                icon_normal = user_input[CONF_ICON_NORMAL]
            if CONF_ICON_TODAY in user_input:
                icon_today = user_input[CONF_ICON_TODAY]
            if CONF_SOON in user_input:
                days_as_soon = user_input[CONF_SOON]
            if CONF_ICON_SOON in user_input:
                icon_soon = user_input[CONF_ICON_SOON]
        data_schema = OrderedDict()
        data_schema[vol.Required(CONF_ICON_NORMAL, default=icon_normal)] = str
        data_schema[vol.Required(CONF_ICON_TODAY, default=icon_today)] = str
        data_schema[vol.Required(CONF_SOON, default=days_as_soon)] = int
        data_schema[vol.Required(CONF_ICON_SOON, default=icon_soon)] = str
        return self.async_show_form(step_id="icons", data_schema=vol.Schema(data_schema), errors=self._errors)

    async def async_step_import(self, user_input):  # pylint: disable=unused-argument
        """Import a config entry.
        Special type of import, we're not actually going to store any data.
        Instead, we're going to rely on the values that are in config file.
        """
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return self.async_create_entry(title="configuration.yaml", data={})

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        if config_entry.options.get("unique_id", None) is not None:
            return OptionsFlowHandler(config_entry)
        else:
            return EmptyOptions(config_entry)

def is_not_date(date, one_time):
    try:
        datetime.strptime(date, "%Y-%m-%d")
        return False
    except ValueError:
        if not one_time:
            pass
        else:
            return True
    try:
        datetime.strptime(date, "%m-%d")
        return False
    except ValueError:
        return True


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry
        self._data = {}
        self._data["unique_id"] = config_entry.options.get("unique_id")

    async def async_step_init(self, user_input=None):
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            if is_not_date(user_input[CONF_DATE], user_input[CONF_ONE_TIME]):
                self._errors["base"] = "invalid_date"
            if self._errors == {}:
                return await self.async_step_icons()
        return await self._show_init_form(user_input)

    async def async_step_icons(self, user_input=None):
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="", data=self._data)
        return await self._show_icon_form(user_input)

    async def _show_init_form(self, user_input):
        data_schema = OrderedDict()
        one_time = self.config_entry.options.get(CONF_ONE_TIME)
        unit_of_measurement = self.config_entry.options.get(CONF_UNIT_OF_MEASUREMENT)
        half_anniversary = self.config_entry.options.get(CONF_HALF_ANNIVERSARY)
        if one_time is None:
            one_time = DEFAULT_ONE_TIME
        if half_anniversary is None:
            half_anniversary = DEFAULT_HALF_ANNIVERSARY
        if unit_of_measurement is None:
            unit_of_measurement = DEFAULT_UNIT_OF_MEASUREMENT
        data_schema[vol.Required(CONF_NAME,default=self.config_entry.options.get(CONF_NAME),)] = str
        data_schema[vol.Required(CONF_DATE, default=self.config_entry.options.get(CONF_DATE),)] = str
        data_schema[vol.Required(CONF_ONE_TIME, default=one_time,)] = bool
        data_schema[vol.Required(CONF_HALF_ANNIVERSARY,default=half_anniversary,)] = bool
        data_schema[vol.Required(CONF_DATE_FORMAT,default=self.config_entry.options.get(CONF_DATE_FORMAT),)] = str
        data_schema[vol.Required(CONF_UNIT_OF_MEASUREMENT,default=unit_of_measurement,)] = str
        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(data_schema), errors=self._errors
        )

    async def _show_icon_form(self, user_input):
        data_schema = OrderedDict()
        data_schema[vol.Required(CONF_ICON_NORMAL,default=self.config_entry.options.get(CONF_ICON_NORMAL),)] = str
        data_schema[vol.Required(CONF_ICON_TODAY,default=self.config_entry.options.get(CONF_ICON_TODAY),)] = str
        data_schema[vol.Required(CONF_SOON,default=self.config_entry.options.get(CONF_SOON),)] = int
        data_schema[vol.Required(CONF_ICON_SOON,default=self.config_entry.options.get(CONF_ICON_SOON),)] = str
        return self.async_show_form(step_id="icons", data_schema=vol.Schema(data_schema), errors=self._errors)


class EmptyOptions(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry
