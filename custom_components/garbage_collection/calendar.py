"""Garbage collection calendar."""

import logging
from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEventDevice
from homeassistant.util import Throttle

from .const import CALENDAR_NAME, CALENDAR_PLATFORM, DOMAIN, SENSOR_PLATFORM

_LOGGER = logging.getLogger(__name__)
MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)


async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
):  # pylint: disable=unused-argument
    """Add calendar entities to HA, of there are calendar instances."""
    # Only single instance allowed
    if GarbageCollectionCalendar.instances == 0:
        async_add_entities([GarbageCollectionCalendar(hass)], True)


class GarbageCollectionCalendar(CalendarEventDevice):
    """The garbage collection calendar class."""

    instances = 0

    def __init__(self, hass):
        """Create empry calendar."""
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
        await self.hass.data[DOMAIN][CALENDAR_PLATFORM].async_update()

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
    """Class used by the Entities Calendar class to hold all entity events."""

    def __init__(self, hass):
        """Initialize an Entities Calendar Data."""
        self.event = None
        self._hass = hass
        self.entities = []

    def add_entity(self, entity_id):
        """Append entity ID to the calendar."""
        if entity_id not in self.entities:
            self.entities.append(entity_id)

    def remove_entity(self, entity_id):
        """Remove entity ID from the calendar."""
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
            if (
                entity not in hass.data[DOMAIN][SENSOR_PLATFORM]
                or hass.data[DOMAIN][SENSOR_PLATFORM][entity].hidden
            ):
                continue
            garbage_collection = hass.data[DOMAIN][SENSOR_PLATFORM][entity]
            await garbage_collection.async_load_holidays(start_date)
            start = await garbage_collection.async_find_next_date(start_date, True)
            while start is not None and start >= start_date and start <= end_date:
                try:
                    end = start + timedelta(days=1)
                except TypeError:
                    end = start
                if garbage_collection.expire_after is None:
                    event = {
                        "uid": entity,
                        "summary": garbage_collection.name,
                        "start": {"date": start.strftime("%Y-%m-%d")},
                        "end": {"date": end.strftime("%Y-%m-%d")},
                        "allDay": True,
                    }
                else:
                    event = {
                        "uid": entity,
                        "summary": garbage_collection.name,
                        "start": {
                            "date": datetime.combine(
                                start, garbage_collection.expire_after
                            ).strftime("%Y-%m-%d %H:%M")
                        },
                        "end": {
                            "date": datetime.combine(
                                start, garbage_collection.expire_after
                            ).strftime("%Y-%m-%d %H:%M")
                        },
                        "allDay": False,
                    }
                events.append(event)
                start = await garbage_collection.async_find_next_date(
                    start + timedelta(days=1), True
                )
        return events

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Get the latest data."""
        next_dates = {}
        for entity in self.entities:
            if self._hass.data[DOMAIN][SENSOR_PLATFORM][entity]._next_date is not None:
                next_dates[entity] = self._hass.data[DOMAIN][SENSOR_PLATFORM][
                    entity
                ]._next_date
        if len(next_dates) > 0:
            entity_id = min(next_dates.keys(), key=(lambda k: next_dates[k]))
            start = next_dates[entity_id]
            end = start + timedelta(days=1)
            name = self._hass.data[DOMAIN][SENSOR_PLATFORM][entity_id].name
            self.event = {
                "uid": entity_id,
                "summary": name,
                "start": {"date": start.strftime("%Y-%m-%d")},
                "end": {"date": end.strftime("%Y-%m-%d")},
                "allDay": True,
            }
