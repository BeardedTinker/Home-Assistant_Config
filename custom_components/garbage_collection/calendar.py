"""Garbage collection calendar."""
from __future__ import annotations

from datetime import datetime, timedelta

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util import Throttle

from .const import CALENDAR_NAME, CALENDAR_PLATFORM, DOMAIN, SENSOR_PLATFORM

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)


async def async_setup_entry(
    _: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    # pylint: disable=unused-argument
    """Add calendar entity to HA."""
    async_add_entities([GarbageCollectionCalendar()], True)


class GarbageCollectionCalendar(CalendarEntity):
    """The garbage collection calendar class."""

    instances = False

    def __init__(self) -> None:
        """Create empty calendar."""
        self._cal_data: dict = {}
        self._attr_name = CALENDAR_NAME
        GarbageCollectionCalendar.instances = True

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event."""
        return self.hass.data[DOMAIN][CALENDAR_PLATFORM].event

    @property
    def name(self) -> str | None:
        """Return the name of the entity."""
        return self._attr_name

    async def async_update(self) -> None:
        """Update all calendars."""
        await self.hass.data[DOMAIN][CALENDAR_PLATFORM].async_update()

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> list[CalendarEvent]:
        """Get all events in a specific time frame."""
        return await self.hass.data[DOMAIN][CALENDAR_PLATFORM].async_get_events(
            hass, start_date, end_date
        )

    @property
    def extra_state_attributes(self) -> dict | None:
        """Return the device state attributes."""
        if self.hass.data[DOMAIN][CALENDAR_PLATFORM].event is None:
            # No tasks, we don't need to show anything.
            return None
        return {}


class EntitiesCalendarData:
    """Class used by the Entities Calendar class to hold all entity events."""

    __slots__ = "_hass", "event", "entities", "_throttle"

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize an Entities Calendar Data."""
        self._hass = hass
        self.event: CalendarEvent | None = None
        self.entities: list[str] = []

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
    ) -> list[CalendarEvent]:
        """Get all tasks in a specific time frame."""
        events: list[CalendarEvent] = []
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
            start = garbage_collection.get_next_date(start_date, True)
            while start is not None and start_date <= start <= end_date:
                try:
                    end = start + timedelta(days=1)
                except TypeError:
                    end = start
                name = (
                    garbage_collection.name
                    if garbage_collection.name is not None
                    else "Unknown"
                )
                if garbage_collection.expire_after is None:
                    event = CalendarEvent(
                        summary=name,
                        start=start,
                        end=end,
                    )
                else:
                    event = CalendarEvent(
                        summary=name,
                        start=datetime.combine(start, datetime.min.time()),
                        end=datetime.combine(start, garbage_collection.expire_after),
                    )
                events.append(event)
                start = garbage_collection.get_next_date(
                    start + timedelta(days=1), True
                )
        return events

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
    async def async_update(self) -> None:
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
            self.event = CalendarEvent(
                summary=name,
                start=start,
                end=end,
            )
