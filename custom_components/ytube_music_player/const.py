from homeassistant.components.sensor import PLATFORM_SCHEMA, ENTITY_ID_FORMAT
import homeassistant.helpers.config_validation as cv
from homeassistant.components.media_player import MediaPlayerState, MediaPlayerEntityFeature
from homeassistant.components.media_player.const import MediaClass, MediaType, RepeatMode
import voluptuous as vol
import logging
import datetime
import traceback
import asyncio
from collections import OrderedDict
from ytmusicapi import YTMusic


from homeassistant.const import (
	EVENT_HOMEASSISTANT_START,
	ATTR_ENTITY_ID,
	CONF_DEVICE_ID,
	CONF_NAME,
	CONF_USERNAME,
	CONF_PASSWORD,
	STATE_PLAYING,
	STATE_PAUSED,
	STATE_ON,
	STATE_OFF,
	STATE_IDLE,
	ATTR_COMMAND,
)

from homeassistant.components.media_player import (
	MediaPlayerEntity,
	PLATFORM_SCHEMA,
	SERVICE_TURN_ON,
	SERVICE_TURN_OFF,
	SERVICE_PLAY_MEDIA,
	SERVICE_MEDIA_PAUSE,
	SERVICE_VOLUME_UP,
	SERVICE_VOLUME_DOWN,
	SERVICE_VOLUME_SET,
	ATTR_MEDIA_VOLUME_LEVEL,
	ATTR_MEDIA_CONTENT_ID,
	ATTR_MEDIA_CONTENT_TYPE,
	DOMAIN as DOMAIN_MP,
)

#  add for old settings
from homeassistant.components.input_boolean import (
	SERVICE_TURN_OFF as IB_OFF,
	SERVICE_TURN_ON as IB_ON,
	DOMAIN as DOMAIN_IB,
)

import homeassistant.components.select as select
import homeassistant.components.input_select as input_select  # add for old settings
import homeassistant.components.input_boolean as input_boolean  # add for old settings

# Should be equal to the name of your component.
PLATFORMS = {"sensor", "select", "media_player" }
DOMAIN = "ytube_music_player"

SUPPORT_YTUBEMUSIC_PLAYER = (
	MediaPlayerEntityFeature.TURN_ON
	| MediaPlayerEntityFeature.TURN_OFF
	| MediaPlayerEntityFeature.PLAY
	| MediaPlayerEntityFeature.PLAY_MEDIA
	| MediaPlayerEntityFeature.PAUSE
	| MediaPlayerEntityFeature.STOP
	| MediaPlayerEntityFeature.VOLUME_SET
	| MediaPlayerEntityFeature.VOLUME_STEP
	| MediaPlayerEntityFeature.VOLUME_MUTE
	| MediaPlayerEntityFeature.PREVIOUS_TRACK
	| MediaPlayerEntityFeature.NEXT_TRACK
	| MediaPlayerEntityFeature.SHUFFLE_SET
	| MediaPlayerEntityFeature.REPEAT_SET
	| MediaPlayerEntityFeature.BROWSE_MEDIA
	| MediaPlayerEntityFeature.SELECT_SOURCE
	| MediaPlayerEntityFeature.SEEK
)

SERVICE_SEARCH = "search"
SERVICE_ADD_TO_PLAYLIST = "add_to_playlist"
SERVICE_REMOVE_FROM_PLAYLIST = "remove_from_playlist"
SERVICE_LIMIT_COUNT = "limit_count"
SERVICE_RADIO = "start_radio"
ATTR_PARAMETERS = "parameters"
ATTR_QUERY = "query"
ATTR_FILTER = "filter"
ATTR_LIMIT = "limit"
ATTR_SONG_ID = "song_id"
ATTR_PLAYLIST_ID = "playlist_id"
ATTR_RATING = "rating"
ATTR_INTERRUPT = "interrupt"
SERVICE_CALL_METHOD = "call_method"
SERVICE_CALL_RATE_TRACK = "rate_track"
SERVICE_CALL_THUMB_UP = "thumb_up"
SERVICE_CALL_THUMB_DOWN = "thumb_down"
SERVICE_CALL_THUMB_MIDDLE = "thumb_middle"
SERVICE_CALL_TOGGLE_THUMB_UP_MIDDLE = "thumb_toggle_up_middle"
SERVICE_CALL_INTERRUPT_START = "interrupt_start"
SERVICE_CALL_INTERRUPT_RESUME = "interrupt_resume"
SERVICE_CALL_RELOAD_DROPDOWNS = "reload_dropdowns"
SERVICE_CALL_OFF_IS_IDLE = "off_is_idle"
SERVICE_CALL_PAUSED_IS_IDLE = "paused_is_idle"
SERVICE_CALL_IGNORE_PAUSED_ON_MEDIA_CHANGE = "ignore_paused_on_media_change"
SERVICE_CALL_DO_NOT_IGNORE_PAUSED_ON_MEDIA_CHANGE = "do_not_ignore_paused_on_media_change"
SERVICE_CALL_IDLE_IS_IDLE = "idle_is_idle"
SERIVCE_CALL_DEBUG_AS_ERROR = "debug_as_error"
SERVICE_CALL_LIKE_IN_NAME = "like_in_name"
SERVICE_CALL_GOTO_TRACK = "goto_track"
SERVICE_CALL_MOVE_TRACK = "move_track_within_queue"
SERVICE_CALL_APPEND_TRACK = "append_track_to_queue"

