
# Attempting to support yTube Music in Home Assistant #
import logging
import random
import os.path
import datetime
from urllib.request import urlopen, Request
from urllib.parse import unquote
import requests
from typing import Any, Callable, Dict, List, Optional, Tuple

import voluptuous as vol
from homeassistant.components.media_player import BrowseError
from homeassistant.helpers import config_validation as cv, entity_platform
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.core import Event
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.storage import STORAGE_DIR

from homeassistant.const import ATTR_ENTITY_ID, ATTR_FRIENDLY_NAME
import homeassistant.components.media_player as media_player

from pytubefix import YouTube # to generate cipher
from pytubefix import request # to generate cipher
from pytubefix import extract # to generate cipher

import ytmusicapi
from ytmusicapi.auth.oauth import OAuthCredentials
from pytubefix.exceptions import RegexMatchError
# use this to work with local version
# and make sure that the local package is also only loading local files
# from .ytmusicapi import YTMusic
from .browse_media import build_item_response, library_payload
from .const import *


################### Temp FIX remove me! ###############################
################### Temp FIX remove me! ###############################
import pytubefix, re

_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
	# Run setup via YAML
	_LOGGER.debug("Config via YAML")
	if(config is not None):
		async_add_entities([yTubeMusicComponent(hass, config, "_yaml")], update_before_add=True)


async def async_setup_entry(hass, config, async_add_entities):
	# Run setup via Storage
	_LOGGER.debug("Config via Storage/UI")
	if(len(config.data) > 0):
		async_add_entities([yTubeMusicComponent(hass, config, "")], update_before_add=True)


