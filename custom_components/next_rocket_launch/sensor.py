"""The Next Rocket Launch integration."""

from datetime import datetime, timedelta, timezone
import logging

from ics import Calendar
import voluptuous as vol

from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import ATTR_ATTRIBUTION
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.aiohttp_client import async_create_clientsession
import async_timeout

_LOGGER = logging.getLogger(__name__)

DOMAIN = "next_rocket_launch"
DEFAULT_NAME = "Next rocket launch"
DEFAULT_ROCKET_NAME = "ALL"
ICS_URL = "https://ics.teamup.com/feed/ks9mo8bt5a2he89r6j/0.ics"
ATTRIBUTION = "Data provided by Teamup"
SCAN_INTERVAL = timedelta(minutes=60)
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=15)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {vol.Optional("rocket_name", default=DEFAULT_ROCKET_NAME): cv.ensure_list}
)


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Create the launch sensor."""
    session = async_create_clientsession(hass)
    ics_data_provider = GetICSData(ICS_URL, session, hass)

    async def async_update_data():
        async with async_timeout.timeout(10):
            return await ics_data_provider.ics_update()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="sensor",
        update_method=async_update_data,
        update_interval=SCAN_INTERVAL,
    )

    await coordinator.async_refresh()

    nl_sensors = []
    for option in config.get("rocket_name"):
        nl_sensors.append(GetNextLaunch(coordinator, option, ics_data_provider))

    async_add_entities(nl_sensors, True)


class GetICSData:

    """The class for handling the data retrieval."""

    def __init__(self, url, session, hass):
        """Initialize the data object."""
        _LOGGER.debug("Initialize the data object")
        self.url = url
        self.timeline = None
        self.session = session
        self.hass = hass

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def ics_update(self):
        """Get the latest data from ics."""
        _LOGGER.debug("Get the latest data from ics")

        async with async_timeout.timeout(10):
            resp = await self.session.get(self.url)

            if resp.status != 200:
                _LOGGER.error(
                    "Unable to get ics file: %s (%s)",
                    resp.status_code,
                    self.url,
                )
                return False

            raw_ics_file = await resp.text()
            try:
                parsed_ics = Calendar(raw_ics_file)
                self.timeline = list(parsed_ics.timeline)
                return self.timeline
            except ValueError as error:
                _LOGGER.error(
                    "Unable (ValueError) to parse ics file: %s (%s)",
                    error,
                    self.url,
                )
                return False
            except NotImplementedError as error:
                _LOGGER.error(
                    "Unable (NotImplementedError) to parse ics file: %s (%s)",
                    error,
                    self.url,
                )
                return False


class GetNextLaunch(Entity):

    """The class for handling the data."""

    def __init__(self, coordinator, rocket_name, ics_data_provider):
        """Initialize the sensor object."""
        _LOGGER.debug("Initialize the sensor object")
        self.ics_data_provider = ics_data_provider
        self.rocket_name = rocket_name
        self._name = "Next Rocket " + rocket_name
        self._attributes = {}
        self._state = None
        self.have_futur = False
        self.coordinator = coordinator

    async def async_update(self):
        """Process data."""
        _LOGGER.debug("Start async update for %s", self.name)

        self.have_futur = False

        if self.ics_data_provider is None:
            _LOGGER.debug("ICS Data not init")
            return

        if self.ics_data_provider.timeline is None:
            _LOGGER.debug("ICS Data timeline not init")
            return

        last_passed = None
        last_futur = None

        if self.rocket_name == "ALL":
            selected_events = self.ics_data_provider.timeline
        else:
            selected_events = [
                x for x in self.ics_data_provider.timeline if self.rocket_name in x.name
            ]

        for event in selected_events:
            if event.begin < datetime.now(timezone.utc):
                last_passed = event
            else:
                if not self.have_futur:
                    last_futur = event
                    self.have_futur = True

        if last_futur is not None:
            self._state = last_futur.begin.isoformat()
            self._attributes["Comment"] = last_futur.name
            self._attributes["Location"] = last_futur.location
            self._attributes["Url"] = last_futur.url
        else:
            self._state = "Not planned"

        if last_passed is not None:
            self._attributes["Previous"] = last_passed.name
            self._attributes["Previous date"] = last_passed.begin.format()

        self._attributes[ATTR_ATTRIBUTION] = ATTRIBUTION
        self._attributes["last_update"] = datetime.now()

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the icon of the sensor."""
        return "mdi:rocket"

    @property
    def device_state_attributes(self):
        """Return attributes for the sensor."""
        return self._attributes

    @property
    def device_class(self):
        """Return device_class."""
        if self.have_futur:
            return "timestamp"

        return "text"

    @property
    def available(self):
        """Return if entity is available."""
        return self.coordinator.last_update_success

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )

    # @property
    # def should_poll(self):
    #     """No need to poll. Coordinator notifies entity of updates."""
    #     return False
