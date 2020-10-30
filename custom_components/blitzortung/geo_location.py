"""Support for Blitzortung geo location events."""
import bisect
import hashlib
import logging
import time

from homeassistant.components.geo_location import GeolocationEvent
from homeassistant.const import (
    ATTR_ATTRIBUTION,
    CONF_UNIT_SYSTEM_IMPERIAL,
    LENGTH_KILOMETERS,
    LENGTH_MILES,
)
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect,
    async_dispatcher_send,
)
from homeassistant.util.dt import utc_from_timestamp

from .const import ATTR_EXTERNAL_ID, ATTR_PUBLICATION_DATE, ATTRIBUTION, DOMAIN

_LOGGER = logging.getLogger(__name__)


DEFAULT_EVENT_NAME_TEMPLATE = "Lightning Strike"
DEFAULT_ICON = "mdi:flash"

SIGNAL_DELETE_ENTITY = "blitzortung_delete_entity_{0}"


async def async_setup_entry(hass, config_entry, async_add_entities):
    coordinator = hass.data[DOMAIN][config_entry.entry_id]
    if not coordinator.max_tracked_lightnings:
        return

    manager = BlitzortungEventManager(
        hass,
        async_add_entities,
        coordinator.max_tracked_lightnings,
        coordinator.time_window_seconds,
    )

    coordinator.register_lightning_receiver(manager.lightning_cb)
    coordinator.register_on_tick(manager.tick)


class Strikes(list):
    def __init__(self, capacity):
        self._keys = []
        self._key_fn = lambda strike: strike._publication_date
        self._max_key = 0
        self._capacity = capacity
        super().__init__()

    def insort(self, item):
        k = self._key_fn(item)
        if k > self._max_key:
            self._max_key = k
            self._keys.append(k)
            self.append(item)
        else:
            i = bisect.bisect_right(self._keys, k)
            self._keys.insert(i, k)
            self.insert(i, item)
        n = len(self) - self._capacity
        if n > 0:
            del self._keys[0:n]
            to_delete = self[0:n]
            self[0:n] = []
            return to_delete
        return ()

    def cleanup(self, k):
        if not self._keys or self._keys[0] > k:
            return ()

        i = bisect.bisect_right(self._keys, k)
        if not i:
            return ()

        del self._keys[0:i]
        to_delete = self[0:i]
        self[0:i] = []
        return to_delete


class BlitzortungEventManager:
    """Define a class to handle Blitzortung events."""

    def __init__(
        self, hass, async_add_entities, max_tracked_lightnings, window_seconds,
    ):
        """Initialize."""
        self._async_add_entities = async_add_entities
        self._hass = hass
        self._strikes = Strikes(max_tracked_lightnings)
        self._window_seconds = window_seconds

        if hass.config.units.name == CONF_UNIT_SYSTEM_IMPERIAL:
            self._unit = LENGTH_MILES
        else:
            self._unit = LENGTH_KILOMETERS

    def lightning_cb(self, lightning):
        _LOGGER.debug("geo_location lightning: %s", lightning)
        event = BlitzortungEvent(
            lightning["distance"],
            lightning["lat"],
            lightning["lon"],
            "km",
            lightning["time"],
        )
        to_delete = self._strikes.insort(event)
        self._async_add_entities([event])
        if to_delete:
            self._remove_events(to_delete)
        _LOGGER.debug("tracked lightnings: %s", len(self._strikes))

    @callback
    def _remove_events(self, events):
        """Remove old geo location events."""
        _LOGGER.debug("Going to remove %s", events)
        for event in events:
            async_dispatcher_send(
                self._hass, SIGNAL_DELETE_ENTITY.format(event._strike_id)
            )

    def tick(self):
        to_delete = self._strikes.cleanup(time.time() - self._window_seconds)
        if to_delete:
            self._remove_events(to_delete)


class BlitzortungEvent(GeolocationEvent):
    """Define a lightning strike event."""

    def __init__(self, distance, latitude, longitude, unit, time):
        """Initialize entity with data provided."""
        self._distance = distance
        self._latitude = latitude
        self._longitude = longitude
        self._time = time
        self._publication_date = time / 1e9
        self._remove_signal_delete = None
        self._strike_id = hashlib.sha1(f"{latitude}_{longitude}_{time}".encode()).hexdigest()
        self._unit_of_measurement = unit
        self.entity_id = "geo_location.lightning_strike_{0}".format(self._strike_id)

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        attributes = {}
        for key, value in (
            (ATTR_EXTERNAL_ID, self._strike_id),
            (ATTR_ATTRIBUTION, ATTRIBUTION),
            (ATTR_PUBLICATION_DATE, utc_from_timestamp(self._publication_date)),
        ):
            attributes[key] = value
        return attributes

    @property
    def distance(self):
        """Return distance value of this external event."""
        return self._distance

    @property
    def icon(self):
        """Return the icon to use in the front-end."""
        return DEFAULT_ICON

    @property
    def latitude(self):
        """Return latitude value of this external event."""
        return self._latitude

    @property
    def longitude(self):
        """Return longitude value of this external event."""
        return self._longitude

    @property
    def name(self):
        """Return the name of the event."""
        return DEFAULT_EVENT_NAME_TEMPLATE.format(self._publication_date)

    @property
    def source(self) -> str:
        """Return source value of this external event."""
        return DOMAIN

    @property
    def should_poll(self):
        """Disable polling."""
        return False

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return self._unit_of_measurement

    @callback
    def _delete_callback(self):
        """Remove this entity."""
        self._remove_signal_delete()
        self.hass.async_create_task(self.async_remove())

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        self._remove_signal_delete = async_dispatcher_connect(
            self.hass,
            SIGNAL_DELETE_ENTITY.format(self._strike_id),
            self._delete_callback,
        )
