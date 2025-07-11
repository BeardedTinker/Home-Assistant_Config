"""Provide the config flow."""
from homeassistant.core import callback
from homeassistant import config_entries
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.selector import selector
import voluptuous as vol
import logging
from .const import *
import os
import os.path
from homeassistant.helpers.storage import STORAGE_DIR
import ytmusicapi
from ytmusicapi.helpers import SUPPORTED_LANGUAGES
from ytmusicapi.auth.oauth import OAuthCredentials, RefreshingToken
import requests

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
		return await async_common_step_user(self,user_input)
		

	async def async_step_oauth(self, user_input=None):   # pylint: disable=unused-argument
		return await async_common_step_oauth(self, user_input)

	# we get here after the user click submit on the oauth screem
	# lets check if oauth worked
	async def async_step_oauth2(self, user_input=None):   # pylint: disable=unused-argument
		return await async_common_step_oauth2(self, user_input)
		
	# we get here after the user click submit on the oauth screem
	# lets check if oauth worked
	async def async_step_oauth3(self, user_input=None):   # pylint: disable=unused-argument
		return await async_common_step_oauth3(self, user_input)  # pylint: disable=unused-argument
		
	# will be called by sending the form, until configuration is done
	async def async_step_finish(self,user_input=None):
		return await async_common_step_finish(self, user_input)
	

	async def async_step_adv_finish(self,user_input=None):
		return await async_common_step_adv_finish(self, user_input)
		

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
		self.data = dict(config_entry.options or config_entry.data)
		self.data[CONF_HEADER_PATH+"_old"] = self.data[CONF_HEADER_PATH]
		self.data[CONF_RENEW_OAUTH] = False


	# will be called by sending the form, until configuration is done
	async def async_step_init(self, user_input=None):   # pylint: disable=unused-argument
		"""Call this as first page."""
		user_input = self.data
		return await async_common_step_user(self,user_input, option_flow = True)
	
	async def async_step_oauth(self, user_input=None):   # pylint: disable=unused-argument
		return await async_common_step_oauth(self, user_input, option_flow = True)

	# we get here after the user click submit on the oauth screem
	# lets check if oauth worked
	async def async_step_oauth2(self, user_input=None):   # pylint: disable=unused-argument
		return await async_common_step_oauth2(self, user_input, option_flow = True)
		
	# we get here after the user click submit on the oauth screem
	# lets check if oauth worked
	async def async_step_oauth3(self, user_input=None):   # pylint: disable=unused-argument
		return await async_common_step_oauth3(self, user_input, option_flow = True)  # pylint: disable=unused-argument
		
	# will be called by sending the form, until configuration is done
	async def async_step_finish(self,user_input=None):
		return await async_common_step_finish(self, user_input, option_flow = True)
	

	async def async_step_adv_finish(self,user_input=None):
		return await async_common_step_adv_finish(self, user_input, option_flow = True)
	

async def async_common_step_user(self, user_input=None, option_flow = False):
	self._errors = {}
	#_LOGGER.error("step user was just called")
	"""Call this as first page."""
	if(user_input == None):
		user_input = dict()
		user_input[CONF_NAME] = DOMAIN
	self.data = user_input
	return self.async_show_form(step_id="oauth", data_schema=vol.Schema(await async_create_form(self.hass,user_input,0, option_flow)), errors=self._errors)


async def async_common_step_oauth(self, user_input=None, option_flow = False):   # pylint: disable=unused-argument
	# we should have received the entity ID
	# now we show the form to enter the oauth user credentials
	self._errors = {}
	#_LOGGER.error("step oauth was just called")
	if user_input is not None:
		self.data.update(user_input)
		if CONF_NAME in user_input:
			self.data[CONF_NAME] = user_input[CONF_NAME].replace(DOMAIN_MP+".","") # make sure to erase "media_player.bla" -> bla

		# skip the complete oauth cycle if unchecked (default)
		if CONF_RENEW_OAUTH in user_input:
			if not(user_input[CONF_RENEW_OAUTH]):
				return self.async_show_form(step_id="finish", data_schema=vol.Schema(await async_create_form(self.hass,self.data,3, option_flow)), errors=self._errors)
			
	return self.async_show_form(step_id="oauth2", data_schema=vol.Schema(await async_create_form(self.hass,user_input,1, option_flow)), errors=self._errors)


async def async_common_step_oauth2(self, user_input=None, option_flow = False):   # pylint: disable=unused-argument
	self._errors = {}
	#_LOGGER.error("step oauth2 was just called")
	if user_input is not None:
		self.data.update(user_input)
