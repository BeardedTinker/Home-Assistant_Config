"""Sensor platform for emscrss."""
from georss_client.xml_parser import feed
from .const import DEFAULT_NAME, DOMAIN, ICON, SENSOR

from datetime import timedelta
import logging

from georss_client import UPDATE_OK, UPDATE_OK_NO_DATA
from georss_emsc_csem_earthquakes_client import EMSCEarthquakesFeed
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_NAME,
    CONF_RADIUS,
    CONF_URL,
    LENGTH_KILOMETERS
)
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

CONF_MAGNITUDE = "magnitude"
CONF_AGE = "age"

DEFAULT_URL = "https://www.emsc-csem.org/service/rss/rss.php?typ=emsc"
DEFAULT_RADIUS_IN_KM = 300.0
DEFAULT_MAGNITUDE = 3.0
DEFAULT_AGE_HOURS = 24

SCAN_INTERVAL = timedelta(minutes=5)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_URL, default=DEFAULT_URL): cv.string,
        vol.Optional(CONF_LATITUDE): cv.latitude,
        vol.Optional(CONF_LONGITUDE): cv.longitude,
        vol.Optional(CONF_RADIUS, default=DEFAULT_RADIUS_IN_KM): vol.Coerce(float),
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_MAGNITUDE, default=DEFAULT_MAGNITUDE): vol.Coerce(float),
        vol.Optional(CONF_AGE, default=DEFAULT_AGE_HOURS): vol.Coerce(float)
    }
)


def setup_platform(hass, config, add_entities, discovery_info=None):
    """Set up the EMSC component."""
    name = config.get(CONF_NAME)
    latitude = config.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config.get(CONF_LONGITUDE, hass.config.longitude)
    url = config.get(CONF_URL)
    radius_in_km = config.get(CONF_RADIUS)
    magnitude = config.get(CONF_MAGNITUDE)
    age = timedelta(hours=config.get(CONF_AGE))

    _LOGGER.debug(
        "latitude=%s, longitude=%s, url=%s, radius=%s, magintude=%s, age=%s",
        latitude,
        longitude,
        url,
        radius_in_km,
        magnitude,
        age
    )

    # Create all sensors based on categories.
    devices = []
    device = EMSCRSSServiceSensor(
        name, (latitude, longitude), url, radius_in_km, magnitude, age
    )
    devices.append(device)
    add_entities(devices, True)


class EMSCRSSServiceSensor(Entity):
    """Representation of a Sensor."""

    def __init__(
        self, service_name, coordinates, url, radius, magnitude, age
    ):
        """Initialize the sensor."""
        self._service_name = service_name
        self._state = None
        self._state_attributes = None

        self._feed = EMSCEarthquakesFeed(
            coordinates,
            url,
            filter_radius=radius,
            filter_minimum_magnitude=magnitude,
            filter_timespan=age
        )

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"{self._service_name}"

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement."""
        return None

    @property
    def icon(self):
        """Return the default icon to use in the frontend."""
        return ICON

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._state_attributes

    def update(self):
        """Update this sensor from the EMSC service."""

        status, feed_entries = self._feed.update()
        if status == UPDATE_OK:
            _LOGGER.debug(
                "Adding events to sensor %s: %s", self.entity_id, feed_entries
            )
            self._state = len(feed_entries)
            # And now compute the attributes from the filtered events.
            data = {}
            entries = []
            for entry in feed_entries:
                feed_entry = {}
                feed_entry["title"] = entry.title
                feed_entry["magnitude"] = entry.magnitude
                feed_entry["time"] = entry.time
                feed_entry["distance"] = round(entry.distance_to_home, 0)
                feed_entry["link"] = entry.link
                entries.append(feed_entry)
            data["earthquakes"] = entries
            self._state_attributes = data
        elif status == UPDATE_OK_NO_DATA:
            _LOGGER.debug("Update successful, but no data received from %s", self._feed)
            # Don't change the state or state attributes.
        else:
            _LOGGER.warning(
                "Update not successful, no data received from %s", self._feed
            )
            # If no events were found due to an error then just set state to
            # zero.
            self._state = 0
            self._state_attributes = {}