""" config flow """
import logging
import uuid

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant, callback

from collections import OrderedDict

from .const import (
    DOMAIN,
    DEFAULT_ICON_NORMAL,
    DEFAULT_ICON_SOON,
    DEFAULT_ICON_TODAY,
    DEFAULT_DATE_FORMAT,
    DEFAULT_SOON,
    CONF_ICON_NORMAL,
    CONF_ICON_TODAY,
    CONF_ICON_SOON,
    CONF_HOLIDAY,
    CONF_DATE_FORMAT,
    CONF_SOON,
)

from . import holiday_list

_LOGGER = logging.getLogger(__name__)

@callback
def calendarific_entries(hass: HomeAssistant):
    return set(
        (entry.data)
        for entry in hass.config_entries.async_entries(DOMAIN)
    )

class CalendarificConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    "handle config flow"
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    def __init__(self) -> None:
        self._errors = {}
        self._data = {}
        self._data["unique_id"] = str(uuid.uuid4())

    async def async_step_user(self, user_input=None):
        if holiday_list == []:
            return self.async_abort(reason="no_holidays_found")
        self._errors = {}
        if user_input is not None:
            self._data.update(user_input)
            if self._errors == {}:
                if self._data["name"] == "":
                    self._data["name"] = self._data["holiday"]
                return self.async_create_entry(title=self._data["name"], data=self._data)
        return await self._show_user_form(user_input)

    async def _show_user_form(self, user_input):
        name = ""
        holiday = ""
        icon_normal = DEFAULT_ICON_NORMAL
        icon_soon = DEFAULT_ICON_SOON
        icon_today = DEFAULT_ICON_TODAY
        date_format = DEFAULT_DATE_FORMAT
        days_as_soon = DEFAULT_SOON
        if user_input is not None:
            if CONF_NAME in user_input:
                name = user_input[CONF_NAME]
            if CONF_HOLIDAY in user_input:
                holiday = user_input[CONF_HOLIDAY]
            if CONF_ICON_NORMAL in user_input:
                icon_normal = user_input[CONF_ICON_NORMAL]
            if CONF_ICON_SOON in user_input:
                icon_soon = user_input[CONF_ICON_SOON]
            if CONF_ICON_TODAY in user_input:
                icon_today = user_input[CONF_ICON_TODAY]
            if CONF_DATE_FORMAT in user_input:
                date_format = user_input[CONF_DATE_FORMAT]
        data_schema = OrderedDict()
        data_schema[vol.Required(CONF_HOLIDAY, default=holiday)] = vol.In(holiday_list) 
        data_schema[vol.Optional(CONF_NAME, default=name)] = str
        data_schema[vol.Required(CONF_ICON_NORMAL, default=icon_normal)] = str
        data_schema[vol.Required(CONF_ICON_TODAY, default=icon_today)] = str
        data_schema[vol.Required(CONF_SOON, default=days_as_soon)] = int
        data_schema[vol.Required(CONF_ICON_SOON, default=icon_soon)] = str
        data_schema[vol.Required(CONF_DATE_FORMAT, default=date_format)] = str
        return self.async_show_form(step_id="user", data_schema=vol.Schema(data_schema), errors=self._errors)

    async def async_step_import(self, user_input=None):
        """Import a config entry.
        Special type of import, we're not actually going to store any data.
        Instead, we're going to rely on the values that are in config file.
        """
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")
        return await self.async_step_user(user_input)
