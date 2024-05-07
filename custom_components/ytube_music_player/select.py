"""Platform for sensor integration."""
import logging
from homeassistant.components.select import SelectEntity
from homeassistant.exceptions import NoEntitySpecifiedError
from . import DOMAIN
from .const import *

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, config, async_add_entities):
	_LOGGER.debug("Init the dropdown(s)")
	init_dropdowns = config.data.get(CONF_INIT_DROPDOWNS, DEFAULT_INIT_DROPDOWNS)
	select_entities = {
		"playlists": yTubeMusicPlaylistSelect(hass, config),
		"speakers": yTubeMusicSpeakerSelect(hass, config),
		"playmode": yTubeMusicPlayModeSelect(hass, config),
		"radiomode": yTubeMusicSourceSelect(hass, config),
		"repeatmode": yTubeMusicRepeatSelect(hass, config)
	}
	entities = []
	for dropdown,entity in select_entities.items():
		if dropdown in init_dropdowns:
			entities.append(entity)
	async_add_entities(entities, update_before_add=True)

class yTubeMusicSelectEntity(SelectEntity):
	def __init__(self, hass, config):
		self.hass = hass
		self._device_id = config.entry_id
		self._device_name = config.data.get(CONF_NAME)
		self._attr_has_entity_name = True

	def select_option(self, option):
		"""Change the selected option."""
		self._attr_current_option = option
		self.schedule_update_ha_state()
	@property
	def device_info(self):
		return {
			'identifiers': {(DOMAIN, self._device_id)},
			'name': self._device_name,
			'manufacturer': "Google Inc.",
			'model': DOMAIN
		}

	@property
	def should_poll(self):
		return False


class yTubeMusicPlaylistSelect(yTubeMusicSelectEntity):
	def __init__(self, hass, config):
		super().__init__(hass, config)
		self._attr_unique_id = self._device_id + "_playlist"
		self._attr_name = "Playlist"
		self._attr_icon = 'mdi:playlist-music'
		self.hass.data[DOMAIN][self._device_id]['select_playlists'] = self
		self._attr_options = ["loading"]
		self._attr_current_option = None

	async def async_update(self):
		# update select
		self._ready = True
		try:
			self._attr_options = list(self.hass.data[DOMAIN][self._device_id]['playlists'].keys())
		except:
			pass
		try:
			self.async_schedule_update_ha_state()
		except NoEntitySpecifiedError:
			pass  # we ignore this due to a harmless startup race condition


class yTubeMusicSpeakerSelect(yTubeMusicSelectEntity):
	def __init__(self, hass, config):
		super().__init__(hass, config)
		self._attr_unique_id = self._device_id + "_speaker"
		self._attr_name = "Speaker"
		self._attr_icon = 'mdi:speaker'
		self.hass.data[DOMAIN][self._device_id]['select_speakers'] = self
		self._attr_options = ["loading"]
		self._attr_current_option = None

	async def async_update(self, options=[]):
		# update select
		self._ready = True
		try:
			self._attr_options = options
		except:
			pass
		try:
			self.async_schedule_update_ha_state()
		except NoEntitySpecifiedError:
			pass  # we ignore this due to a harmless startup race condition


class yTubeMusicPlayModeSelect(yTubeMusicSelectEntity):
	def __init__(self, hass, config):
		super().__init__(hass, config)
		self._attr_unique_id = self._device_id + "_playmode"
		self._attr_name = "Play Mode"
		self._attr_icon = 'mdi:shuffle'
		self.hass.data[DOMAIN][self._device_id]['select_playmode'] = self
		self._attr_options = ["Shuffle","Random","Shuffle Random","Direct"]
		self._attr_current_option = "Shuffle Random"


class yTubeMusicSourceSelect(yTubeMusicSelectEntity):
	def __init__(self, hass, config):
		super().__init__(hass, config)
		self._attr_unique_id = self._device_id + "_radiomode"
		self._attr_name = "Radio Mode"
		self._attr_icon = 'mdi:music-box-multiple'
		self.hass.data[DOMAIN][self._device_id]['select_radiomode'] = self
		self._attr_options = ["Playlist","Playlist Radio"] # "Playlist" means not radio mode
		self._attr_current_option = "Playlist"


class yTubeMusicRepeatSelect(yTubeMusicSelectEntity):
	def __init__(self, hass, config):
		super().__init__(hass, config)
		self._attr_unique_id = self._device_id + "_repeat"
		self._attr_name = "Repeat Mode"
		self._attr_icon = 'mdi:repeat'
		self.hass.data[DOMAIN][self._device_id]['select_repeatmode'] = self
		self._attr_options = ["all", "one", "off"]  # one for future
		self._attr_current_option = "all"