#		OAUTH		
	self.data[CONF_HEADER_PATH] = os.path.join(self.hass.config.path(STORAGE_DIR),DEFAULT_HEADER_FILENAME+self.data[CONF_NAME].replace(' ','_')+'.json')
	try:
		self.oauth = await self.hass.async_add_executor_job(lambda: OAuthCredentials(self.data[CONF_CLIENT_ID], self.data[CONF_CLIENT_SECRET], None, None)) 
		self.code = await self.hass.async_add_executor_job(self.oauth.get_code) 
		self.data[CONF_CODE] = self.code
	except:
		self._errors["base"] = ERROR_OAUTH
		return self.async_show_form(step_id="oauth2", data_schema=vol.Schema(await async_create_form(self.hass,self.data,1, option_flow)), errors=self._errors)

#		OAUTH
	return self.async_show_form(step_id="oauth3", data_schema=vol.Schema(await async_create_form(self.hass,self.data,2, option_flow)), errors=self._errors)

async def async_common_step_oauth3(self, user_input=None, option_flow = False):   # pylint: disable=unused-argument
	self._errors = {}
	#_LOGGER.error("step oauth3 was just called")
	self.data.update(user_input)
	
	store_token = True
	if CONF_RENEW_OAUTH in self.data:
		if not(self.data[CONF_RENEW_OAUTH]):
			store_token = False

	if store_token:
		try:
			self.token = await self.hass.async_add_executor_job(lambda: self.oauth.token_from_code(self.code["device_code"])) 
			self.refresh_token = RefreshingToken(credentials=self.oauth, **self.token)
			self.refresh_token.update(self.refresh_token.as_dict())
		except:
			self._errors["base"] = ERROR_AUTH_USER
			user_input = self.data
			return self.async_show_form(step_id="oauth3", data_schema=vol.Schema(await async_create_form(self.hass,self.data,2, option_flow)), errors=self._errors)
#		OAUTH	
	return self.async_show_form(step_id="finish", data_schema=vol.Schema(await async_create_form(self.hass,self.data,3, option_flow)), errors=self._errors)


async def async_common_step_finish(self,user_input=None, option_flow = False):
	self._errors = {}
	#_LOGGER.error("step finish was just called")
	self.data.update(user_input)
	store_token = True
	if CONF_RENEW_OAUTH in self.data:
		if not(self.data[CONF_RENEW_OAUTH]):
			store_token = False
	
	if store_token:
		await self.hass.async_add_executor_job(lambda: self.refresh_token.store_token(self.data[CONF_HEADER_PATH]))
	elif self.data[CONF_HEADER_PATH] != self.data[CONF_HEADER_PATH+"_old"]:
		#_LOGGER.error("moving cookie to "+self.data[CONF_HEADER_PATH])
		if os.path.exists(self.data[CONF_HEADER_PATH+"_old"]):
			os.rename(self.data[CONF_HEADER_PATH+"_old"],self.data[CONF_HEADER_PATH])

		
	if(self.data[CONF_ADVANCE_CONFIG]):
		return self.async_show_form(step_id="adv_finish", data_schema=vol.Schema(await async_create_form(self.hass,self.data,4, option_flow)), errors=self._errors)
	elif option_flow:
		return self.async_create_entry(data = self.data)
	else:
		return self.async_create_entry(title="yTubeMusic "+self.data[CONF_NAME].replace(DOMAIN,''), data=self.data)
	

async def async_common_step_adv_finish(self,user_input=None, option_flow = False):
	self._errors = {}
	#_LOGGER.error("step adv finish was just called")
	self.data.update(user_input)
	if option_flow:
		return self.async_create_entry(data = self.data)
	else:
		return self.async_create_entry(title="yTubeMusic "+self.data[CONF_NAME].replace(DOMAIN,''), data=self.data)

	