CONF_RECEIVERS = 'speakers'  # list of speakers (media_players)
CONF_HEADER_PATH = 'header_path'
CONF_API_LANGUAGE = 'api_language'
CONF_SHUFFLE = 'shuffle'
CONF_SHUFFLE_MODE = 'shuffle_mode'
CONF_COOKIE = 'cookie'
CONF_CLIENT_ID = 'client_id'
CONF_CLIENT_SECRET = 'secret'
CONF_CODE = 'code'
CONF_BRAND_ID = 'brand_id'
CONF_ADVANCE_CONFIG = 'advance_config'
CONF_RENEW_OAUTH = 'renew_oauth'
CONF_LIKE_IN_NAME = 'like_in_name'
CONF_DEBUG_AS_ERROR = 'debug_as_error'
CONF_LEGACY_RADIO = 'legacy_radio'
CONF_SORT_BROWSER = 'sort_browser'
CONF_INIT_EXTRA_SENSOR = 'extra_sensor'
CONF_INIT_DROPDOWNS = 'dropdowns'
ALL_DROPDOWNS = ["playlists","speakers","playmode","radiomode","repeatmode"]
DEFAULT_INIT_DROPDOWNS = ["playlists","speakers","playmode"]
CONF_MAX_DATARATE = 'max_datarate'

CONF_TRACK_LIMIT = 'track_limit'
CONF_PROXY_URL = 'proxy_url'
CONF_PROXY_PATH = 'proxy_path'

#  add for old settings
CONF_SELECT_SOURCE = 'select_source'
CONF_SELECT_PLAYLIST = 'select_playlist'
CONF_SELECT_SPEAKERS = 'select_speakers'
CONF_SELECT_PLAYMODE = 'select_playmode'
CONF_SELECT_PLAYCONTINUOUS = 'select_playcontinuous'
OLD_INPUTS = {
				"playlists": CONF_SELECT_PLAYLIST,
				"speakers": CONF_SELECT_SPEAKERS,
				"playmode": CONF_SELECT_PLAYMODE,
				"radiomode": CONF_SELECT_SOURCE,
				"repeatmode": CONF_SELECT_PLAYCONTINUOUS
}
DEFAULT_SELECT_PLAYCONTINUOUS = ""
DEFAULT_SELECT_SOURCE = ""
DEFAULT_SELECT_PLAYLIST = ""
DEFAULT_SELECT_PLAYMODE = ""
DEFAULT_SELECT_SPEAKERS = ""

DEFAULT_HEADER_FILENAME = 'header_'
DEFAULT_API_LANGUAGE = 'en'
DEFAULT_LIKE_IN_NAME = False
DEFAULT_DEBUG_AS_ERROR = False
DEFAULT_INIT_EXTRA_SENSOR = False
PROXY_FILENAME = "ytube_proxy.mp4"

DEFAULT_TRACK_LIMIT = 25
DEFAULT_MAX_DATARATE = 129000
DEFAULT_LEGACY_RADIO = True
DEFAULT_SORT_BROWSER = True

ERROR_COOKIE = 'ERROR_COOKIE'
ERROR_AUTH_USER = 'ERROR_AUTH_USER'
ERROR_GENERIC = 'ERROR_GENERIC'
ERROR_OAUTH = 'ERROR_OAUTH'
ERROR_CONTENTS = 'ERROR_CONTENTS'
ERROR_FORMAT = 'ERROR_FORMAT'
ERROR_NONE = 'ERROR_NONE'
ERROR_FORBIDDEN = 'ERROR_FORBIDDEN'

PLAYMODE_SHUFFLE = "Shuffle"
PLAYMODE_RANDOM = "Random"
PLAYMODE_SHUFFLE_RANDOM = "Shuffle Random"
PLAYMODE_DIRECT = "Direct"

ALL_SHUFFLE_MODES = [PLAYMODE_SHUFFLE, PLAYMODE_RANDOM, PLAYMODE_SHUFFLE_RANDOM, PLAYMODE_DIRECT]
DEFAULT_SHUFFLE_MODE = PLAYMODE_SHUFFLE_RANDOM
DEFAULT_SHUFFLE = True