class yTubeMusicComponent(MediaPlayerEntity):
	def __init__(self, hass, config, name_add):
		self.hass = hass
		self._attr_unique_id = config.entry_id
		configuration = dict(config.options or config.data)
		self.hass.data[DOMAIN][self._attr_unique_id][DOMAIN_MP] = self
		self._debug_log_concat = ""	
		self._debug_as_error = configuration.get(CONF_DEBUG_AS_ERROR, DEFAULT_DEBUG_AS_ERROR)
		self._org_name = configuration.get(CONF_NAME, DOMAIN + name_add)
		self._attr_name = self._org_name
		self._api_language = configuration.get(CONF_API_LANGUAGE, DEFAULT_API_LANGUAGE)
		self._init_extra_sensor = configuration.get(CONF_INIT_EXTRA_SENSOR, DEFAULT_INIT_EXTRA_SENSOR)
		self._init_dropdowns = configuration.get(CONF_INIT_DROPDOWNS, DEFAULT_INIT_DROPDOWNS)
		self._maxDatarate = configuration.get(CONF_MAX_DATARATE,DEFAULT_MAX_DATARATE)

		# All entities are now automatically generated,will be registered in the async_update_selects method later.
		# This should be helpful for multiple accounts.
		self._selects = dict()  # use a dict to store the dropdown entity_id should be more convenient.
		# For old settings.
		for k,v in OLD_INPUTS.items():
			if v == CONF_SELECT_PLAYCONTINUOUS:
				_domain = input_boolean.DOMAIN
			else:
				_domain = input_select.DOMAIN
			try:
				self._selects[k] = configuration.get(v)
			except:
				pass
			if self._selects[k] is not None and self._selects[k].replace(" ","") != "":
				self._selects[k] = _domain + "." + self._selects[k].replace(_domain + ".", "")
				self.log_me('debug', "Found old {} {}: {},please consider using the new select entities.".format(_domain, k, self._selects[k] ))	

		self._like_in_name = configuration.get(CONF_LIKE_IN_NAME, DEFAULT_LIKE_IN_NAME)

		self._attr_shuffle = configuration.get(CONF_SHUFFLE, DEFAULT_SHUFFLE)
		self._shuffle_mode = configuration.get(CONF_SHUFFLE_MODE, DEFAULT_SHUFFLE_MODE)

		default_header_file = os.path.join(hass.config.path(STORAGE_DIR), DEFAULT_HEADER_FILENAME)
		self._header_file = configuration.get(CONF_HEADER_PATH, default_header_file)
		self._speakersList = configuration.get(CONF_RECEIVERS)
		self._trackLimit = configuration.get(CONF_TRACK_LIMIT)
		self._legacyRadio = configuration.get(CONF_LEGACY_RADIO)
		self._sortBrowser = configuration.get(CONF_SORT_BROWSER)
		self._friendly_speakersList = dict()

		# proxy settings
		self._proxy_url = configuration.get(CONF_PROXY_URL, "")
		self._proxy_path = configuration.get(CONF_PROXY_PATH, "")


		self.log_me('debug', "YtubeMediaPlayer config: ")
		self.log_me('debug', "- Header path: " + self._header_file)
		self.log_me('debug', "- speakerlist: " + str(self._speakersList))
		self.log_me('debug', "- shuffle: " + str(self._attr_shuffle))
		self.log_me('debug', "- shuffle_mode: " + str(self._shuffle_mode))
		self.log_me('debug', "- like_in_name: " + str(self._like_in_name))
		self.log_me('debug', "- track_limit: " + str(self._trackLimit))
		self.log_me('debug', "- legacy_radio: " + str(self._legacyRadio))
		self.log_me('debug', "- max_dataRate: " + str(self._maxDatarate))
		
		self._client_id = configuration.get(CONF_CLIENT_ID)
		self._client_secret = configuration.get(CONF_CLIENT_SECRET)
		self._brand_id = str(configuration.get(CONF_BRAND_ID, ""))
		self._api = None
		self._js = ""
		self._update_needed = False

		self._remote_player = ""
		self._untrack_remote_player = None
		self._untrack_remote_player_selector = None
		self._playlists = []
		self._playlist_to_index = {}
		self._tracks = []
		self._trackLimitUser = -1
		self._attributes = {}
		self._playing = False
		self._state = STATE_OFF
		self._track_name = None
		self._track_artist = None
		self._track_album_name = None
		self._track_album_cover = None
		self._track_artist_cover = None
		self._track_album_id = None
		self._media_duration = None
		self._media_position = None
		self._media_position_updated = None
		self._attributes['remote_player_state'] = STATE_OFF
		self._attributes['likeStatus'] = ""
		self._attributes['current_playlist_title'] = ""
		self._attributes['videoId'] = ""
		self._attributes['_media_type'] = ""
		self._attributes['_media_id'] = ""
		self._attributes['current_track'] = 0
		self._attributes['_media_type'] = None
		self._attributes['_media_id'] = None
		self._next_track_no = 0
		self._allow_next = False
		self._last_auto_advance = datetime.datetime.now()
		self._started_by = None
		self._interrupt_data = None
		self._attributes['remote_player_id'] = None
		self._volume = 0.0
		self._is_mute = False
		self._attr_repeat = RepeatMode.ALL
		self._signatureTimestamp = 0
		self._x_to_idle = None  # Some Mediaplayer don't transition to 'idle' but to 'off' on track end. This re-routes off to idle
		self._ignore_paused_on_media_change = False	# RobinR1, OwnTone compatibility
		self._ignore_next_remote_pause_state = False	# RobinR1, OwnTone compatibility: Some Mediaplayers temporarely switches to 'paused' during media changes (next/prev/seek)
		self._search = {"query": "", "filter": None, "limit": 20}
		self.reset_attributs()

		# register "call_method"
		if(name_add == ""):
			platform = entity_platform.current_platform.get()
			platform.async_register_entity_service(
				SERVICE_CALL_METHOD,
				{
					vol.Required(ATTR_COMMAND): cv.string,
					vol.Optional(ATTR_PARAMETERS): vol.All(
						cv.ensure_list, vol.Length(min=1), [cv.string]
					),
				},
				"async_call_method",
			)
			platform.async_register_entity_service(
				SERVICE_SEARCH,
				{
					vol.Required(ATTR_QUERY): cv.string,
					vol.Optional(ATTR_FILTER): cv.string,
					vol.Optional(ATTR_LIMIT): vol.Coerce(int)
				},
				"async_search",
			)
			platform.async_register_entity_service(
				SERVICE_ADD_TO_PLAYLIST,
				{
					vol.Optional(ATTR_SONG_ID): cv.string,
					vol.Optional(ATTR_PLAYLIST_ID): cv.string
				},
				"async_add_to_playlist",
			)
			platform.async_register_entity_service(
				SERVICE_REMOVE_FROM_PLAYLIST,
				{
					vol.Optional(ATTR_SONG_ID): cv.string,
					vol.Optional(ATTR_PLAYLIST_ID): cv.string
				},
				"async_remove_from_playlist",
			)
			platform.async_register_entity_service(
				SERVICE_CALL_RATE_TRACK,
				{
					vol.Required(ATTR_RATING): cv.string,
					vol.Optional(ATTR_SONG_ID): cv.string
				},
				"async_rate_track",
			)
			platform.async_register_entity_service(
				SERVICE_LIMIT_COUNT,
				{
					vol.Required(ATTR_LIMIT): vol.Coerce(int)
				},
				"async_limit_count",
			)
			platform.async_register_entity_service(
				SERVICE_RADIO,
				{
					vol.Optional(ATTR_INTERRUPT): vol.Coerce(bool)
				},
				"async_start_radio",
			)

		# run the api / get_cipher / update select as soon as possible
		if hass.is_running:
			self._update_needed = True
		else:
			hass.bus.async_listen_once(EVENT_HOMEASSISTANT_START, self.async_startup)


	# user had difficulties during the debug message on, so we'll provide a workaroud to post debug as errors
	def log_me(self, type, msg):
		# clear buffer of _later
		# see if this is just the ending message:
		try:
			if(isinstance(msg, str)):
				if(msg.find('[E]') == 0 and self._debug_log_concat != ""):
					name = msg.split('[E]')[1]
					if(self._debug_log_concat.find(name) >= 0):
						self._debug_log_concat += " [E]"
						msg = ""
			if(self._debug_log_concat != ""):
				if(self._debug_as_error):
					_LOGGER.error(self._debug_log_concat)
				else:
					_LOGGER.debug(self._debug_log_concat)
				self._debug_log_concat = ""
		except:
			self.exc()
		# send new message
		if(msg != ""):
			if(self._debug_as_error or type == 'error'):
				_LOGGER.error(msg)
			else:
				_LOGGER.debug(msg)

	def log_debug_later(self, msg):
		# sum up a log
		if(msg.find('[S]') == 0):  # a new start message
			if(self._debug_log_concat != ""):  # if there is something in the buffer print it now
				self.log_me("", "")
			self._debug_log_concat = msg  # start with a new buffer
		else:  # not a new messsage, append it
			self._debug_log_concat += " ... " + msg
		if self._debug_log_concat.find('[E]') >= 0:  # if the end part is in the messeage print it now
			self.log_me("", "")


	def reset_attributs(self):
		# reset some common attributs
		self._playing = False
		self._state = STATE_OFF
		self._track_name = None
		self._track_artist = None
		self._track_album_name = None
		self._track_album_cover = None
		self._track_artist_cover = None
		self._track_album_id = None
		self._media_duration = None
		self._media_position = None
		self._media_position_updated = None
		self._app_id = None
		self._attributes['remote_player_state'] = STATE_OFF
		self._attributes['likeStatus'] = ""
		self._attributes['current_playlist_title'] = ""
		self._attributes['videoId'] = ""
		self._attributes['_media_type'] = ""
		self._attributes['_media_id'] = ""
		self._attributes['current_track'] = 0
		self._attributes['_media_type'] = None
		self._attributes['_media_id'] = None

		self.hass.data[DOMAIN][self._attr_unique_id]['lyrics'] = ""
		# After turning off the media_player, keep the playlists and search information available
		# as they may be needed forautomations.
		# self.hass.data[DOMAIN][self._attr_unique_id]['search'] = ""
		self.hass.data[DOMAIN][self._attr_unique_id]['tracks'] = ""
		# self.hass.data[DOMAIN][self._attr_unique_id]['playlists'] = ""
		self.hass.data[DOMAIN][self._attr_unique_id]['total_tracks'] = 0


	async def async_update(self):
		# update will be called eventually BEFORE homeassistant is started completly
		# therefore we should not use this method for ths init
		self.log_debug_later("[S] async_update")
		if(self._update_needed):
			self._update_needed = False
			await self.async_startup(self.hass)
		self.log_me('debug', "[E] async_update")

	# either called once homeassistant started (component was configured before startup)
	# or call from update(), if the component was configured AFTER homeassistant was started
	async def async_startup(self, hass):
		self.log_me('debug', "[S] async_startup")
		try:
			await self.async_get_cipher('BB2mjBuAtiQ')
		except:
			self.log_me('error', "async_get_cipher failed")
		try:
			await self.async_check_api()
		except:
			self.log_me('error', "async_check_api failed")
		try:
			await self.async_update_selects()
		except:
			self.log_me('error', "async_update_selects failed")
		try:
			await self.async_update_playmode()
		except:
			self.log_me('error', "async_update_playmode failed")
		self.log_me('debug', "[E] async_startup")

	async def async_check_api(self):
		self.log_debug_later("[S] async_check_api")
		if(self._api is None):
			self.log_debug_later("- no valid API, try to login")
			if(os.path.exists(self._header_file)):
				oauth_credentials=OAuthCredentials(client_id=self._client_id, client_secret=self._client_secret)
				[ret, msg, self._api] = await async_try_login(self.hass, self._header_file, self._brand_id, self._api_language,oauth_credentials)
				if(msg != ""):
					self._api = None
					out = "Issue during login: " + msg
					data = {"title": "yTubeMediaPlayer error", "message": out}
					await self.hass.services.async_call("persistent_notification", "create", data)
					self.log_me('debug', "[E] (fail) async_check_api")
					return False
				else:
					self._signatureTimestamp = await self.hass.async_add_executor_job(self._api.get_signatureTimestamp)
					try:
						self.log_debug_later("YouTube Api initialized ok, version: " + str(ytmusicapi.__version__))
					except:
						self.log_debug_later("YouTube Api initialized ok")
			else:
				out = "can't find header file at " + self._header_file
				data = {"title": "yTubeMediaPlayer error", "message": out}
				await self.hass.services.async_call("persistent_notification", "create", data)
				self.log_me('debug', "[E] (fail) async_check_api")
				return False
		self.log_me('debug', "[E] async_check_api")
		return True

	@property
	def device_info(self):
		return {
			'identifiers': {(DOMAIN, self._attr_unique_id)},
			'name': self._attr_name,
			'manufacturer': "Google Inc.",
			'model': DOMAIN
		}

	@property
	def name(self):
		# Return the name of the player.
		return self._attr_name

	@property
	def icon(self):
		return 'mdi:music-circle'

	@property
	def supported_features(self) -> media_player.MediaPlayerEntityFeature:
		# Flag media player features that are supported.
		return SUPPORT_YTUBEMUSIC_PLAYER

	@property
	def should_poll(self):
		# No polling needed.
		return False

	@property
	def state(self):
		# Return the state of the device.
		return self._state

	@property
	def extra_state_attributes(self):
		# Return the device state attributes.
		return self._attributes

	@property
	def is_volume_muted(self):
		# Return True if device is muted
		return self._is_mute

	@property
	def is_on(self):
		# Return True if device is on.
		return self._playing

	@property
	def media_content_type(self):
		# Content type of current playing media.
		return MediaType.MUSIC

	@property
	def media_title(self):
		# Title of current playing media.
		return self._track_name

	@property
	def media_artist(self):
		# Artist of current playing media
		return self._track_artist

	@property
	def media_album_name(self):
		# Album name of current playing media
		return self._track_album_name

	@property
	def media_image_url(self):
		# Image url of current playing media.
		return self._track_album_cover

	@property
	def media_image_remotely_accessible(self):
		# True  returns: entity_picture: http://lh3.googleusercontent.com/Ndilu...
		# False returns: entity_picture: /api/media_player_proxy/media_player.gmusic_player?token=4454...
		return True

	@property
	def media_position(self):
		# Position of current playing media in seconds.
		return self._media_position


	@property
	def media_position_updated_at(self):
		# When was the position of the current playing media valid.
		# Returns value from homeassistant.util.dt.utcnow().
		#
		return self._media_position_updated


	@property
	def media_duration(self):
		# Duration of current playing media in seconds.
		return self._media_duration


	@property
	def shuffle(self):
		# Boolean if shuffling is enabled.
		return self._attr_shuffle

	@property
	def repeat(self):
		# Return current repeat mode.
		return self._attr_repeat

	async def async_set_repeat(self, repeat: str):
		if self.repeat != repeat:
			self.log_me('debug', f"[S] set_repeat: {repeat}")
			# Set repeat mode.
			self._attr_repeat = repeat
			if(self._selects['repeatmode'] is not None):
				if repeat == RepeatMode.ALL:
					ib_repeat = STATE_ON
				else:
					ib_repeat = STATE_OFF
				if (_state := self.hass.states.get(self._selects['repeatmode']).state) != repeat:
					if input_boolean.DOMAIN in self._selects['repeatmode']:
						if _state != ib_repeat:
							data = {ATTR_ENTITY_ID: self._selects['repeatmode']}
							if ib_repeat == STATE_ON:
								await self.hass.services.async_call(input_boolean.DOMAIN, IB_ON, data)
							else:
								await self.hass.services.async_call(input_boolean.DOMAIN, IB_OFF, data)
					else:
						data = {select.ATTR_OPTION: repeat, ATTR_ENTITY_ID: self._selects['repeatmode']}
						await self.hass.services.async_call(select.DOMAIN, select.SERVICE_SELECT_OPTION, data)
					
			self.log_me('debug', f"[E] set_repeat: {repeat}")
			self.async_schedule_update_ha_state()

	@property
	def volume_level(self):
		# Volume level of the media player (0..1).
		return self._volume


	async def async_turn_on(self, *args, **kwargs):
		# Turn on the selected media_player from select
		self.log_me('debug', "[S] TURNON")
		self._started_by = "UI"

		# exit if we don't konw what to play (the select_playlist will be set to "" if the config provided a value but the entity_id is not in homeassistant)
		if self._selects['playlists'] is None:
			self.log_me('debug', "no or wrong playlist select field in the config, exiting")
			msg = "You have no playlist entity_id in your config, or that entity_id is not in homeassistant. I don't know what to play and will exit. Either use the media_browser or add the playlist dropdown"
			data = {"title": "yTubeMediaPlayer error", "message": msg}
			await self.hass.services.async_call("persistent_notification", "create", data)
			await self.async_turn_off_media_player()
			self.log_me('debug', "[E] (fail) TURNON")
			return

		# set UI to correct playlist, or grab playlist if none was submitted
		playlist = self.hass.states.get(self._selects['playlists']).state

		# exit if we don't have any playlists from the account
		if(len(self._playlists) == 0):
			_LOGGER.error("playlists empty")
			await self.async_turn_off_media_player()
			self.log_me('debug', "[E] (fail) TURNON")
			return

		# load ID for playlist name
		idx = self._playlist_to_index.get(playlist)
		if idx is None:
			_LOGGER.error("playlist to index is none!")
			await self.async_turn_off_media_player()
			self.log_me('debug', "[E] (fail) TURNON")
			return

		# playlist or playlist_radio?
		if self._selects['radiomode'] is not None:
			_source = self.hass.states.get(self._selects['radiomode'])
			if _source is None:
				_LOGGER.error("- (%s) is not a valid select entity.", self._selects['radiomode'])
				self.log_me('debug', "[E] (fail) TURNON")
				return
			if(_source.state == "Playlist"):
				self._attributes['_media_type'] = MediaType.PLAYLIST
			else:
				self._attributes['_media_type'] = CHANNEL
		else:
			self._attributes['_media_type'] = MediaType.PLAYLIST

		# store id and start play_media
		self._attributes['_media_id'] = self._playlists[idx]['playlistId']
		self.log_me('debug', "[E] TURNON")
		return await self.async_play_media(media_type=self._attributes['_media_type'], media_id=self._attributes['_media_id'])

	async def async_prepare_play(self):
		self.log_me('debug', "[S] async_prepare_play")
		if(not await self.async_check_api()):
			self.log_me('debug', "[E] (fail) async_prepare_play")
			return False

		# get _remote_player
		if not await self.async_update_remote_player():
			self.log_me('debug', "[E] (fail) async_prepare_play")
			return False
		_player = self.hass.states.get(self._remote_player)

		# subscribe to changes
		if self._selects['playmode'] is not None:
			async_track_state_change_event(self.hass, self._selects['playmode'], self.async_update_playmode)
		if self._selects['repeatmode'] is not None:
			async_track_state_change_event(self.hass, self._selects['repeatmode'], self.async_update_playmode)
		if self._selects['speakers'] is not None:
			async_track_state_change_event(self.hass, self._selects['speakers'], self.async_select_source_helper)

		# make sure that the player, is on and idle
		try:
			if self._playing is True:
				await self.async_media_stop()
			elif self._playing is False and self._state == STATE_OFF:
				if _player.state == STATE_OFF:
					await self.async_turn_on_media_player()
			else:
				self.log_me('debug', "self._state is: (" + self._state + ").")
				if(self._state == STATE_PLAYING):
					await self.async_media_stop()
		except:
			_LOGGER.error("We hit an error during prepare play, likely related to issue 52")
			_LOGGER.error("Player: " + str(_player) + ".")
			_LOGGER.error("remote_player: " + str(self._remote_player) + ".")
			self.exc()


		# update cipher
		await self.async_get_cipher('BB2mjBuAtiQ')

		# display imidiatly a loading state to provide feedback to the user
		self._allow_next = False
		self._track_album_name = ""
		self._track_artist = ""
		self._track_artist_cover = None
		self._track_album_cover = None
		self._track_name = "loading..."
		self._state = STATE_PLAYING  # a bit early otherwise no info will be shown
		self.async_schedule_update_ha_state()
		self.log_me('debug', "[E] async_prepare_play")
		return True

	async def async_turn_on_media_player(self, data=None):
		self.log_debug_later("[S] async_turn_on_media_player")
		# Fire the on action.
		if data is None:
			data = {ATTR_ENTITY_ID: self._remote_player}
		self._state = STATE_IDLE
		self.async_schedule_update_ha_state()
		self.log_me('debug', "[E] async_turn_on_media_player")
		await self.hass.services.async_call(DOMAIN_MP, 'turn_on', data)


	async def async_turn_off(self, entity_id=None, old_state=None, new_state=None, **kwargs):
		# Turn off the selected media_player
		self.log_me('debug', "turn_off")
		self._playing = False
		await self.async_turn_off_media_player()

	async def async_turn_off_media_player(self, data=None):
		self.log_debug_later("[S] async_turn_off_media_player")
		# Fire the off action.
		self.reset_attributs()
		if(self._like_in_name):
			self._attr_name = self._org_name
		self.async_schedule_update_ha_state()
		if(self._remote_player == ""):
			if(not(await self.async_update_remote_player())):
				self.log_me('debug', "[E] (fail) async_turn_off_media_player")
				return
		if(data != 'skip_remote_player'):
			data = {ATTR_ENTITY_ID: self._remote_player}
			await self.hass.services.async_call(DOMAIN_MP, 'media_stop', data)
			await self.hass.services.async_call(DOMAIN_MP, 'turn_off', data)

		# unsubscribe from remote media_player
		if(self._untrack_remote_player is not None):
			try:
				self._untrack_remote_player()
			except:
				pass
			self._untrack_remote_player = None

		self.log_me('debug', "[E] async_turn_off_media_player")


	async def async_update_remote_player(self, remote_player=""):
		self.log_debug_later("[S] async_update_remote_player(Input " + str(remote_player) + "/ current " + str(self._remote_player) + ") ")
		if(remote_player == self._remote_player and remote_player != ""):
			self.log_me('debug', " no change [E]")
			return


		old_remote_player = self._remote_player
		# sanitize player, remove domain
		remote_player = remote_player.replace(DOMAIN_MP + ".", "")

		if(remote_player != ""):
			# make sure that the entity ID is complete
			remote_player = DOMAIN_MP + "." + remote_player
		# sets the current media_player from speaker select
		elif(self._selects['speakers'] is not None and await self.async_check_entity_exists(self._selects['speakers'], unavailable_is_ok=False)):  # drop down for player does exist .. double check!!
			media_player_select = self.hass.states.get(self._selects['speakers'])  # Example: self.hass.states.get(select.gmusic_player_speakers)
			if media_player_select is None:
				self.log_me('error', "(" + self._selects['speakers'] + ") is not a valid select entity to get the player.")
			else:
				# since we can't be sure if the MediaPlayer Domain is in the field value, add it and remove it :D
				remote_player = DOMAIN_MP + "." + media_player_select.state.replace(DOMAIN_MP + ".", "")

		# ok lets check if we have a player or post an error
		if(await self.async_check_entity_exists(remote_player)):
			self._remote_player = remote_player
			self._attributes['remote_player_id'] = self._remote_player
		elif(await self.async_check_entity_exists(self._remote_player)):
			self._attributes['remote_player_id'] = self._remote_player
		else:
			self._track_name = "Please select player first"
			self.async_schedule_update_ha_state()
			msg = "Please select a player before start playing, e.g. via the 'media_player.select_source' method or in the settings/config_flow"
			data = {"title": "yTubeMediaPlayer error", "message": msg}
			await self.hass.services.async_call("persistent_notification", "create", data)
			self.log_me('error', "No player selected or the selected player isn't available (" + str(remote_player) + "/" + str(self._remote_player) + "), you will not be able to play music, please set the default player in the settings/config_flow or call media_player.select_source")
			self.log_me('debug', "[E] (fail) async_update_remote_player")
			return False

		# unsubscribe / resubscribe to the player, because the old subscrition was for the old player
		if self._remote_player != old_remote_player:
			if(self._untrack_remote_player is not None):
				try:
					self._untrack_remote_player()
				except:
					pass
				self._untrack_remote_player = None
		if(self._untrack_remote_player is None):
			self._untrack_remote_player = async_track_state_change_event(self.hass, self._remote_player, self.async_sync_player)
		self.log_me('debug', "[E] async_update_remote_player")
		return True


	async def async_get_cipher(self, videoId):
		self.log_debug_later("[S] async_get_cipher")
		embed_url = "https://www.youtube.com/embed/" + videoId
		# this is why we need pytubefix as include 
		embed_html = await self.hass.async_add_executor_job(request.get, embed_url)
		js_url = extract.js_url(embed_html)
		self._js = await self.hass.async_add_executor_job(request.get, js_url)
		self._cipher = pytubefix.cipher.Cipher(js=self._js, js_url=js_url)
		# this is why we need pytubefix as include 
		self.log_me('debug', "[E] async_get_cipher")

	async def async_sync_player(self, event=None):
		self.log_debug_later("[S] async_sync_player")
		if isinstance(event,Event):
			_event_data = event.data
			entity_id = _event_data.get('entity_id')
			old_state = _event_data.get('old_state')
			new_state = _event_data.get('new_state')
		else:
			entity_id = None
			old_state = None
			new_state = None
			self.log_me('debug', f"event: {event}")
	
		if(entity_id is not None and old_state is not None) and new_state is not None:
			self.log_debug_later(entity_id + ": " + old_state.state + " -> " + new_state.state)
			if(entity_id.lower() != self._remote_player.lower()):
				self.log_me('debug', "- ignoring player " + str(entity_id) + " the player of interest is " + str(self._remote_player))
				return
		else:
			self.log_debug_later(self._remote_player)

		# Perform actions based on the state of the selected (Speakers) media_player #
		if not self._playing:
			self.log_debug_later("not playing [E]")
			return
		# _player = The selected speakers #
		_player = self.hass.states.get(self._remote_player)

		# Only update the duration and especially the position if we're not in pause
		# else the mini-media-player will advance during our pause state
		if(self._state != STATE_PAUSED):
			if('media_duration' in _player.attributes):
				self._media_duration = _player.attributes['media_duration']
			if('media_position' in _player.attributes):
				self._media_position = _player.attributes['media_position']
			if('media_position_updated_at' in _player.attributes):
				if(isinstance(_player.attributes['media_position_updated_at'],datetime.datetime)):
					self._media_position_updated = _player.attributes['media_position_updated_at']
				else:
					self._media_position_updated = datetime.datetime.now(datetime.timezone.utc)
			else:
				self._media_position_updated = datetime.datetime.now(datetime.timezone.utc)

		# Workaround for chromecast sometimes not playing first song in a playlist
		if(old_state!=None and new_state!=None):	
			try:
				if(old_state.state == STATE_IDLE and new_state.state == STATE_PAUSED):
					if(self._state == STATE_PLAYING):
						self.log_me('error','chromecast in pause should be playings, '+str(old_state))
						await self.async_get_track()
			except:
				pass

		# detect app switch an turn off if so
		if('app_id' in _player.attributes):
			if(self._app_id == None):
				self._app_id = _player.attributes['app_id']
				self.log_me('debug', "detected app _id, "+str(self._app_id))
			elif (_player.attributes['app_id'] != self._app_id):
				self.log_me('debug', "detected different app _id, shuttiung down without interruption")
				await self.async_turn_off_media_player('skip_remote_player')
				return

		# entity_id of selected speakers. #
		self._attributes['remote_player_id'] = _player.entity_id

		# _player state - Example [playing -or- idle]. #
		self._attributes['remote_player_state'] = _player.state

		# unlock allow next, some player fail because their media_position is 'strange' catch #
		found_position = False
		try:
			if 'media_position' in _player.attributes:
				found_position = True
				if(isinstance(_player.attributes['media_position'], int)):
					if _player.state == 'playing' and _player.attributes['media_position'] > 0:
						self._allow_next = True
		except:
			found_position = False
		if not(found_position) and _player.state == 'playing':  # fix for browser mod media_player not providing the 'media_position'
			self._allow_next = True

		# auto next .. best cast: we have an old and a new state #
		if(old_state is not None and new_state is not None):
			# chromecast quite frequently change from playing to idle twice, so we need some kind of time guard
			if(old_state.state == STATE_PLAYING and new_state.state == STATE_IDLE and (datetime.datetime.now() - self._last_auto_advance).total_seconds() > 10):
				self._allow_next = False
				# add track to history
				try:
					response = await self.hass.async_add_executor_job(lambda: self._api.get_song(self._attributes['videoId'], self._signatureTimestamp))
					await self.hass.async_add_executor_job(lambda: self._api.add_history_item(response))
				except:
					self.log_me('debug', "adding "+self._attributes['videoId']+" to history failed")

				await self.async_get_track(auto_advance=True) 
			# turn this player off when the remote_player was shut down
			elif((old_state.state == STATE_PLAYING or old_state.state == STATE_IDLE or old_state.state == STATE_PAUSED) and new_state.state == STATE_OFF):
				if(self._x_to_idle == STATE_OFF or self._x_to_idle == STATE_OFF_1X):  # workaround for MPD (changes to OFF at the end of a track)
					self._allow_next = False
					# add track to history
					try:
						response = await self.hass.async_add_executor_job(lambda: self._api.get_song(self._attributes['videoId'], self._signatureTimestamp))
						await self.hass.async_add_executor_job(lambda: self._api.add_history_item(response))
					except:
						self.log_me('debug', "adding "+self._attributes['videoId']+" to history failed")
					await self.async_get_track(auto_advance=True)
					if(self._x_to_idle == STATE_OFF_1X):
						self._x_to_idle = None
				else:
					self._state = STATE_OFF
					self.log_me('debug', "media player got turned off")
					await self.async_turn_off()
			# workaround for SONOS (changes to PAUSED at the end of a track)
			elif(old_state.state == STATE_PLAYING and new_state.state == STATE_PAUSED and  # noqa: W504
								(datetime.datetime.now() - self._last_auto_advance).total_seconds() > 10 and  # noqa: W504
								self._x_to_idle == STATE_PAUSED):
				# add track to history
				try:
					response = await self.hass.async_add_executor_job(lambda: self._api.get_song(self._attributes['videoId'], self._signatureTimestamp))
					await self.hass.async_add_executor_job(lambda: self._api.add_history_item(response))
				except:
					self.log_me('debug', "adding "+self._attributes['videoId']+" to history failed")
				self._allow_next = False
				await self.async_get_track(auto_advance=True)
			# set this player in to pause state when the remote player does, or ignore when assumed it is a temporary state (as some players do while seeking/skipping track)
			elif(old_state.state == STATE_PLAYING and new_state.state == STATE_PAUSED):
				self.log_me('debug', "Remote Player changed from PLAYING to PAUSED.")
				if(self._ignore_paused_on_media_change and self._ignore_next_remote_pause_state):	# RobinR1, OwnTone compatibility
					self.log_me('debug', "Ignoring state change")					# RobinR1, OwnTone compatibility
					self._ignore_next_remote_pause_state = False					# RobinR1, OwnTone compatibility
					return										# RobinR1, OwnTone compatibility
				else:											# RobinR1, OwnTone compatibility
					return await self.async_media_pause()
			# resume playback when the player does
			elif(old_state.state == STATE_PAUSED and new_state.state == STATE_PLAYING and self._state == STATE_PAUSED):
				return await self.async_media_play()
			# player changes itsself from pause -> idle (while we where in pause state)
			elif(old_state.state == STATE_PAUSED and new_state.state == STATE_IDLE and self._state == STATE_PAUSED):
				self.log_me('debug', "Remote Player changed from PAUSED to IDLE withouth our interaction, so likely another source is using the player now. I'll step back and swich myself off")
				await self.async_turn_off_media_player('skip_remote_player')
				return
		# no states, lets rely on stuff like _allow_next
		elif _player.state == 'idle':
			if self._allow_next:
				if (datetime.datetime.now() - self._last_auto_advance).total_seconds() > 10:
					self._allow_next = False
					await self.async_get_track(auto_advance=True)


		# Set new volume if it has been changed on the _player #
		if 'volume_level' in _player.attributes:
			self._volume = round(_player.attributes['volume_level'], 2)
		self.async_schedule_update_ha_state()
		self.log_me('debug', "[E] async_sync_player")

	async def async_ytubemusic_play_media(self, event):
		self.log_me('debug', "[S] async_ytubemusic_play_media")
		_speak = event.data.get('speakers')
		_source = event.data.get('source')
		_media = event.data.get('name')

		if event.data['shuffle_mode']:
			self._shuffle_mode = event.data.get('shuffle_mode')
			_LOGGER.info("SHUFFLE_MODE: %s", self._shuffle_mode)

		if event.data['shuffle']:
			self.async_set_shuffle(event.data.get('shuffle'))
			_LOGGER.info("- SHUFFLE: %s", self._attr_shuffle)

		self.log_me('debug', "- Speakers: (%s) | Source: (%s) | Name: (%s)", _speak, _source, _media)
		await self.async_play_media(_source, _media, _speak)
		self.log_me('debug', "[E] async_ytubemusic_play_media")


	def extract_info(self, _track):
		# self.log_me('debug', "extract_info")
		# If available, get track information. #
		info = dict()
		info['track_album_name'] = ""
		info['track_artist_cover'] = ""
		info['track_name'] = ""
		info['track_artist'] = ""
		info['track_album_cover'] = ""
		info['track_album_id'] = ""

		try:
			if 'title' in _track:
				info['track_name'] = _track['title']
		except:
			pass

		try:
			if 'byline' in _track:
				info['track_artist'] = _track['byline']
			elif 'artists' in _track:
				info['track_artist'] = ""
				if(isinstance(_track["artists"], str)):
					info['track_artist'] = _track["artists"]
				elif(isinstance(_track["artists"], list)):
					for t in _track['artists']:
						if 'name' in t:
							name = t['name']
						else:
							name = t
						if(info['track_artist'] == ""):
							info['track_artist'] = name
						else:
							info['track_artist'] += " / " + name
			elif 'author' in _track:
				info['track_artist'] = _track['author']  # use 'author' if still no artist info.
		except:
			pass

		try:
			_album_art_ref = None
			if 'thumbnail' in _track:
				_album_art_ref = _track['thumbnail']  # returns a list,
				if 'thumbnails' in _album_art_ref:
					_album_art_ref = _album_art_ref['thumbnails']
			elif 'thumbnails' in _track:
				_album_art_ref = _track['thumbnails']  # returns a list

			if isinstance(_album_art_ref, list):
				th_width = 0
				for th_data in _album_art_ref:
					if('width' in th_data and 'url' in th_data):
						if(th_data['width'] > th_width):
							th_width = th_data['width']
							info['track_album_cover'] = th_data['url']
		except:
			pass

		try:
			if 'album' in _track:
				info['track_album_name'] = _track['album']['name']  # fix missing album info.
				if 'id' in _track['album']:
					info['track_album_id'] = _track['album']['id']
		except:
			pass

		# make sure all extracted infos are actually strings
		for key in info:
			if(info[key] is None):
				info[key] = ""
		return info

	async def async_select_source_helper(self, event=None):
		self.log_me('debug', "[S] async_select_source_helper")
		# redirect call, obviously we got called by status change, so we can call it without argument and let it pick
		source_entity_id = None
		source = self.hass.states.get(self._selects['speakers']).state
		# get entity id from friendly_name
		for e, f in self._friendly_speakersList.items():
			if(f == source):
				source_entity_id = f"{DOMAIN_MP}.{e}"
				break
		if(source_entity_id is None):
			self.log_me('debug', "- Couldn't find " + source + " in dropdown list, giving up")
			return
		else:
			self.log_me('debug', 'Translated friendly name ' + source + ' to entity id ' + source_entity_id)
		self.log_me('debug', "selected '"+source_entity_id+"'")
		self.log_me('debug', "[E] async_select_source_helper")
		return await self.async_select_source(source_entity_id)

	async def async_select_source(self, source=None):
		self.log_me('debug', "[S] async_select_source(" + str(source) + ")")
		# source should just be the NAME without DOMAIN, to select it in the dropdown
		if(isinstance(source, str)):
			source = source.replace(DOMAIN_MP + ".", "")
		# shutdown old player if we're currently playimg
		was_playing = self._playing
		if(self._playing):
			self.log_me('debug', "- was playing")
			old_player = self.hass.states.get(self._remote_player)
			await self.async_media_stop(player=self._remote_player)  # important to mention the player here explictly. We're going to change it and stuff runs async
		# set player
		if(source is not None):
			# set entity_id
			await self.async_update_remote_player(remote_player=DOMAIN_MP + "." + source)
			self.log_me('debug', "- Choosing " + self._remote_player + " as player")
			# try to set drop down
			if self._selects['speakers'] is not None:
				if(not await self.async_check_entity_exists(self._selects['speakers'], unavailable_is_ok=False)):
					self.log_me('debug', "- Drop down for media player: " + str(self._selects['speakers']) + " not found")
				elif source in self._friendly_speakersList:
					# untrack player field change (to avoid self call)
					if(self._untrack_remote_player_selector is not None):
						try:
							self._untrack_remote_player_selector()
							self._untrack_remote_player_selector = None
							self.log_me('debug', "- untrack passed")
						except:
							self.log_me('debug', "- untrack failed")
							pass
					if self.hass.states.get(self._selects['speakers']).state != self._friendly_speakersList[source]:
						data = {select.ATTR_OPTION: self._friendly_speakersList[source], ATTR_ENTITY_ID: self._selects['speakers']}
						await self.hass.services.async_call(select.DOMAIN, select.SERVICE_SELECT_OPTION, data)
					# resubscribe with 3 sec delay so the UI can settle, directly call it will trigger the change from above
					async_call_later(self.hass, 3, self.async_track_select_mediaplayer_helper)
				else:
					self.log_me('debug', "- Selected player '" + source + "' not found in options for Drop down, skipping")
		else:
			# load from dropdown, if that fails, exit
			if(not await self.async_update_remote_player()):
				_LOGGER.error("- async_update_remote_player failed")
				return
		# if playing, switch player
		if(was_playing):
			# don't call "_play" here, as that resets the playlist position
			await self.async_get_track()
			# seek, if possible
			new_player = self.hass.states.get(self._remote_player)
			if (all(a in old_player.attributes for a in ('media_position', 'media_position_updated_at', 'media_duration')) and 'supported_features' in new_player.attributes):
				if(new_player.attributes['supported_features'] | MediaPlayerEntityFeature.SEEK):
					now = datetime.datetime.now(datetime.timezone.utc)
					delay = now - old_player.attributes['media_position_updated_at']
					pos = delay.total_seconds() + old_player.attributes['media_position']
					if pos < old_player.attributes['media_duration']:
						data = {'seek_position': pos, ATTR_ENTITY_ID: self._remote_player}
						await self.hass.services.async_call(DOMAIN_MP, media_player.SERVICE_MEDIA_SEEK, data)
		if not self.entity_id:
			self.log_me('debug', "Skipping state update because entity_id is not yet set")
		else:
			self.async_schedule_update_ha_state()

		self.log_me('debug', "[E] async_select_source")


	async def async_update_selects(self, now=None):
		self.log_me('debug', "[S] async_update_selects")
		# -- Register dropdown(s). -- #
		for dropdown in self._init_dropdowns:
			if not await self.async_check_entity_exists(self._selects[dropdown], unavailable_is_ok=False):
				entity_id = self.hass.data[DOMAIN][self._attr_unique_id][f'select_{dropdown}'].entity_id
				if await self.async_check_entity_exists(entity_id, unavailable_is_ok=False):
					self._selects[dropdown] = entity_id
					self.log_me('debug', f"- {dropdown} select: {str(entity_id)} registered")

		# track changes
		if(self._untrack_remote_player_selector is not None):
			try:
				self._untrack_remote_player_selector()
			except:
				self.log_me('error', 'untrack failed')
		if self._selects['speakers'] is not None:
			self._untrack_remote_player_selector = async_track_state_change_event(self.hass, self._selects['speakers'], self.async_select_source_helper)
		if self._selects['playmode'] is not None:
			async_track_state_change_event(self.hass, self._selects['playmode'], self.async_update_playmode)
		if self._selects['repeatmode'] is not None:
			async_track_state_change_event(self.hass, self._selects['repeatmode'], self.async_update_playmode)
		# ----------- speaker -----#
		try:
			if(isinstance(self._speakersList, str)):
				speakersList = [self._speakersList]
			else:
				speakersList = list(self._speakersList)
			for i in range(0, len(speakersList)):
				speakersList[i] = speakersList[i].replace(DOMAIN_MP + ".", "")
		except:
			speakersList = list()

		# generate the speaker list in any case (will be needed for the media_browser)
		if(len(speakersList) <= 1):  # Perhaps this behavior is no longer necessary?
			all_entities = await self.hass.async_add_executor_job(self.hass.states.all)
			for e in all_entities:
				if(e.entity_id.startswith(DOMAIN_MP) and not(e.entity_id.startswith(DOMAIN_MP + "." + DOMAIN))):
					speakersList.append(e.entity_id.replace(DOMAIN_MP + ".", ""))
		# create friendly speakerlist based on the current speakerLlist
		self._friendly_speakersList = dict()
		for a in speakersList:
			state = self.hass.states.get(DOMAIN_MP + "." + a)
			friendly_name = state.attributes.get(ATTR_FRIENDLY_NAME)
			if(friendly_name is None):
				friendly_name = a
			self._friendly_speakersList.update({a: friendly_name})
		friendly_speakersList = list(self._friendly_speakersList.values())
		if self._selects['speakers'] is not None:
			if input_select.DOMAIN in self._selects['speakers']:
				_select = input_select
			else:
				_select = select
			data = {_select.ATTR_OPTIONS: friendly_speakersList, ATTR_ENTITY_ID: self._selects['speakers']}
			if _select == input_select:
				await self.hass.services.async_call(input_select.DOMAIN, input_select.SERVICE_SET_OPTIONS, data)
			else:
				await self.hass.data[DOMAIN][self._attr_unique_id]['select_speakers'].async_update(friendly_speakersList)  # update speaker select
			
			data = {_select.ATTR_OPTION: friendly_speakersList[0], ATTR_ENTITY_ID: self._selects['speakers']}  # select the first one in the list as the default player
			await self.hass.services.async_call(_select.DOMAIN, _select.SERVICE_SELECT_OPTION, data)
		else:
			# we need to set the default player here, as there is no selct field. without a select field we don't get updates from the field and will never set the default player
			await self.async_select_source(speakersList[0])
		
		# finally call update playlist to fill the list .. if it exists
		await self.async_update_playlists()
		self.log_me('debug', "[E] async_update_selects")

	async def async_check_entity_exists(self, e, unavailable_is_ok=True):
		try:
			r = self.hass.states.get(e)
			if(r is None):
				return False
			if(r.state == "unavailable"):  # needed, some dropdown field will report as "unavailable" although they don't exist
				if(not(unavailable_is_ok)):
					return False
			return True
		except:
			return False

	async def async_update_playlists(self, now=None):
		self.log_me('debug', "[S] async_update_playlists")
		# Sync playlists from Google Music library #
		if(self._api is None):
			self.log_me('debug', "- no api, exit")
			return
		if self._selects['playlists'] is None:
			self.log_me('debug', "- no playlist select field, exit")
			return

		self._playlist_to_index = {}
		playlists_to_extra = {}
		try:
			try:
				self._playlists = await self.hass.async_add_executor_job(lambda: self._api.get_library_playlists(limit=self._trackLimit))
				self._playlists = self._playlists[:self._trackLimit]  # limit function doesn't really work ... loads at least 25
				self.log_me('debug', " - " + str(len(self._playlists)) + " Playlists loaded")
			except:
				self._api = None
				self.exc()
				return
			idx = -1
			for playlist in self._playlists:
				idx = idx + 1
				name = playlist.get('title', '')
				if len(name) < 1:
					continue
				self._playlist_to_index[name] = idx
				#  the "your likes" playlist won't return a count of tracks
				if not('count' in playlist):
					try:
						extra_info = await self.hass.async_add_executor_job(self._api.get_playlist, playlist['playlistId'])
						self._playlists[idx]['count'] = 25
						if('trackCount' in extra_info):
							if(extra_info['trackCount']):
								self._playlists[idx]['count'] = int(extra_info['trackCount'])
					except:
						if('playlistId' in playlist):
							self.log_me('debug', "- Failed to get_playlist count for playlist ID '" + str(playlist['playlistId']) + "' setting it to 25")
						else:
							self.log_me('debug', "- Failed to get_playlist, no playlist ID")
						self.exc()
						self._playlists[idx]['count'] = 25
				playlists_to_extra[playlist['title']] = playlist['playlistId']

			if(len(self._playlists) == 0):
				self._playlist_to_index["No playlists found"] = 0

			# sort with case-ignore
			playlists = sorted(list(self._playlist_to_index.keys()), key=str.casefold)
			await self.async_update_extra_sensor('playlists', playlists_to_extra)  # update extra sensor
			if self._selects['playlists'] is not None:  # update playlist select
				if input_select.DOMAIN in self._selects['playlists']:
					data = {input_select.ATTR_OPTIONS: list(playlists), ATTR_ENTITY_ID: self._selects["playlists"]}
					await self.hass.services.async_call(input_select.DOMAIN, input_select.SERVICE_SET_OPTIONS, data)
				else:
					await self.hass.data[DOMAIN][self._attr_unique_id]['select_playlists'].async_update()
		except:
			self.exc()
			msg = "Caught error while loading playlist. please log for details"
			data = {"title": "yTubeMediaPlayer error", "message": msg}
			await self.hass.services.async_call("persistent_notification", "create", data)
		self.log_me('debug', "[E] async_update_playlists")


	async def _tracks_to_attribute(self):
		self.log_debug_later("[S] _tracks_to_attribute")
		await self.async_update_extra_sensor('total_tracks', len(self._tracks))
		track_attributes = []
		for track in self._tracks:
			info = self.extract_info(track)
			track_attributes.append(info['track_artist'] + " - " + info['track_name'])
		await self.async_update_extra_sensor('tracks', track_attributes)  # update extra sensor
		
		# fire event to let media card know to update
		event_data = {
			"device_id": self._attr_unique_id,
			"entity_id": self.entity_id,
			"type": "reload_playlist",
		}
		self.hass.bus.async_fire(DOMAIN+"_event", event_data)
		self.log_me('debug', "[E] _tracks_to_attribute")

	async def async_update_extra_sensor(self, attribute, value):
		# update extra sensor
		self.log_debug_later("[S] async_update_extra_sensor")
		self.hass.data[DOMAIN][self._attr_unique_id][attribute] = value
		if(self._init_extra_sensor):
			try:
				await self.hass.data[DOMAIN][self._attr_unique_id]['extra_sensor'].async_update()
			except:
				self.log_me('debug', "Update failed")
				pass
		self.log_me('debug', "[E] async_update_extra_sensor")

	async def async_update_playmode(self, event=None):
		# called from HA when th user changes the input entry, will read selection to membervar
		# Changing the shuffle_mode while music is playing will no longer cause interruptions.
		# Only when shuffle_mode=true the next song will be random.
		# By default, when shuffle_mode = "Shuffle", shuffle=False. However,
		# the _attr_shuffle variable can be changed during playback without interrupting the music.
		self.log_me('debug', "[S] async_update_playmode")
		try:
			if self._selects['repeatmode'] is not None:
				if (_state := self.hass.states.get(self._selects['repeatmode']).state) == STATE_ON:
					_state = RepeatMode.ALL
				await self.async_set_repeat(_state)
		except:
			self.log_me('debug', "- Selection field " + self._selects['repeatmode'] + " not found, skipping")

		try:
			if self._selects['playmode'] is not None:
				if (_playmode := self.hass.states.get(self._selects['playmode']).state) is not None:
					if _playmode in (PLAYMODE_SHUFFLE,PLAYMODE_DIRECT):
						shuffle = False
					else:
						shuffle = True
					self._shuffle_mode = _playmode
				await self.async_set_shuffle(shuffle)  # The non-existent set_shuffle method was incorrectly called previously.
				self.log_me('debug', f"- Playmode: {_playmode}")
		except:
			self.log_me('debug', "- Selection field " + self._selects['playmode'] + " not found, skipping")

		self.log_me('debug', "[E] async_update_playmode")


	async def async_play(self):
		self.log_me('debug', f"_play,shuffle:{self.shuffle},shuffle_mode:{self._shuffle_mode}")
		self._next_track_no = 0
		if self.shuffle:
			await self.async_get_track(keep_track_no=False)
		else:
			await self.async_get_track()

	async def async_get_track(self, event=None, retry=3, auto_advance=False, keep_track_no=True):
		self.log_me('debug', "[S] async_get_track")
		# Get a track and play it from the track_queue.
		# grab next track from prefetched lis
		_track = None
		# get next track nr (randomly or by increasing).
		if auto_advance:  # auto_advance=true means that the call is coming from automatic playback of the next track.
			if self.repeat == RepeatMode.ONE:
				self.log_me('debug', "Single track loop.")
			elif self.shuffle:
				self._next_track_no = random.randrange(len(self._tracks)) - 1
				self.log_me('debug', "Random track.")
			else:
				self._next_track_no = self._next_track_no + 1
				self.log_me('debug', "- Playing track nr " + str(self._next_track_no + 1) + " / " + str(len(self._tracks)))  # technically + 1 is wrong, but is still less confusing
				if self._next_track_no >= len(self._tracks):
				# we've reached the end of the playlist
					if(self.repeat == RepeatMode.ALL):
						# call PLAY_MEDIA with the same arguments
						# return await self.async_play_media(media_type=self._attributes['_media_type'], media_id=self._attributes['_media_id'])
						self._next_track_no = 0  # This maybe better.
					else:
						_LOGGER.info("- End of playlist and repeat mode is off")
						await self.async_turn_off_media_player()
						return
		elif keep_track_no:
			self.log_me('debug', "The track_no has already been specified,do not change it.")
		elif self.shuffle:
			self._next_track_no = random.randrange(len(self._tracks)) - 1
			self.log_me('debug', f"auto_advance={auto_advance},keep_track_no={keep_track_no},repeat={self.repeat},shuffle_mode={self._shuffle_mode}")
			self.log_me('debug', "Press the next/pref button and shuffle is true, play random track.")
		else:
			self.log_me('debug', f"Uncaught Situation,auto_advance={auto_advance},keep_track_no={keep_track_no},repeat={self.repeat},shuffle_mode={self._shuffle_mode}")


		# get track from array of _trackS
		try:
			_track = self._tracks[self._next_track_no]
		except:
			_LOGGER.error("- Out of range! Number of tracks in track_queue == (%s)", len(self._tracks))
			self._api = None
			await self.async_turn_off_media_player()
			return
		if _track is None:
			_LOGGER.error("- _track is None!")
			await self.async_turn_off_media_player()
			return

		# make sure there is a videoId
		if not('videoId' in _track):
			_LOGGER.error("- Failed to get ID for track: (%s)", _track)
			_LOGGER.error(_track)
			if retry < 1:
				await self.async_turn_off_media_player()
				return
			return await self.async_get_track(retry=retry - 1, auto_advance=auto_advance, keep_track_no=keep_track_no)

		# updates attributes
		self._attributes['current_track'] = self._next_track_no
		self._attributes['videoId'] = _track['videoId']
		if('likeStatus' in _track):
			self._attributes['likeStatus'] = _track['likeStatus']
			if(self._like_in_name):
				self._attr_name = self._org_name + " - " + str(_track['likeStatus'])
		else:
			self._attributes['likeStatus'] = ""
			if(self._like_in_name):
				self._attr_name = self._org_name
		# this will quickly update the information although the thumbnail might not super great, we'll update that later
		info = self.extract_info(_track)
		self._track_album_name = info['track_album_name']
		self._track_artist_cover = info['track_artist_cover']
		self._track_name = info['track_name']
		self._track_artist = info['track_artist']
		self._track_album_cover = info['track_album_cover']
		self._track_album_id = info['track_album_id']
		self.async_schedule_update_ha_state()

		# Get the stream URL and play on media_player
		_url = await self.async_get_url(_track['videoId'])
		if(_url == ""):
			if retry < 1:
				self.log_me('debug', "- get track failed to return URL, turning off")
				await self.async_turn_off_media_player()
				return
			else:
				_LOGGER.error("- Retry with: (%i)", retry)
			return await self.async_get_track(retry=retry - 1, auto_advance=auto_advance, keep_track_no=keep_track_no)

		# proxy playback, needed e.g. for sonos
		try:
			if(self._proxy_url != "" and self._proxy_path != "" and self._proxy_url != " " and self._proxy_path != " "):
				p1 = datetime.datetime.now()
				_proxy_url = await self.hass.async_add_executor_job(lambda:  urlopen(Request(_url, headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'})))
				_proxy_file = open(os.path.join(self._proxy_path, PROXY_FILENAME), 'wb')
				_proxy_url_content = await self.hass.async_add_executor_job(_proxy_url.read)
				await self.hass.async_add_executor_job(_proxy_file.write, _proxy_url_content)
				if(self._proxy_url.endswith('/')):
					self._proxy_url = self._proxy_url[:-1]
				_url = self._proxy_url + "/" + PROXY_FILENAME
				t = (datetime.datetime.now() - p1).total_seconds()
				self.log_me('debug', "- proxy loading time: " + str(t) + " sec")
		except:
			_LOGGER.error("The proxy method hit an error, turning off")
			self.exc()
			await self.async_turn_off_media_player()
			return

		# start playback
		self._state = STATE_PLAYING
		self._playing = True
		self.async_schedule_update_ha_state()
		self._last_auto_advance = datetime.datetime.now()  # avoid auto_advance
		data = {
			ATTR_MEDIA_CONTENT_ID: _url,
			ATTR_MEDIA_CONTENT_TYPE: MediaType.MUSIC,
			ATTR_ENTITY_ID: self._remote_player,
			"extra": {
				"metadata": {
					"metadataType": 3,
					"title": self._track_name,
					"artist": self._track_artist,
					"images": [
						{
							"url": self._track_album_cover,
						}
					]
				}
			}
		}
		self.log_me('debug', "- forwarding url to player " + str(self._remote_player))
		await self.hass.services.async_call(DOMAIN_MP, SERVICE_PLAY_MEDIA, data)

		# get lyrics and more info after playback started
		await self.async_update_extra_sensor('lyrics', 'No lyrics available')


		try:
			l_id = await self.hass.async_add_executor_job(self._api.get_watch_playlist, _track['videoId'])
			if 'lyrics' in l_id:
				if(l_id['lyrics'] is not None):
					lyrics = await self.hass.async_add_executor_job(self._api.get_lyrics, l_id['lyrics'])
					await self.async_update_extra_sensor('lyrics', lyrics['lyrics'])
			# the nice thing about this 'get_watch_playlist' is that one gets also extra info about the current track
			# like a better thumbnail. The original thumbnail from get_playlist has poor quality.
			for vid in l_id['tracks']:
				if(('videoId' in vid) and (vid['videoId'] == _track['videoId'])):
					info = self.extract_info(vid)
					if(self._track_album_cover != info['track_album_cover']):
						self._track_album_cover = info['track_album_cover']
						self.async_schedule_update_ha_state()
					break
		except:
			pass
		async_call_later(self.hass, 15, self.async_sync_player)
		self.log_me('debug', "[E] async_get_track")


	async def async_get_url(self, videoId=None, retry=60):
		self.log_me('debug', "[S] async_get_url")
		if(videoId is None):
			self.log_me('debug', "videoId was None")
			return ""
		_url = await self.async_get_url_self(videoId,retry)

		# check url
		if(_url != ""):
			r = await self.hass.async_add_executor_job(requests.head, _url)
			if(r.status_code == 403):
				self.log_me('error', "- self decoded url return 403 status code, attempt "+str(retry)+"/60")
				_url = ""
		
		if(_url == ""):
			_url = await self.async_get_url_pytube(videoId)
		
		# check url
		if(_url != ""):
			r = await self.hass.async_add_executor_job(requests.head, _url)
			if(r.status_code == 403 or r.status_code == 410):
				self.log_me('error', "- self decoded url return 403 status code, attempt "+str(retry)+"/60")
				_url = ""

				if(retry>0):
					self._api = None
					self.log_me('debug', "- relogin to fresh cookie and try again")
					self.async_check_api() 
					return await self.async_get_url(videoId, retry-1)
				else:
					self.log_me('debug', "- giving up, maybe pyTube can help")
					_url = ""

		self.log_me('debug', "[E] async_get_url")
		return _url


	async def async_get_url_self(self, videoId=None, retry=60):
		self.log_me('debug', "[S] async_get_url_self")
		_url = ""
		await self.async_check_api()
		try:
			stop = False
			self.log_me('debug', "- try to find URL on our own")
			try:
				response = await self.hass.async_add_executor_job(lambda: self._api.get_song(videoId, self._signatureTimestamp))
			except:
				self._api = None
				self.log_me('error', 'self.get_song(videoId=' + str(videoId) + ',signatureTimestamp=' + str(self._signatureTimestamp) + ')')
				self.exc()
				return
			streamingData = []
			if 'streamingData' in response:
				if('adaptiveFormats' in response['streamingData']):
					streamingData += response['streamingData']['adaptiveFormats']
				if('formats' in response['streamingData']):  # backup, not sure if that is ever needed, or if adaptiveFormats are always present
					streamingData += response['streamingData']['formats']
				if(len(streamingData) == 0):
					self.log_me('error', 'No adaptiveFormat and no formats found')
					self.log_me('error', 'self.get_song(videoId=' + str(videoId) + ',signatureTimestamp=' + str(self._signatureTimestamp) + ')')
					stop = True
			else:
				stop = True

			if(not(stop)):
				streamId = 0
				found_quality = -1
				quality_mapper = {'AUDIO_QUALITY_LOW': 1, 'AUDIO_QUALITY_MEDIUM': 2, 'AUDIO_QUALITY_HIGH': 3}
				# try to find valid audio streams
				valid_streams = []
				for i, stream in enumerate(streamingData):
					#self.log_me('debug', 'found stream')
					#self.log_me('error',stream)
					if('audioQuality' in stream):
						# self.log_me('error', '- found stream with audioQuality ' + stream['audioQuality'] + ' (' + str(i) + ')')
						# store only stream with better quality, accept 0 once
						stream['audioQuality'] = quality_mapper.get(stream['audioQuality'], 0)
						valid_streams.append(stream)
					elif(found_quality == -1):  # only search for mimetype if we didn't find a quality stream before
						if('mimeType' in stream):
							if(stream['mimeType'].startswith('audio/mp4')):
								self.log_me('debug', '- found audio/mp4 audiostream (' + str(i) + ')')
								stream['audioQuality'] = quality_mapper.get(stream['audioQuality'], 0)
								valid_streams.append(stream)
							elif(stream['mimeType'].startswith('audio')):
								self.log_me('debug', '- found audio audiostream (' + str(i) + ')')
								stream['audioQuality'] = quality_mapper.get(stream['audioQuality'], 0)
								valid_streams.append(stream)
				
				# try to find best audio only stream, but accept lower quality if we have to
				valid_streams.sort(key=lambda x: x['bitrate'], reverse=True)
				self.log_me('debug', "found "+str(len(valid_streams))+" streams")
				# remove all streams with too high bitrates
				if(self._maxDatarate>0):
					for stream in valid_streams:
						if(stream['bitrate']>self._maxDatarate):
							if(len(valid_streams)>1):
								valid_streams.remove(stream)
								self.log_me('debug', '- removed stream with too high bitrate of '+str(stream['bitrate']))
							else:
								self.log_me('debug', '- preseved stream, too high quality but last available stream')

				if(retry<20):
					streamId = min(3,len(valid_streams))
				elif(retry<30):
					streamId = min(2,len(valid_streams))
				elif(retry<40):
					streamId = min(1,len(valid_streams))
				else:
					streamId = 0
				
				self.log_me('debug', 'Using stream '+str(streamId)+"/"+str(len(valid_streams))+", bitrate:"+str(valid_streams[streamId]['bitrate']))
				# self.log_me('debug', '- using stream ' + str(streamId))
				if(valid_streams[streamId].get('url') is None):
					sigCipher_ch = valid_streams[streamId]['signatureCipher']
					sigCipher_ex = sigCipher_ch.split('&')
					res = dict({'s': '', 'url': ''})
					for sig in sigCipher_ex:
						for key in res:
							if(sig.find(key + "=") >= 0):
								res[key] = unquote(sig[len(key + "="):])
					# I'm just not sure if the original video from the init will stay online forever
					# in case it's down the player might not load and thus we won't have a javascript loaded
					# so if that happens: we try with this url, might work better (at least the file should be online)
					# the only trouble i could see is that this video is private and thus also won't load the player ..
					if(self._js == "" or retry<60):
						self.log_me('debug', "- reloading cipher from current video")
						await self.async_get_cipher(videoId)
					
					#stream_manifest = extract.apply_descrambler(self.streaming_data)
					##try:
            		#extract.apply_signature(stream_manifest, self.vid_info, self.js)
        			##except exceptions.ExtractError:
					##	extract.apply_signature(stream_manifest, self.vid_info, self.js)
					if "signature" in res['url'] or ("s" not in res and ("&sig=" in res['url'] or "&lsig=" in res['url'])):
						# For certain videos, YouTube will just provide them pre-signed, in
						# which case there's no real magic to download them and we can skip
						# the whole signature descrambling entirely.
						self.log_me('error',"signature found, skip decipher")
						_url = res['url']
					else:
						self.log_me('error',"signature not found, decoding")
						signature = self._cipher.get_signature(ciphered_signature=res['s'])
						_url = res['url'] + "&sig=" + signature
					self.log_me('debug', "- self decoded URL via cipher")
					
				else:
					_url = valid_streams[streamId]['url']
					self.log_me('debug', "- found URL in api data")

		except Exception:
			_LOGGER.error("- Failed to get own(!) URL for track, further details below. Will not try YouTube method")
			_LOGGER.error(traceback.format_exc())
			_LOGGER.error(videoId)
		self.log_me('debug', "[E] async_get_url")
		return _url

	async def async_get_url_pytube(self, videoId=None):
		# backup: run youtube stack, only if we failed
		self.log_me('debug', "[S] async_get_url_pytube")
		_url = ""
		try:
			streamingData = await self.hass.async_add_executor_job(lambda: YouTube("https://www.youtube.com/watch?v=" + videoId))
			streams = await self.hass.async_add_executor_job(lambda: streamingData.streams)
			streams_audio = streams.filter(only_audio=True)
			if(len(streams_audio) > 0):
				_url = streams_audio.order_by('abr').last().url
			else:
				_url = streams.order_by('abr').last().url

		except Exception as err:
			# _LOGGER.error(traceback.format_exc())
			_LOGGER.error("- Failed to get URL with YouTube methode")
			_LOGGER.error(err)
			return ""
		self.log_me('debug', "[E] async_get_url_pytube")
		return _url


	async def async_play_media(self, media_type, media_id, _player=None, **kwargs):
		self.log_me('debug', "[S] play_media, media_type: " + str(media_type) + ", media_id: " + str(media_id))

		self._started_by = "Browser"
		self._attributes['_media_type'] = media_type
		self._attributes['_media_id'] = media_id

		if(not(media_type in [CONF_RECEIVERS,CHANNEL_VID_NO_INTERRUPT])):  # don't to this for the speaker configuration (it will fail) and also skip it for the vid no interrupt
			if(not(await self.async_prepare_play())):
				return

		# Update player if we got an input
		if _player is not None:
			await self.async_update_remote_player(remote_player=_player)
			if self._selects['speakers'] is not None:
				if input_select.DOMAIN in self._selects['speakers']:
					_select = input_select
				else:
					_select = select
				data = {_select.ATTR_OPTION: _player, ATTR_ENTITY_ID: self._selects['speakers']}
				await self.hass.services.async_call(_select.DOMAIN, _select.SERVICE_SELECT_OPTION, data)

		# load Tracks depending on input
		try:
			crash_extra = ''
			self._attributes['current_playlist_title'] = ""
			if(media_type == MediaType.PLAYLIST):
				crash_extra = 'get_playlist(playlistId=' + str(media_id) + ')'
				if(media_id == ALL_LIB_TRACKS):
					self._tracks = await self.hass.async_add_executor_job(lambda: self._api.get_library_songs(limit=self._trackLimit))
					self._attributes['current_playlist_title'] = ALL_LIB_TRACKS_TITLE
				else:
					playlist_info = await self.hass.async_add_executor_job(lambda: self._api.get_playlist(media_id, limit=self._trackLimit))
					self._tracks = playlist_info['tracks'][:self._trackLimit]  # limit function doesn't really work ... seems like
					self._attributes['current_playlist_title'] = str(playlist_info['title'])
			elif(media_type == MediaType.ALBUM):
				crash_extra = 'get_album(browseId=' + str(media_id) + ')'
				if media_id[:7] == "OLAK5uy": #Sharing over Android app sends 'bad' album id. Checking and converting.
					media_id = await self.hass.async_add_executor_job(self._api.get_album_browse_id, media_id)
				self._tracks = await self.hass.async_add_executor_job(self._api.get_album, media_id)  # no limit needed
				thumbnail = find_thumbnail(self._tracks)
				self._tracks = self._tracks['tracks'][:self._trackLimit]  # limit function doesn't really work ... seems like
				for i in range(0, len(self._tracks)):
					self._tracks[i].update({'album': {'id': media_id}})
					self._tracks[i].update({'thumbnails': [{'url': thumbnail}]})
			elif(media_type == MediaType.TRACK):
				crash_extra = 'get_song(videoId=' + str(media_id) + ',signatureTimestamp=' + str(self._signatureTimestamp) + ')'
				self._tracks = [await self.hass.async_add_executor_job(lambda: self._api.get_song(media_id, self._signatureTimestamp))]  # no limit needed
				self._tracks[0] = self._tracks[0]['videoDetails']
			elif(media_id == HISTORY):
				crash_extra = 'get_history()'
				self._tracks = await self.hass.async_add_executor_job(self._api.get_history)  # no limit needed
			elif(media_id == USER_TRACKS):
				crash_extra = 'get_library_upload_songs(limit=999)'
				self._tracks = await self.hass.async_add_executor_job(self._api.get_library_upload_songs, self._trackLimit)
				self._tracks = self._tracks[:self._trackLimit]  # limit function doesn't really work ... seems like
			elif(media_type == CHANNEL):
				if(self._legacyRadio):
					# get original playlist from the media_id
					crash_extra = 'get_playlist(playlistId=' + str(media_id) + ',limit=' + str(self._trackLimit) + ')'
					self._tracks = await self.hass.async_add_executor_job(lambda: self._api.get_playlist(media_id, limit=self._trackLimit))
					self._tracks = self._tracks['tracks']
					# select on track randomly
					if(isinstance(self._tracks, list)):
						if(len(self._tracks) > 0):
							if(len(self._tracks) > 1):
								r_track = self._tracks[random.randrange(0, len(self._tracks) - 1)]
								info = self.extract_info(r_track)
								self._attributes['_radio_based'] = info['track_artist'] + " - " + info['track_name']
							else:
								r_track = self._tracks[0]
							# get a 'channel' based on that random track
							crash_extra += ' ... get_watch_playlist(videoId=' + str(r_track['videoId']) + ',limit=' + str(self._trackLimit) + ')'
							self._tracks = await self.hass.async_add_executor_job(lambda: self._api.get_watch_playlist(r_track['videoId'], limit=self._trackLimit))
							self._tracks = self._tracks['tracks'][:self._trackLimit]  # limit function doesn't really work ... seems like
				else:
					crash_extra = 'get_watch_playlist(playlistId=RDAMPL' + str(media_id) + ')'
					self._tracks = await self.hass.async_add_executor_job(lambda: self._api.get_watch_playlist(playlistId="RDAMPL" + str(media_id), limit=self._trackLimit))
					self._tracks = self._tracks['tracks'][:self._trackLimit]  # limit function doesn't really work ... seems like
				self._started_by = "UI"  # technically wrong, but this will enable auto-reload playlist once all tracks are played
				playlist_info = await self.hass.async_add_executor_job(lambda: self._api.get_playlist(media_id, limit=self._trackLimit))
				self._attributes['current_playlist_title'] = "Radio of " + str(playlist_info['title'])
			elif(media_type == CHANNEL_VID or media_type==CHANNEL_VID_NO_INTERRUPT):
				crash_extra = 'get_watch_playlist(videoId=RDAMVM' + str(media_id) + ')'
				self._tracks = await self.hass.async_add_executor_job(lambda: self._api.get_watch_playlist(videoId=str(media_id), limit=self._trackLimit))
				self._tracks = self._tracks['tracks'][:self._trackLimit]  # limit function doesn't really work ... seems like
				self._started_by = "UI"  # technically wrong, but this will enable auto-reload playlist once all tracks are played
				video_info = await self.hass.async_add_executor_job(lambda: self._api.get_song(media_id, self._signatureTimestamp))  # no limit needed
				title = "unknown title"
				if("videoDetails" in video_info):
					if("title" in video_info["videoDetails"]):
						title = video_info['videoDetails']['title']
				self._attributes['current_playlist_title'] = "Radio of " + str(title)
			elif(media_type == USER_ALBUM):
				crash_extra = 'get_library_upload_album(browseId=' + str(media_id) + ')'
				self._tracks = await self.hass.async_add_executor_job(lambda: self._api.get_library_upload_album(media_id))
				self._tracks = self._tracks['tracks'][:self._trackLimit]  # limit function here not supported
			elif(media_type in (USER_ARTIST, USER_ARTIST_2)):  # Artist -> Track or Artist [-> Album ->] Track
				crash_extra = 'get_library_upload_artist(browseId=' + str(media_id) + ')'
				self._tracks = await self.hass.async_add_executor_job(lambda: self._api.get_library_upload_artist(media_id, limit=self._trackLimit))
				self._tracks = self._tracks[:self._trackLimit]  # limit function doesn't really work ... seems like
			elif(media_type == CONF_RECEIVERS):  # a bit funky, but this enables us to select the player via the media browser ..
				await self.async_select_source(media_id)
			elif(media_type == CUR_PLAYLIST_COMMAND):  # a bit funky, but this enables us to just in the current playlist
				await self.async_call_method(SERVICE_CALL_GOTO_TRACK, media_id)
				return  # INSTANT leave after this call to prevent any further shuffeling etc
			else:
				self.log_me('debug', "- error during fetching play_media, turning off")
				await self.async_turn_off()
		except:
			self._api = None
			self.log_me('debug', crash_extra)
			self.exc()
			await self.async_turn_off_media_player()
			return
		self.log_me('debug', crash_extra)

		# mode "Shuffle" and "Shuffle Random" shuffle the playlist after generation, but only if shuffle is active
		if(isinstance(self._tracks, list)):
			if(self._attr_shuffle): 
				if self._shuffle_mode in (PLAYMODE_SHUFFLE,PLAYMODE_SHUFFLE_RANDOM) and len(self._tracks) > 1:
					random.shuffle(self._tracks)
					self.log_me('debug', "- shuffle new tracklist")
				if(len(self._tracks) == 0):
					_LOGGER.error("tracklist with 0 tracks loaded, existing")
					await self.async_turn_off()
					return
		else:
			self.log_me('error', "Tracklist not a list .. turning off")
			await self.async_turn_off()
			return

		# limit list now
		if(self._trackLimitUser > 0):
			self.log_me('debug', "Limiting playlist from " + str(len(self._tracks)) + " to " + str(self._trackLimitUser) + " items")
			self._tracks = self._tracks[:self._trackLimitUser]
		await self._tracks_to_attribute()

		# grab track from tracks[] and forward to remote player
		if(media_type != CHANNEL_VID_NO_INTERRUPT):
			await self.async_play()
		self.log_me('debug', "[E] play_media")


	async def async_media_play(self, entity_id=None, old_state=None, new_state=None, **kwargs):
		self.log_me('debug', "[S] media_play")

		# Send play command.
		if self._state == STATE_PAUSED:
			self._state = STATE_PLAYING
			self.async_schedule_update_ha_state()
			data = {ATTR_ENTITY_ID: self._remote_player}
			await self.hass.services.async_call(DOMAIN_MP, 'media_play', data)
		else:
			await self.async_play()
		self.log_me('debug', "[E] media_play")


	async def async_media_pause(self, **kwargs):
		self.log_me('debug', "media_pause")
		# Send media pause command to media player
		self._state = STATE_PAUSED
		self._media_position = None  # set it to none, otherwise player like mini-media-player will continue
		# _LOGGER.error(" PAUSE ")
		self.async_schedule_update_ha_state()
		data = {ATTR_ENTITY_ID: self._remote_player}
		await self.hass.services.async_call(DOMAIN_MP, 'media_pause', data)

	async def async_media_play_pause(self, **kwargs):
		self.log_me('debug', "media_play_pause")
		# Simulate play pause media player.
		if self._state == STATE_PLAYING:
			self._allow_next = False
			await self.async_media_pause()
		elif(self._state == STATE_PAUSED):
			self._allow_next = False
			await self.async_media_play()

	async def async_media_previous_track(self, **kwargs):
		# Send the previous track command.
		if self._playing:
			self._allow_next = False
			self._ignore_next_remote_pause_state = True	# RobinR1, OwnTone compatibility
			if self.shuffle:
				await self.async_get_track(keep_track_no=False)
			else:
				self._next_track_no = max(self._next_track_no - 1, 0)
				await self.async_get_track()

	async def async_media_next_track(self, **kwargs):
		# Send next track command.
		if self._playing:
			self._allow_next = False
			self._ignore_next_remote_pause_state = True	# RobinR1, OwnTone compatibility
			if self.shuffle:
				await self.async_get_track(keep_track_no=False)
			else:
				self._next_track_no = self._next_track_no + 1
				if self._next_track_no >= len(self._tracks):
					self._next_track_no = 0
				await self.async_get_track()

	async def async_media_stop(self, **kwargs):
		# Send stop command.
		self.log_me('debug', "async_media_stop")
		self._state = STATE_IDLE
		self._playing = False
		self._track_artist = None
		self._track_album_name = None
		self._track_name = None
		self._track_album_cover = None
		self.async_schedule_update_ha_state()
		if('player' in kwargs):
			self.log_me('debug', "- player found")
			data = {ATTR_ENTITY_ID: kwargs.get('player')}
		else:
			data = {ATTR_ENTITY_ID: self._remote_player}
		await self.hass.services.async_call(DOMAIN_MP, 'media_stop', data)
		self.log_me('debug', "- async_media_stop -> " + self._remote_player)

	async def async_media_seek(self, position):
		# Seek the media to a specific location.
		self.log_me('debug', "seek: " + str(position))
		self._ignore_next_remote_pause_state = True			# RobinR1, OwnTone compatibility
		data = {ATTR_ENTITY_ID: self._remote_player, 'seek_position': position}
		await self.hass.services.async_call(DOMAIN_MP, 'media_seek', data)

	async def async_set_shuffle(self, shuffle):
		# Only implement the function which the HA media_player entity built-in, without affecting the _shuffle_mode and dropdown options.
		# if shuffle is true,the next song should be random.
		# shuffle_mode="Shuffle" means that when starting a playlist, the original order is randomized, but it does not imply shuffle=true.
		if self.shuffle != shuffle:
			self.log_me('debug', f"set_shuffle: {str(shuffle)}")
			self._attr_shuffle = shuffle  # True / False
			self.async_schedule_update_ha_state()


	async def async_set_volume_level(self, volume):
		# Set volume level.
		self._volume = round(volume, 2)
		data = {ATTR_ENTITY_ID: self._remote_player, 'volume_level': self._volume}
		await self.hass.services.async_call(DOMAIN_MP, 'volume_set', data)
		self.async_schedule_update_ha_state()

	async def async_volume_up(self, **kwargs):
		# Volume up the media player.
		newvolume = min(self._volume + 0.05, 1)
		await self.async_set_volume_level(newvolume)

	async def async_volume_down(self, **kwargs):
		# Volume down media player.
		newvolume = max(self._volume - 0.05, 0.01)
		await self.async_set_volume_level(newvolume)

	async def async_mute_volume(self, mute):
		# Send mute command.
		if self._is_mute is False:
			self._is_mute = True
		else:
			self._is_mute = False
		self.async_schedule_update_ha_state()
		data = {ATTR_ENTITY_ID: self._remote_player, "is_volume_muted": self._is_mute}
		await self.hass.services.async_call(DOMAIN_MP, 'volume_mute', data)

	async def async_call_method(self, command=None, parameters=None):
		self.log_me('debug', 'START async_call_method')
		all_params = []
		if parameters:
			for parameter in parameters:
				all_params.append(parameter)
		self.log_me('debug', command)
		self.log_me('debug', parameters)
		if(command == SERVICE_CALL_RATE_TRACK):
			if(len(all_params) >= 1):
				await self.async_rate_track(rating=all_params[0])
		elif(command == SERVICE_CALL_INTERRUPT_START):
			if(self._state not in (STATE_PLAYING, STATE_PAUSED)):
				self._interrupt_data = None
				return
			await self.async_update_remote_player()
			# _LOGGER.error(self._remote_player)
			t = self.hass.states.get(self._remote_player)
			# _LOGGER.error(t)
			self._interrupt_data = dict()
			if(all(a in t.attributes for a in ('media_position', 'media_position_updated_at', 'media_duration'))):
				now = datetime.datetime.now(datetime.timezone.utc)
				delay = now - t.attributes['media_position_updated_at']
				pos = delay.total_seconds() + t.attributes['media_position']
				if pos < t.attributes['media_duration']:
					self._interrupt_data['pos'] = pos
			# _LOGGER.error(self._interrupt_data)
			# _LOGGER.error(self._remote_player)
			self._interrupt_data['player'] = self._remote_player
			# _LOGGER.error(self._interrupt_data)
			await self.async_media_stop(player=self._remote_player)
			if(self._untrack_remote_player is not None):
				try:
					# _LOGGER.error("calling untrack")
					self._untrack_remote_player()
				except:
					# _LOGGER.error("untrack failed!!")
					pass
				self._untrack_remote_player = None

		elif(command == SERVICE_CALL_INTERRUPT_RESUME):
			if(self._interrupt_data is None):
				return
			if('player' in self._interrupt_data):
				await self.async_update_remote_player(remote_player=self._interrupt_data['player'])
				self._untrack_remote_player = async_track_state_change_event(self.hass, self._remote_player, self.async_sync_player)
				self._interrupt_data['player'] = None
			await self.async_get_track()
			if('pos' in self._interrupt_data):
				player = self.hass.states.get(self._remote_player)
				if(player.attributes['supported_features'] | MediaPlayerEntityFeature.SEEK):
					data = {'seek_position': self._interrupt_data['pos'], ATTR_ENTITY_ID: self._remote_player}
					await self.hass.services.async_call(DOMAIN_MP, media_player.SERVICE_MEDIA_SEEK, data)
				self._interrupt_data['pos'] = None
		elif(command == SERVICE_CALL_RELOAD_DROPDOWNS):
			await self.async_update_selects()
		elif(command == SERVICE_CALL_OFF_IS_IDLE):  # needed for the MPD and OwnTone server but for nobody else
			self._x_to_idle = STATE_OFF
			self.log_me('debug', "Setting x_is_idle to State Off")
		elif(command == SERVICE_CALL_PAUSED_IS_IDLE):  # needed for the Sonos but for nobody else
			self._x_to_idle = STATE_PAUSED
			self.log_me('debug', "Setting x_is_idle to State Paused")
		elif(command == SERVICE_CALL_IGNORE_PAUSED_ON_MEDIA_CHANGE):		# RobinR1, OwnTone compatibility
			self._ignore_paused_on_media_change = True			# RobinR1, OwnTone compatibility
			self.log_me('debug', "Setting to ignore remote player Paused state on Next/Prev track and Seek")
		elif(command == SERVICE_CALL_DO_NOT_IGNORE_PAUSED_ON_MEDIA_CHANGE):	# RobinR1, OwnTone compatibility
			self._ignore_paused_on_media_change = False			# RobinR1, OwnTone compatibility
			self.log_me('debug', "Setting to NOT ignore remote player Paused state on Next/Prev track and Seek")
		elif(command == SERVICE_CALL_IDLE_IS_IDLE): # reset idle detection to default behaviour
			self._x_to_idle = None
			self.log_me('debug', "Resetting x_is_idle")
		elif(command == SERIVCE_CALL_DEBUG_AS_ERROR):
			self._debug_as_error = True
			self.log_me('debug', "Posting debug messages as error until restart")
		elif(command == SERVICE_CALL_LIKE_IN_NAME):
			self._like_in_name = True
			self._attr_name = self._org_name + " - " + str(self._attributes['likeStatus'])
			self.log_me('debug', "Showing like status in name until restart")
		elif(command == SERVICE_CALL_GOTO_TRACK):
			self.log_me('debug', "Going to Track " + str(parameters[0]) + ".")
			self._next_track_no = min(max(int(parameters[0]) - 1, 0), len(self._tracks) - 1)
			prev_shuffle = self._attr_shuffle  # store current shuffle setting
			self._attr_shuffle = False  # set false, otherwise async_get_track will override next_track
			await self.async_get_track()
			self._attr_shuffle = prev_shuffle  # restore
		elif(command == SERVICE_CALL_APPEND_TRACK):
			self.log_me('debug', "Adding track " + str(parameters[0]) + " at position " + str(parameters[1]))
			if(len(parameters)==2 and parameters[1].isnumeric()):
				add_track = await self.hass.async_add_executor_job(lambda: self._api.get_song(parameters[0], self._signatureTimestamp))  # no limit needed
			else:
				self.log_me('debug', str(parameters[1]) + " is not numeric, or not exactly 2 parameters given")
			# how to check
			# I don't know why, but the format of get_song is very differnt, so we fix at least author and thumbnail to make it lookalike
			add_track['videoDetails']['artists'] = [{'name': add_track['videoDetails']['author'], 'id': ''}]
			add_track['videoDetails']['thumbnails'] = add_track['videoDetails']['thumbnail']['thumbnails']
			self._tracks.insert(int(parameters[1]),add_track['videoDetails'])

			await self._tracks_to_attribute()
		elif(command == SERVICE_CALL_MOVE_TRACK):
			self.log_me('debug', "Moving track " + str(parameters[0]) + " to position " + str(parameters[1]))
			if(parameters[0].isnumeric() and (parameters[1].isnumeric() or parameters[1]=="-1")):
				add_track = self._tracks[int(parameters[0])]
				self._tracks.remove(add_track)
				if(parameters[1].isnumeric()):
					self._tracks.insert(int(parameters[1]),add_track)
				await self._tracks_to_attribute()
			else:
				self.log_me('debug', str(parameters[0]) + " or " + str(parameters[1]) + " is not numeric, not moving tracks")
		else:
			self.log_me('error', "Command " + str(command) + " not implimented")
		self.log_me('debug', "[E] async_call_method")


	async def async_search(self, query="", filter=None, limit=20):
		self.log_debug_later("[S] async_search")
		if(filter is None or filter in {'albums', 'playlists', 'songs', 'artists'}):
			# store data for media_browser
			self._search['query'] = query
			self._search['filter'] = filter
			self._search['limit'] = limit

			if(self._init_extra_sensor):
				search_results = list()
				# execute search and store informtion for the extra sensor
				media_all = await self.hass.async_add_executor_job(lambda: self._api.search(query=query, filter=filter, limit=limit))
				self.log_me('debug',media_all)
				supported_media = [['song', 'videoId'], ['playlist', 'browseId'], ['album', 'browseId'], ['artist','browseId']]
				for media_type in supported_media:
					for result in media_all:
						if result['resultType'] == media_type[0]:
							if not('title' in result):
								if 'artist' in result:
									result['title'] = result['artist']
								elif 'artists' in result:  # handle top result
									result['title'] = result['artists'][0]['name']
									result['browseId'] = result['artists'][0]['id']
							if ('videoId' in result) or ('browseId' in result):
								search_results.append({'type': media_type[0], 'title': result['title'], 'id': result[media_type[1]], 'thumbnail': result['thumbnails'][-1]['url']})

				try:
					await self.async_update_extra_sensor('search', search_results)
				except:
					pass

		else:
			data = {"title": "yTubeMediaPlayer error", "message": "Please use a valid filter: 'albums', 'playlists', 'songs'"}
			await self.hass.services.async_call("persistent_notification", "create", data)
		self.log_me('debug', "[E] async_search")


	async def async_add_to_playlist(self, song_id="", playlist_id=""):
		await self.async_modify_playlist(song_id,playlist_id,mode="add")

	async def async_remove_from_playlist(self, song_id="", playlist_id=""):
		await self.async_modify_playlist(song_id,playlist_id,mode="remove")

	async def async_modify_playlist(self, song_id="", playlist_id="", mode="add"):
		self.log_debug_later("[S] async_modify_playlist")
		if(song_id == ""):
			if(self._attributes['videoId'] != ""):
				song_id = self._attributes['videoId']
			else:
				self.log_me('error', "no song_id given, but also currently not playing, so I don't know what to add/remove")
		if(song_id != "" and playlist_id == ""):
			if(self._attributes['_media_type'] in [MediaType.PLAYLIST, CHANNEL]):
				playlist_id = self._attributes['_media_id']
			else:
				self.log_me('error', "No playlist Id provided and the current playmode isn't 'playlist' nor 'channel', so I don't know where to add/remove the track")
		if(song_id != "" and playlist_id != ""):
			# self.log_me('debug', "add_playlist_items(playlistId=" + playlist_id + ", videoIds=[" + song_id + "]))")
			if(playlist_id == "LM"):
				if(mode=="add"):
					await self.async_call_method(command=SERVICE_CALL_RATE_TRACK, parameters=[SERVICE_CALL_THUMB_UP])
					res = 'song added by liking it'
				else:
					await self.async_call_method(command=SERVICE_CALL_RATE_TRACK, parameters=[SERVICE_CALL_THUMB_DOWN])
					res = 'song removed by dis-liking it'
			else:
				if(mode=="add"):
					try:
						res = await self.hass.async_add_executor_job(lambda: self._api.add_playlist_items(playlistId=str(playlist_id), videoIds=[str(song_id)]))
						res = 'song added'
					except:
						res = 'You can\'t add songs to this playlist (are you the owner?), requrest failed'
				else:
					try:
						extra_info = await self.hass.async_add_executor_job(self._api.get_playlist, str(playlist_id))
						res = 'song not found in playlist'
						if('tracks' in extra_info):
							for track in extra_info['tracks']:
								if track['videoId'] == song_id:
									await self.hass.async_add_executor_job(lambda: self._api.remove_playlist_items(playlistId=str(playlist_id), videos=[track]))
									res = 'song removed'
									break
					except:
						res = 'You can\'t remove songs from this playlist (are you the owner?), requrest failed'
			self.log_me('debug', res)
		self.log_me('debug', "[E] async_modify_playlist")


	


	async def async_limit_count(self, limit):
		self.log_debug_later("[S] async_limit_count")
		self._trackLimitUser = limit
		# having a tracklimit (requests from the api) smaller than the user limit
		# (limits the list AFTER generation) is pointless, so lets adjust this here as well
		if(self._trackLimitUser > self._trackLimit):
			self._trackLimit = self._trackLimitUser
		self.log_me("debug", "New limit: " + str(self._trackLimitUser))
		self.log_me("debug", "[E] async_limit_count")


	async def async_start_radio(self, interrupt=True):
		self.log_debug_later("[S] async_start_radio")
		if(self._attributes['videoId'] == ""):
			self.log_me('debug', "Currently not playing anything so I don't know what to base the radio on")
		else:
			self.log_me('debug', "Starting radio based on " + str(self._attributes['videoId']))
			media_type = CHANNEL_VID_NO_INTERRUPT
			if(interrupt):
				media_type = CHANNEL_VID
			await self.async_play_media(media_type, self._attributes['videoId'])
		self.log_me("debug", "[E] async_start_radio")


	async def async_rate_track(self, rating="", song_id=""):
		self.log_debug_later("[S] async_rate_track")
		if(rating == ""):
			self.log_me('error', "No Rating given, stopping")
		if(song_id == ""):
			if(self._attributes['videoId'] != ""):
				self.log_me('debug', "No song Id given, taking current song")
				song_id = self._attributes['videoId']
			else:
				self.log_me('error', "No song Id given and currently not playing, giving up")

		if(song_id != "" and rating != ""):
			try:
				arg = 'LIKE'
				if(rating == SERVICE_CALL_THUMB_UP):
					self.log_me('debug', "rate thumb up")
					arg = 'LIKE'
				elif(rating == SERVICE_CALL_THUMB_DOWN):
					self.log_me('debug', "rate thumb down")
					arg = 'DISLIKE'
				elif(rating == SERVICE_CALL_THUMB_MIDDLE):
					self.log_me('debug', "rate thumb middle")
					arg = 'INDIFFERENT'
				elif(rating == SERVICE_CALL_TOGGLE_THUMB_UP_MIDDLE):
					if('likeStatus' in self._attributes):
						if(self._attributes['likeStatus'] == 'LIKE'):
							self.log_me('debug', "rate thumb middle")
							arg = 'INDIFFERENT'
						else:
							self.log_me('debug', "rate thumb up")
							arg = 'LIKE'
				await self.hass.async_add_executor_job(self._api.rate_song, song_id, arg)
				# only change arguments if the track that we're rating is the current one
				if(song_id == self._attributes['videoId']):
					self._attributes['likeStatus'] = arg
					if(self._like_in_name):
						self._attr_name = self._org_name + " - " + arg
					self.async_schedule_update_ha_state()
					self._tracks[self._next_track_no]['likeStatus'] = arg
			except:
				self.exc()
		self.log_me('debug', "[E] async_rate_track")


	def exc(self, resp="self"):
		# Print nicely formated exception.
		_LOGGER.error("\n\n == == == == == == = ytube_music_player Integration Error == == == == == == == == ")
		if(resp == "self"):
			_LOGGER.error("unfortunately we hit an error, please open a ticket at")
			_LOGGER.error("https://github.com/KoljaWindeler/ytube_music_player/issues")
		else:
			_LOGGER.error("unfortunately we hit an error in the sub api, please open a ticket at")
			_LOGGER.error("https://github.com/sigma67/ytmusicapi/issues")
		_LOGGER.error("and paste the following output:\n")
		_LOGGER.error(traceback.format_exc())
		_LOGGER.error("\nthanks, Kolja")
		_LOGGER.error(" == == == == == == = ytube_music_player Integration Error == == == == == == == == \n\n")


	async def async_browse_media(self, media_content_type=None, media_content_id=None):
		# Implement the websocket media browsing helper.
		self.log_me('debug', "async_browse_media")
		await self.async_check_api()
		if media_content_type in [None, "library"]:
			return await self.hass.async_add_executor_job(lambda: library_payload(self))

		payload = {
			"search_type": media_content_type,
			"search_id": media_content_id,
		}

		response = await build_item_response(self, payload)
		if response is None:
			raise BrowseError(
				f"Media not found: {media_content_type} / {media_content_id}"
			)
		return response

	# helper to resume tracking of the select field for media player
	# we have to untrack it before we change it ourself and give HA some time
	#  to make the change and call this resubscription delayed
	async def async_track_select_mediaplayer_helper(self, args):
		# this should now be needed .. but one never know
		if(self._untrack_remote_player_selector is not None):
			try:
				self._untrack_remote_player_selector()
				self.log_me('debug', "- untrack passed")
			except:
				self.log_me('debug', "- untrack failed")
			self._untrack_remote_player_selector = None
		self._untrack_remote_player_selector = async_track_state_change_event(
			self.hass, self._selects['speakers'], self.async_select_source_helper)
		self.log_me('debug', "- untrack resub")
