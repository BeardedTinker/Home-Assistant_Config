"""Garbage collection calendar."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from homeassistant.components.calendar import CalendarEventDevice
from homeassistant.core import HomeAssistant
from homeassistant.util import Throttle

from .const import CALENDAR_NAME, CALENDAR_PLATFORM, DOMAIN, SENSOR_PLATFORM

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)


async def async_setup_platform(
    hass, config, async_add_entities, discovery_info=None
):  # pylint: disable=unused-argument
    """Add calendar entities to HA, of there are calendar instances."""
    # Only single instance allowed
    if not GarbageCollectionCalendar.instances:
        async_add_entities([GarbageCollectionCalendar()], True)


class GarbageCollectionCalendar(CalendarEventDevice):
    """The garbage collection calendar class."""

    instances = False

    def __init__(self):
        """Create empty calendar."""
        self._cal_data: Dict = {}
        self._name = CALENDAR_NAME
        GarbageCollectionCalendar.instances = True

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

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ):
        """Get all events in a specific time frame."""
        return await self.hass.data[DOMAIN][CALENDAR_PLATFORM].async_get_events(
            hass, start_date, end_date
        )

    @property
    def extra_state_attributes(self):
        """Return the device state attributes."""
        if self.hass.data[DOMAIN][CALENDAR_PLATFORM].event is None:
            # No tasks, we don't need to show anything.
            return None
        return {}


class EntitiesCalendarData:
    """Class used by the Entities Calendar class to hold all entity events."""

    def __init__(self, hass: HomeAssistant):
        """Initialize an Entities Calendar Data."""
        self.event: Optional[Dict] = None
        self._hass = hass
        self.entities: List[str] = []

    def add_entity(self, entity_id: str) -> None:
        """Append entity ID to the calendar."""
        if entity_id not in self.entities:
            self.entities.append(entity_id)

    def remove_entity(self, entity_id: str) -> None:
        """Remove entity ID from the calendar."""
        if entity_id in self.entities:
            self.entities.remove(entity_id)

    async def async_get_events(
        self, hass: HomeAssistant, start_datetime: datetime, end_datetime: datetime
    ) -> List[Dict]:
        """Get all tasks in a specific time frame."""
        events: List[Dict] = []
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
            start = await garbage_collection.async_next_date(start_date, True)
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
                start = await garbage_collection.async_next_date(
                    start + timedelta(days=1), True
                )
        return events

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self):
        """Get the latest data."""
        next_dates = {}
        for entity in self.entities:
            if self._hass.data[DOMAIN][SENSOR_PLATFORM][entity].next_date is not None:
                next_dates[entity] = self._hass.data[DOMAIN][SENSOR_PLATFORM][
                    entity
                ].next_date
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