SEARCH_ID = "search_id"
SEARCH_TYPE = "search_type"
LIB_PLAYLIST = 'library_playlists'
LIB_PLAYLIST_TITLE = "Library Playlists"

HOME_TITLE = "Home"
HOME_CAT = "home"
HOME_CAT_2 = "home2"

LIB_ALBUM = 'library_albums'
LIB_ALBUM_TITLE = "Library Albums"

LIB_TRACKS = 'library_tracks'
LIB_TRACKS_TITLE = "Library Songs"
ALL_LIB_TRACKS = 'all_library_tracks'
ALL_LIB_TRACKS_TITLE = 'All library tracks'

HISTORY = 'history'
HISTORY_TITLE = "Last played songs"

USER_TRACKS = 'user_tracks'
USER_TRACKS_TITLE = "Uploaded songs"

USER_ALBUMS = 'user_albums'
USER_ALBUMS_TITLE = "Uploaded Albums"
USER_ALBUM = 'user_album'

USER_ARTISTS = 'user_artists'
USER_ARTISTS_TITLE = "Uploaded Artists"

USER_ARTISTS_2 = 'user_artists2'
USER_ARTISTS_2_TITLE = "Uploaded Artists -> Album"

USER_ARTIST = 'user_artist'
USER_ARTIST_TITLE = "Uploaded Artist"

USER_ARTIST_2 = 'user_artist2'
USER_ARTIST_2_TITLE = "Uploaded Album"

SEARCH = 'search'
SEARCH_TITLE = "Search results" 

ALBUM_OF_TRACK = 'album_of_track'
ALBUM_OF_TRACK_TITLE = 'Album of current Track'

PLAYER_TITLE = "Playback device"

MOOD_OVERVIEW = 'mood_overview'
MOOD_PLAYLISTS = 'mood_playlists'
MOOD_TITLE = 'Moods & Genres'

CUR_PLAYLIST = 'cur_playlists'
CUR_PLAYLIST_TITLE = "Current Playlists"
CUR_PLAYLIST_COMMAND = "PLAYLIST_GOTO_TRACK"

CHANNEL = 'channel'
CHANNEL_VID = 'vid_channel'
CHANNEL_VID_NO_INTERRUPT = 'vid_no_interrupt_channel'
STATE_OFF_1X = 'OFF_1X'
BROWSER_LIMIT = 500


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend = vol.Schema({
	DOMAIN: vol.Schema({
		vol.Optional(CONF_RECEIVERS): cv.string,
		vol.Optional(CONF_HEADER_PATH, default=DEFAULT_HEADER_FILENAME): cv.string,
	})
}, extra=vol.ALLOW_EXTRA)

# Shortcut for the logger
_LOGGER = logging.getLogger(__name__)



async def async_try_login(hass, path, brand_id=None, language='en',oauth=None):
	ret = {}
	api = None
	msg = ""
	#### try to init object #####
	try:
		if(oauth):
			api = await hass.async_add_executor_job(lambda: YTMusic(auth=path,oauth_credentials=oauth,user=brand_id,language=language))
		else:
			api = await hass.async_add_executor_job(YTMusic,path,brand_id,None,None,language)
	except KeyError as err:
		_LOGGER.debug("- Key exception")
		if(str(err)=="'contents'"):
			msg = "Format of cookie is OK, found '__Secure-3PAPISID' and '__Secure-3PSID' but can't retrieve any data with this settings, maybe you didn't copy all data?"
			_LOGGER.error(msg)
			ret["base"] = ERROR_CONTENTS
		elif(str(err)=="'Cookie'"):
			msg = "Format of cookie is NOT OK, Field 'Cookie' not found!"
			_LOGGER.error(msg)
			ret["base"] = ERROR_COOKIE
		elif(str(err)=="'__Secure-3PAPISID'" or str(err)=="'__Secure-3PSID'"):
			msg = "Format of cookie is NOT OK, likely missing '__Secure-3PAPISID' or '__Secure-3PSID'"
			_LOGGER.error(msg)
			ret["base"] = ERROR_FORMAT
		else:
			msg = "Some unknown error occured during the cookies usage, key is: "+str(err)
			_LOGGER.error(msg)
			_LOGGER.error("please see below")
			_LOGGER.error(traceback.format_exc())
			ret["base"] = ERROR_GENERIC
	except:
		_LOGGER.debug("- Generic exception")
		msg = "Format of cookie is NOT OK, missing e.g. AuthUser or Cookie"
		_LOGGER.error(msg)
		ret["base"] = ERROR_FORMAT

	#### try to grab library data #####
	if(api == None and ret == {}):
		msg = "Format of cookie seams OK, but the returned sub API object is None"
		_LOGGER.error(msg)
		ret["base"] = ERROR_NONE
	elif(not(api == None) and ret == {}):
		try:
			await hass.async_add_executor_job(api.get_library_songs)
		except KeyError as err:
			if(str(err)=="'contents'"):
				msg = "Format of cookie is OK, found '__Secure-3PAPISID' and '__Secure-3PSID' but can't retrieve any data with this settings, maybe you didn't copy all data? Or did you log-out?"
				_LOGGER.error(msg)
				ret["base"] = ERROR_CONTENTS
		except Exception as e:
			if hasattr(e, 'args'):
				if(len(e.args)>0):
					if(isinstance(e.args[0],str)):
						if(e.args[0].startswith("Server returned HTTP 403: Forbidden")):
							msg = "The entered information has the correct format, but returned an error 403 (access forbidden). You don't have access with this data (anymore?). Please update the cookie"
							_LOGGER.error(msg)
							ret["base"] = ERROR_FORBIDDEN
			else:
				msg = "Running get_library_songs resulted in an exception, no idea why.. honestly"
				_LOGGER.error(msg)
				_LOGGER.error("Please see below")
				_LOGGER.error(traceback.format_exc())
				ret["base"] = ERROR_GENERIC
	return [ret, msg, api]

