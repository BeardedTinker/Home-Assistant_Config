"""Provide the config flow."""
from homeassistant.core import callback
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
import logging
from .const import *
import os
import os.path
from homeassistant.helpers.storage import STORAGE_DIR
from ytmusicapi import YTMusic
import requests
from ytmusicapi.auth.oauth import YTMusicOAuth

import traceback
import asyncio
from collections import OrderedDict

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class yTubeMusicFlowHandler(config_entries.ConfigFlow):
	"""Provide the initial setup."""

	CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL
	VERSION = 1

	def __init__(self):
		"""Provide the init function of the config flow."""
		# Called once the flow is started by the user
		self._errors = {}

	# entry point from config start
	async def async_step_user(self, user_input=None):   # pylint: disable=unused-argument
		"""Call this as first page."""
		self._errors = {}
	
		user_input = dict()
		user_input[CONF_NAME] = DOMAIN

		session = requests.Session()
		self.oauth = YTMusicOAuth(session)
		self.code = await self.hass.async_add_executor_job(self.oauth.get_code) 
		user_input[CONF_CODE] = self.code
		return self.async_show_form(step_id="oauth", data_schema=vol.Schema(await async_create_form(self.hass,user_input,1)), errors=self._errors)

	# we get here after the user click submit on the oauth screem
	# lets check if oauth worked
	async def async_step_oauth(self, user_input=None):   # pylint: disable=unused-argument
		self._errors = {}
		try:
			self.token = await self.hass.async_add_executor_job(lambda: self.oauth.get_token_from_code(self.code["device_code"])) 
		except:
			self._errors["base"] = ERROR_GENERIC
			user_input[CONF_CODE] = self.code
			return self.async_show_form(step_id="oauth", data_schema=vol.Schema(await async_create_form(self.hass,user_input,1)), errors=self._errors)
		# if we get here then Oauth worked, right?
		user_input[CONF_HEADER_PATH] = os.path.join(self.hass.config.path(STORAGE_DIR),DEFAULT_HEADER_FILENAME)
		return self.async_show_form(step_id="finish", data_schema=vol.Schema(await async_create_form(self.hass,user_input,2)), errors=self._errors)


	# will be called by sending the form, until configuration is done
	async def async_step_finish(self,user_input=None):
		self._errors = {}
		if user_input is not None:
			self.data = user_input
			await self.hass.async_add_executor_job(lambda: self.oauth.dump_token(self.token,self.data[CONF_HEADER_PATH])) 
			if(self.data[CONF_ADVANCE_CONFIG]):
				return self.async_show_form(step_id="adv_finish", data_schema=vol.Schema(await async_create_form(self.hass,user_input,3)), errors=self._errors)
			else:
				return self.async_create_entry(title="yTubeMusic "+self.data[CONF_NAME].replace(DOMAIN,''), data=self.data)
		# we should never get below here
		return self.async_show_form(step_id="finish", data_schema=vol.Schema(await async_create_form(self.hass,user_input,2)), errors=self._errors)
	

	async def async_step_adv_finish(self,user_input=None):
		self._errors = {}
		self.data.update(user_input)
		return self.async_create_entry(title="yTubeMusic "+self.data[CONF_NAME].replace(DOMAIN,''), data=self.data)
		

	# TODO .. what is this good for?
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
		"""Call back to start the change flow."""
		return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
	"""Change an entity via GUI."""

	def __init__(self, config_entry):
		"""Set initial parameter to grab them later on."""
		# store old entry for later
		self.data = {}
		self.data.update(config_entry.data.items())

	# will be called by sending the form, until configuration is done
	async def async_step_init(self, user_input=None):   # pylint: disable=unused-argument
		"""Call this as first page."""
		self._errors = {}
		user_input = self.data
		return self.async_show_form(step_id="finish", data_schema=vol.Schema(await async_create_form(self.hass,user_input,2)), errors=self._errors)

	# will be called by sending the form, until configuration is done
	async def async_step_finish(self,user_input=None):
		self._errors = {}
		# if file name changed, we need to move the cookie
		if(self.data[CONF_HEADER_PATH]!=user_input[CONF_HEADER_PATH]):
			os.rename(self.data[CONF_HEADER_PATH],user_input[CONF_HEADER_PATH])
		self.data.update(user_input)
		if(self.data[CONF_ADVANCE_CONFIG]):
			return self.async_show_form(step_id="adv_finish", data_schema=vol.Schema(await async_create_form(self.hass,self.data,3)), errors=self._errors)
		else:
			return self.async_create_entry(title="yTubeMusic "+self.data[CONF_NAME].replace(DOMAIN,''), data=self.data)
	
	async def async_step_adv_finish(self,user_input=None):
		self._errors = {}
		self.data.update(user_input)
		return self.async_create_entry(title="yTubeMusic "+self.data[CONF_NAME].replace(DOMAIN,''), data=self.data)