async def async_create_form(hass, user_input, page=1, option_flow = False):
	"""Create form for UI setup."""
	user_input = ensure_config(user_input)
	data_schema = OrderedDict()
	languages = list(SUPPORTED_LANGUAGES)

	if(page == 0):
		data_schema[vol.Required(CONF_NAME, default=user_input[CONF_NAME])] = str # name of the component without domain
		if option_flow:
			data_schema[vol.Required(CONF_RENEW_OAUTH, default=user_input[CONF_RENEW_OAUTH])] = vol.Coerce(bool) # show page 2
	elif(page == 1):
		data_schema[vol.Required(CONF_CLIENT_ID, default=user_input[CONF_CLIENT_ID])] = str # configuration of the cookie
		data_schema[vol.Required(CONF_CLIENT_SECRET, default=user_input[CONF_CLIENT_SECRET])] = str # configuration of the cookie
	elif(page == 2):
		data_schema[vol.Required(CONF_CODE+"TT", default="https://www.google.com/device?user_code="+user_input[CONF_CODE]["user_code"])] = str # name of the component without domain		
	elif(page == 3):
		# Generate a list of excluded entities.
		# This method is more reliable because it won't become invalid 
		# if users modify entity IDs, and it supports multiple instances.
		_exclude_entities = []
		if (_ytm := hass.data.get(DOMAIN)) is not None:
			for _ytm_player in _ytm.values():
				if DOMAIN_MP in _ytm_player:
					_exclude_entities.append(_ytm_player[DOMAIN_MP].entity_id)

		data_schema[vol.Required(CONF_RECEIVERS,default=user_input[CONF_RECEIVERS])] = selector({
				"entity": {
					"multiple": "true",
					"filter": [{"domain": DOMAIN_MP}],
					"exclude_entities": _exclude_entities
				}
			})
		data_schema[vol.Required(CONF_API_LANGUAGE, default=user_input[CONF_API_LANGUAGE])] = selector({
				"select": {
					"options": languages,
					"mode": "dropdown",
					"sort": True
				}
			})
		data_schema[vol.Required(CONF_HEADER_PATH, default=user_input[CONF_HEADER_PATH])] = str # file path of the header
		data_schema[vol.Required(CONF_ADVANCE_CONFIG, default=user_input[CONF_ADVANCE_CONFIG])] = vol.Coerce(bool) # show page 2

	elif(page == 4):
		data_schema[vol.Optional(CONF_SHUFFLE, default=user_input[CONF_SHUFFLE])] = vol.Coerce(bool) # default shuffle, TRUE/FALSE
		data_schema[vol.Optional(CONF_SHUFFLE_MODE, default=user_input[CONF_SHUFFLE_MODE])] = selector({  # choose default shuffle mode
				"select": {
					"options": ALL_SHUFFLE_MODES,
					"mode": "dropdown"
				}
			})
		data_schema[vol.Optional(CONF_LIKE_IN_NAME, default=user_input[CONF_LIKE_IN_NAME])] = vol.Coerce(bool) # default like_in_name, TRUE/FALSE
		data_schema[vol.Optional(CONF_DEBUG_AS_ERROR, default=user_input[CONF_DEBUG_AS_ERROR])] = vol.Coerce(bool) # debug_as_error, TRUE/FALSE
		data_schema[vol.Optional(CONF_LEGACY_RADIO, default=user_input[CONF_LEGACY_RADIO])] = vol.Coerce(bool) # default radio generation typ
		data_schema[vol.Optional(CONF_SORT_BROWSER, default=user_input[CONF_SORT_BROWSER])] = vol.Coerce(bool) # sort browser results
		data_schema[vol.Optional(CONF_INIT_EXTRA_SENSOR, default=user_input[CONF_INIT_EXTRA_SENSOR])] = vol.Coerce(bool) # default radio generation typ
		data_schema[vol.Optional(CONF_INIT_DROPDOWNS,default=user_input[CONF_INIT_DROPDOWNS])] = selector({  # choose dropdown(s)
				"select": {
					"options": ALL_DROPDOWNS,
					"multiple": "true"
				}
			})
		#  add for the old inputs.
		for _old_conf_input in OLD_INPUTS.values():
			if user_input.get(_old_conf_input) is not None:
				data_schema[vol.Optional(_old_conf_input, default=user_input[_old_conf_input])] = str

		data_schema[vol.Optional(CONF_TRACK_LIMIT, default=user_input[CONF_TRACK_LIMIT])] = vol.Coerce(int)
		data_schema[vol.Optional(CONF_MAX_DATARATE, default=user_input[CONF_MAX_DATARATE])] = vol.Coerce(int)
		data_schema[vol.Optional(CONF_BRAND_ID, default=user_input[CONF_BRAND_ID])] = str # brand id

		data_schema[vol.Optional(CONF_PROXY_PATH, default=user_input[CONF_PROXY_PATH])] = str # select of input_boolean -> continuous on/off
		data_schema[vol.Optional(CONF_PROXY_URL, default=user_input[CONF_PROXY_URL])] = str # select of input_boolean -> continuous on/off

	return data_schema

