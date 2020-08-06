"""Garbage Collection Callendar"""
from datetime import datetime, timedelta
import logging
from homeassistant.components.calendar import PLATFORM_SCHEMA, CalendarEventDevice
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.template import DATE_STR_FORMAT
from homeassistant.util import Throttle, dt

# from .sensor import find_entity

from .const import (
    DOMAIN,
    CALENDAR_PLATFORM,
    SENSOR_PLATFORM,
    CALENDAR_NAME,
)

_LOGGER = logging.getLogger(__name__)
MIN_TIME_BETWEEN_UPDATES = timedelta(seconds=30)


async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
):  # pylint: disable=unused-argument
    """Setup the calendar platform."""
    # Only single instance allowed
    if GarbageCollectionCalendar.instances == 0:
        async_add_entities([GarbageCollectionCalendar(hass)], True)


class GarbageCollectionCalendar(CalendarEventDevice):
    """The garbage collection calendar class"""

    instances = 0

    def __init__(self, hass):
        """Create empry calendar"""
        self._cal_data = {}
        self._name = CALENDAR_NAME
        GarbageCollectionCalendar.instances += 1

    @property
    def event(self):
        """Return the next upcoming event."""
        return self.hass.data[DOMAIN][CALENDAR_PLATFORM].event

    @property
    def name(self):
        """Return the name of the entity."""
        return self._name

    async def async_update(self):
        """Update all calendars."""
        self.hass.data[DOMAIN][CALENDAR_PLATFORM].update()

    async def async_get_events(self, hass, start_date, end_date):
        """Get all events in a specific time frame."""
        return await self.hass.data[DOMAIN][CALENDAR_PLATFORM].async_get_events(
            hass, start_date, end_date
        )

    @property
    def device_state_attributes(self):
        """Return the device state attributes."""
        if self.hass.data[DOMAIN][CALENDAR_PLATFORM].event is None:
            # No tasks, we don't need to show anything.
            return None

        return {}


class EntitiesCalendarData:
    """
    Class used by the Entities Calendar class to hold all entity events.
    """

    def __init__(self, hass):
        """Initialize an Entities Calendar Data"""
        self.event = None
        self._hass = hass
        self.entities = []

    def add_entity(self, entity_id):
        """Append entity ID to the calendar"""
        if entity_id not in self.entities:
            self.entities.append(entity_id)

    def remove_entity(self, entity_id):
        """Remove entity ID from the calendar"""
        if entity_id in self.entities:
            self.entities.remove(entity_id)

    async def async_get_events(self, hass, start_datetime, end_datetime):
        """Get all tasks in a specific time frame."""
        events = []
        if SENSOR_PLATFORM not in hass.data[DOMAIN]:
            return events
        start_date = start_datetime.date()
        end_date = end_datetime.date()
        for entity in self.entities:
            # garbage_collection = find_entity(hass, entity)
            if (
                entity not in hass.data[DOMAIN][SENSOR_PLATFORM]
                or hass.data[DOMAIN][SENSOR_PLATFORM][entity].hidden
            ):
                continue
            garbage_collection = hass.data[DOMAIN][SENSOR_PLATFORM][entity]
            await garbage_collection.async_load_holidays(start_date)
            start = await garbage_collection.async_find_next_date(start_date)
            while start is not None and start >= start_date and start <= end_date:
                event = {
                    "uid": entity,
                    "summary": garbage_collection.name,
                    "start": {"date": start.strftime("%Y-%m-%d"),},
                    "end": {"date": start.strftime("%Y-%m-%d"),},
                    "allDay": True,
                }
                events.append(event)
                start = await garbage_collection.async_find_next_date(
                    start + timedelta(days=1)
                )
        return events

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    def update(self):
        """Get the latest data."""
        events = []
        for entity in self.entities:
            state_object = self._hass.states.get(entity)
            start = state_object.attributes.get("next_date")
            if start is not None:
                event = {
                    "uid": entity,
                    "summary": state_object.attributes.get("friendly_name"),
                    "start": {"date": start.strftime("%Y-%m-%d"),},
                    "end": {"date": start.strftime("%Y-%m-%d"),},
                    "allDay": True,
                }
                events.append(event)
        events.sort(key=lambda x: x["start"]["date"])
        if len(events) > 0:
            self.event = events[0]