async def async_create_form(hass, user_input, page=1):
	"""Create form for UI setup."""
	user_input = ensure_config(user_input)
	data_schema = OrderedDict()
	all_media_player = dict()
	all_entities = await hass.async_add_executor_job(hass.states.all) 
	for e in all_entities:
		if(e.entity_id.startswith(DOMAIN_MP) and not(e.entity_id.startswith(DOMAIN_MP+"."+DOMAIN))):
			all_media_player.update({e.entity_id: e.entity_id.replace(DOMAIN_MP+".","")})
	

	if(page == 1):
		data_schema[vol.Required(CONF_CODE+"lala", default="https://www.google.com/device?user_code="+user_input[CONF_CODE]["user_code"])] = str # name of the component without domain
		
	elif(page == 2):
		data_schema[vol.Required(CONF_NAME, default=user_input[CONF_NAME])] = str # name of the component without domain
		data_schema[vol.Required(CONF_RECEIVERS,default=user_input[CONF_RECEIVERS])] = cv.multi_select(all_media_player)
		data_schema[vol.Required(CONF_HEADER_PATH, default=user_input[CONF_HEADER_PATH])] = str # file path of the header
		data_schema[vol.Required(CONF_ADVANCE_CONFIG, default=user_input[CONF_ADVANCE_CONFIG])] = vol.Coerce(bool) # show page 2

	elif(page == 3):
		data_schema[vol.Optional(CONF_SHUFFLE, default=user_input[CONF_SHUFFLE])] = vol.Coerce(bool) # default duffle, TRUE/FALSE
		data_schema[vol.Optional(CONF_LIKE_IN_NAME, default=user_input[CONF_LIKE_IN_NAME])] = vol.Coerce(bool) # default duffle, TRUE/FALSE
		data_schema[vol.Optional(CONF_DEBUG_AS_ERROR, default=user_input[CONF_DEBUG_AS_ERROR])] = vol.Coerce(bool) # default duffle, TRUE/FALSE
		data_schema[vol.Optional(CONF_LEGACY_RADIO, default=user_input[CONF_LEGACY_RADIO])] = vol.Coerce(bool) # default radio generation typ
		data_schema[vol.Optional(CONF_SORT_BROWSER, default=user_input[CONF_SORT_BROWSER])] = vol.Coerce(bool) # sort browser results
		data_schema[vol.Optional(CONF_INIT_EXTRA_SENSOR, default=user_input[CONF_INIT_EXTRA_SENSOR])] = vol.Coerce(bool) # default radio generation typ

		data_schema[vol.Optional(CONF_TRACK_LIMIT, default=user_input[CONF_TRACK_LIMIT])] = vol.Coerce(int)
		data_schema[vol.Optional(CONF_BRAND_ID, default=user_input[CONF_BRAND_ID])] = str # brand id
		data_schema[vol.Optional(CONF_SELECT_SPEAKERS, default=user_input[CONF_SELECT_SPEAKERS])] = str # drop down to select remote_player
		data_schema[vol.Optional(CONF_SELECT_SOURCE, default=user_input[CONF_SELECT_SOURCE])] = str # drop down to select playlist / playlist-radio
		data_schema[vol.Optional(CONF_SELECT_PLAYLIST, default=user_input[CONF_SELECT_PLAYLIST])] = str # drop down that holds the playlists
		data_schema[vol.Optional(CONF_SELECT_PLAYCONTINUOUS, default=user_input[CONF_SELECT_PLAYCONTINUOUS])] = str # select of input_boolean -> continuous on/off

		data_schema[vol.Optional(CONF_PROXY_PATH, default=user_input[CONF_PROXY_PATH])] = str # select of input_boolean -> continuous on/off
		data_schema[vol.Optional(CONF_PROXY_URL, default=user_input[CONF_PROXY_URL])] = str # select of input_boolean -> continuous on/off

	return data_schema
