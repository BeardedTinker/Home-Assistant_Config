"""Platform for sensor integration."""
import logging
from homeassistant.helpers.entity import Entity
from homeassistant.exceptions import NoEntitySpecifiedError
from . import DOMAIN
from .const import *


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config, async_add_entities):
	# Run setup via Storage
	_LOGGER.debug("init ytube sensor")
	if(config.data.get(CONF_INIT_EXTRA_SENSOR, DEFAULT_INIT_EXTRA_SENSOR)):
		async_add_entities([yTubeMusicSensor(hass, config)], update_before_add=True)


class yTubeMusicSensor(Entity):
	# Extra Sensor for the YouTube Music player integration

	def __init__(self,hass, config):
		# Initialize the sensor.
		self.hass = hass
		self._state = STATE_OFF
		self._device_id = config.entry_id
		self._device_name = config.data.get(CONF_NAME)
		self._attr_unique_id = config.entry_id + "_extra"  # should be different from the media_player entity
		self._attr_has_entity_name = True
		self._attr_name = "Extra"
		self._attr_icon = 'mdi:information-outline'
		self.hass.data[DOMAIN][self._device_id]['extra_sensor'] = self
		self._attr = {'tracks', 'search', 'lyrics', 'playlists', 'total_tracks'}
		self._attributes = {}
		for attr in self._attr:
			self._attributes[attr] = ""

		_LOGGER.debug("init ytube sensor done")

	@property
	def device_info(self):
		return {
			'identifiers': {(DOMAIN, self._device_id)},
			'name': self._device_name,
			'manufacturer': "Google Inc.",
			'model': DOMAIN
		}
		
	@property
	def name(self):
		# Return the name of the sensor.
		return self._attr_name

	@property
	def state(self):
		# Return the state of the sensor.
		return self._state

	@property
	def should_poll(self):
		# No polling needed.
		return False

	async def async_update(self):
		# update sensor
		self._ready = True
		_LOGGER.debug("updating ytube sensor")

		# update all attributes from the data var
		for attr in self._attr:
			if attr in self.hass.data[DOMAIN][self._device_id]:
				self._attributes[attr] = self.hass.data[DOMAIN][self._device_id][attr]

		try:
			self.async_schedule_update_ha_state()
		except NoEntitySpecifiedError:
			pass  # we ignore this due to a harmless startup race condition

	@property
	def extra_state_attributes(self):
		# Return the device state attributes.
		return self._attributes