def ensure_config(user_input):
	"""Make sure that needed Parameter exist and are filled with default if not."""
	out = {}
	out[CONF_NAME] = DOMAIN
	out[CONF_API_LANGUAGE] = DEFAULT_API_LANGUAGE
	out[CONF_RECEIVERS] = ''
	out[CONF_SHUFFLE] = DEFAULT_SHUFFLE
	out[CONF_SHUFFLE_MODE] = DEFAULT_SHUFFLE_MODE
	out[CONF_PROXY_PATH] = ""
	out[CONF_PROXY_URL] = ""
	out[CONF_BRAND_ID] = ""
	out[CONF_COOKIE] = ""
	out[CONF_CLIENT_ID] = ""
	out[CONF_CLIENT_SECRET] = ""
	out[CONF_ADVANCE_CONFIG] = False
	out[CONF_RENEW_OAUTH] = False
	out[CONF_LIKE_IN_NAME] = DEFAULT_LIKE_IN_NAME
	out[CONF_DEBUG_AS_ERROR] = DEFAULT_DEBUG_AS_ERROR
	out[CONF_TRACK_LIMIT] = DEFAULT_TRACK_LIMIT
	out[CONF_LEGACY_RADIO] = DEFAULT_LEGACY_RADIO
	out[CONF_SORT_BROWSER] = DEFAULT_SORT_BROWSER
	out[CONF_INIT_EXTRA_SENSOR] = DEFAULT_INIT_EXTRA_SENSOR
	out[CONF_INIT_DROPDOWNS] = DEFAULT_INIT_DROPDOWNS
	out[CONF_MAX_DATARATE] = DEFAULT_MAX_DATARATE

	if user_input is not None:
		#  for the old shuffle_mode setting.
		out.update(user_input)
		if isinstance(_shuffle_mode := out[CONF_SHUFFLE_MODE], int):
			if _shuffle_mode >= 1:
				out[CONF_SHUFFLE_MODE] = ALL_SHUFFLE_MODES[_shuffle_mode - 1]
			else:
				out[CONF_SHUFFLE_MODE] = PLAYMODE_DIRECT
			_LOGGER.debug(f"shuffle_mode: {_shuffle_mode} is a deprecated value and has been replaced with '{out[CONF_SHUFFLE_MODE]}'.")

		# If old input(s) exists,uncheck the new corresponding select(s).
		# If the old input is set to a blank space character, then permanently delete this field.
		for dropdown in ALL_DROPDOWNS:
			if (_old_conf_input := out.get(OLD_INPUTS[dropdown])) is not None:
				if _old_conf_input.replace(" ","") == "":
					del out[OLD_INPUTS[dropdown]]
				else:
					if dropdown in out[CONF_INIT_DROPDOWNS]:
						out[CONF_INIT_DROPDOWNS].remove(dropdown)
						_LOGGER.debug(f"old {dropdown} input_select: {_old_conf_input} exists,uncheck the corresponding new select.")
	return out


def find_thumbnail(item):
	item_thumbnail = ""
	try:
		thumbnail_list = ""
		if 'thumbnails' in item:
			if 'thumbnail' in item['thumbnails']:
				thumbnail_list = item['thumbnails']['thumbnail']
			else:
				thumbnail_list = item['thumbnails']
		elif 'thumbnail' in item:
			thumbnail_list = item['thumbnail']

		if isinstance(thumbnail_list, list):
			if 'url' in thumbnail_list[-1]:
				item_thumbnail = thumbnail_list[-1]['url']
	except:
		pass
	return item_thumbnail
