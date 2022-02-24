"""Sensor platform for garbage_collection."""
import asyncio
import logging
from datetime import date, datetime, time, timedelta
from typing import List, Optional

import homeassistant.util.dt as dt_util
from dateutil.relativedelta import relativedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_DEVICE_CLASS,
    ATTR_HIDDEN,
    CONF_ENTITIES,
    CONF_NAME,
    WEEKDAYS,
)
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.restore_state import RestoreEntity

from . import const, helpers
from .calendar import EntitiesCalendarData

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=10)
THROTTLE_INTERVAL = timedelta(seconds=60)


def now() -> datetime:
    """Return current date and time. Needed for testing."""
    return dt_util.now()


async def async_setup_entry(_, config_entry, async_add_devices):
    """Create garbage collection entities defined in config_flow and add them to HA."""
    async_add_devices([GarbageCollection(config_entry)], True)


def nth_week_date(week_number: int, date_of_month: date, collection_day: int) -> date:
    """Find weekday in the nth week of the month."""
    first_of_month = date(date_of_month.year, date_of_month.month, 1)
    return first_of_month + relativedelta(
        days=collection_day - first_of_month.weekday() + (week_number - 1) * 7
    )


def nth_weekday_date(
    weekday_number: int, date_of_month: date, collection_day: int
) -> date:
    """Find nth weekday of the month."""
    first_of_month = date(date_of_month.year, date_of_month.month, 1)
    # 1st of the month is before the day of collection
    # (so 1st collection week the week when month starts)
    if collection_day >= first_of_month.weekday():
        return first_of_month + relativedelta(
            days=collection_day - first_of_month.weekday() + (weekday_number - 1) * 7
        )
    return first_of_month + relativedelta(
        days=7 - first_of_month.weekday() + collection_day + (weekday_number - 1) * 7
    )


class GarbageCollection(RestoreEntity):
    """GarbageCollection Sensor class."""

    def __init__(self, config_entry: ConfigEntry):
        """Read configuration and initialise class variables."""
        config = config_entry.data
        self.config_entry = config_entry
        self._name = (
            config_entry.title
            if config_entry.title is not None
            else config.get(CONF_NAME)
        )
        self._hidden = config.get(ATTR_HIDDEN, False)
        self._frequency = config.get(const.CONF_FREQUENCY)
        self._manual = config.get(const.CONF_MANUAL)
        self._collection_days = config.get(const.CONF_COLLECTION_DAYS)
        first_month = config.get(const.CONF_FIRST_MONTH)
        self._first_month: int = (
            const.MONTH_OPTIONS.index(first_month) + 1
            if first_month in const.MONTH_OPTIONS
            else 1
        )
        last_month = config.get(const.CONF_LAST_MONTH)
        self._last_month: int = (
            const.MONTH_OPTIONS.index(last_month) + 1
            if last_month in const.MONTH_OPTIONS
            else 12
        )
        self._monthly_force_week_numbers = config.get(
            const.CONF_FORCE_WEEK_NUMBERS, False
        )
        self._weekday_order_numbers: List
        self._week_order_numbers: List
        order_numbers: List = []
        if const.CONF_WEEKDAY_ORDER_NUMBER in config:
            order_numbers = list(map(int, config.get(const.CONF_WEEKDAY_ORDER_NUMBER)))
        if self._monthly_force_week_numbers:
            self._weekday_order_numbers = []
            self._week_order_numbers = order_numbers
        else:
            self._weekday_order_numbers = order_numbers
            self._week_order_numbers = []
        self._period = config.get(const.CONF_PERIOD)
        self._first_week = config.get(const.CONF_FIRST_WEEK)
        self._first_date: Optional[date]
        try:
            self._first_date = helpers.to_date(config.get(const.CONF_FIRST_DATE))
        except ValueError:
            self._first_date = None
        self._collection_dates: List[date] = []
        self._next_date: Optional[date] = None
        self._last_updated: Optional[datetime] = None
        self.last_collection: Optional[datetime] = None
        self._days: Optional[int] = None
        self._date = config.get(const.CONF_DATE)
        self._entities = config.get(CONF_ENTITIES)
        self._verbose_state = config.get(const.CONF_VERBOSE_STATE)
        self._state = "" if bool(self._verbose_state) else 2
        self._icon_normal = config.get(const.CONF_ICON_NORMAL)
        self._icon_today = config.get(const.CONF_ICON_TODAY)
        self._icon_tomorrow = config.get(const.CONF_ICON_TOMORROW)
        exp = config.get(const.CONF_EXPIRE_AFTER)
        self.expire_after: Optional[time]
        self.expire_after = (
            None if exp is None else datetime.strptime(exp, "%H:%M").time()
        )
        self._date_format = config.get(
            const.CONF_DATE_FORMAT, const.DEFAULT_DATE_FORMAT
        )
        self._verbose_format = config.get(
            const.CONF_VERBOSE_FORMAT, const.DEFAULT_VERBOSE_FORMAT
        )
        self._icon = self._icon_normal

    async def async_added_to_hass(self):
        """When sensor is added to hassio, add it to calendar."""
        await super().async_added_to_hass()
        if const.DOMAIN not in self.hass.data:
            self.hass.data[const.DOMAIN] = {}
        if const.SENSOR_PLATFORM not in self.hass.data[const.DOMAIN]:
            self.hass.data[const.DOMAIN][const.SENSOR_PLATFORM] = {}
        self.hass.data[const.DOMAIN][const.SENSOR_PLATFORM][self.entity_id] = self

        state = await self.async_get_last_state()
        if state is not None:
            self.last_collection = helpers.parse_datetime(
                state.attributes.get(const.ATTR_LAST_COLLECTION)
            )

        device_registry = dr.async_get(self.hass)
        device_registry.async_get_or_create(
            config_entry_id=self.config_entry.entry_id,
            identifiers={(const.DOMAIN, self.unique_id)},
            name=self.name,
            manufacturer="bruxy70",
        )

        if not self.hidden:
            if const.CALENDAR_PLATFORM not in self.hass.data[const.DOMAIN]:
                self.hass.data[const.DOMAIN][
                    const.CALENDAR_PLATFORM
                ] = EntitiesCalendarData(self.hass)
                _LOGGER.debug("Creating garbage_collection calendar")
                self.hass.async_create_task(
                    async_load_platform(
                        self.hass,
                        const.CALENDAR_PLATFORM,
                        const.DOMAIN,
                        {"name": const.CALENDAR_NAME},
                        {"name": const.CALENDAR_NAME},
                    )
                )
            self.hass.data[const.DOMAIN][const.CALENDAR_PLATFORM].add_entity(
                self.entity_id
            )

    async def async_will_remove_from_hass(self):
        """When sensor is added to hassio, remove it."""
        await super().async_will_remove_from_hass()
        del self.hass.data[const.DOMAIN][const.SENSOR_PLATFORM][self.entity_id]
        self.hass.data[const.DOMAIN][const.CALENDAR_PLATFORM].remove_entity(
            self.entity_id
        )

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return self.config_entry.data.get("unique_id", None)

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(const.DOMAIN, self.unique_id)},
            "name": self.config_entry.data.get("name"),
            "manufacturer": "bruxy70",
        }

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def next_date(self):
        """Return next date attribute."""
        return self._next_date

    @property
    def hidden(self):
        """Return the hidden attribute."""
        return self._hidden

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def icon(self):
        """Return the entity icon."""
        return self._icon

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        res = {}
        if self._next_date is None:
            res[const.ATTR_NEXT_DATE] = None
        else:
            res[const.ATTR_NEXT_DATE] = datetime(
                self._next_date.year, self._next_date.month, self._next_date.day
            ).astimezone()
        res[const.ATTR_DAYS] = self._days
        res[const.ATTR_LAST_COLLECTION] = self.last_collection
        res[const.ATTR_LAST_UPDATED] = self._last_updated
        # Needed for translations to work
        res[ATTR_DEVICE_CLASS] = self.DEVICE_CLASS
        return res

    @property
    def DEVICE_CLASS(self):  # pylint: disable=C0103
        """Return the class of the sensor."""
        return const.DEVICE_CLASS

    def __repr__(self):
        """Return main sensor parameters."""
        return (
            f"GarbageCollection[name: {self._name}, "
            f"entity_id: {self.entity_id}, "
            f"state: {self.state}\n"
            f"attributes: {self.extra_state_attributes}]"
        )

    async def _async_monthly_candidate(self, day1: date) -> date:
        """Calculate possible date, for monthly frequency."""
        if self._monthly_force_week_numbers:
            for week_order_number in self._week_order_numbers:
                candidate_date = nth_week_date(
                    week_order_number, day1, WEEKDAYS.index(self._collection_days[0])
                )
                # date is today or in the future -> we have the date
                if candidate_date >= day1:
                    return candidate_date
        else:
            for weekday_order_number in self._weekday_order_numbers:
                candidate_date = nth_weekday_date(
                    weekday_order_number,
                    day1,
                    WEEKDAYS.index(self._collection_days[0]),
                )
                # date is today or in the future -> we have the date
                if candidate_date >= day1:
                    return candidate_date
        if day1.month == 12:
            next_collection_month = date(day1.year + 1, 1, 1)
        else:
            next_collection_month = date(day1.year, day1.month + 1, 1)
        if self._monthly_force_week_numbers:
            return nth_week_date(
                self._week_order_numbers[0],
                next_collection_month,
                WEEKDAYS.index(self._collection_days[0]),
            )
        return nth_weekday_date(
            self._weekday_order_numbers[0],
            next_collection_month,
            WEEKDAYS.index(self._collection_days[0]),
        )

    async def _async_weekly_candidate(
        self, day1: date, period: int, first_week: int
    ) -> date:
        """Calculate possible date, for weekly frequency."""
        week = day1.isocalendar()[1]
        weekday = day1.weekday()
        offset = -1
        if (week - first_week) % period == 0:  # Collection this week
            for day_name in self._collection_days:
                day_index = WEEKDAYS.index(day_name)
                if day_index >= weekday:  # Collection still did not happen
                    offset = day_index - weekday
                    break
        iterate_by_week = 7 - weekday + WEEKDAYS.index(self._collection_days[0])
        while offset == -1:  # look in following weeks
            candidate = day1 + relativedelta(days=iterate_by_week)
            week = candidate.isocalendar()[1]
            if (week - first_week) % period == 0:
                offset = iterate_by_week
                break
            iterate_by_week += 7
        return day1 + relativedelta(days=offset)

    async def _async_daily_candidate(self, day1: date) -> date:
        """Calculate possible date, for every-n-days frequency."""
        try:
            if (day1 - self._first_date).days % self._period == 0:  # type: ignore
                return day1
            offset = self._period - (
                (day1 - self._first_date).days % self._period  # type: ignore
            )
        except TypeError as error:
            raise ValueError(
                f"({self._name}) Please configure first_date and period "
                "for every-n-days collection frequency."
            ) from error
        return day1 + relativedelta(days=offset)

    async def _async_annual_candidate(self, day1: date) -> date:
        """Calculate possible date, for annual frequency."""
        year = day1.year
        try:
            conf_date = datetime.strptime(self._date, "%m/%d").date()
        except TypeError as error:
            raise ValueError(
                f"({self._name}) Please configure the date "
                "for annual collection frequency."
            ) from error
        candidate_date = date(year, conf_date.month, conf_date.day)
        if candidate_date < day1:
            candidate_date = date(year + 1, conf_date.month, conf_date.day)
        return candidate_date

    async def _async_find_candidate_date(self, day1: date) -> Optional[date]:
        """Find the next possible date starting from day1.

        Only based on calendar, not looking at include/exclude days.
        """
        if self._frequency == "blank":
            return None
        if self._frequency in ["weekly", "even-weeks", "odd-weeks", "every-n-weeks"]:
            # convert weekly and even/odd weeks to every-n-weeks
            if self._frequency == "weekly":
                period = 1
                first_week = 1
            elif self._frequency == "even-weeks":
                period = 2
                first_week = 2
            elif self._frequency == "odd-weeks":
                period = 2
                first_week = 1
            else:
                period = self._period
                first_week = self._first_week
            return await self._async_weekly_candidate(day1, period, first_week)
        elif self._frequency == "every-n-days":
            return await self._async_daily_candidate(day1)
        elif self._frequency == "monthly":
            if self._period is None or self._period == 1:
                return await self._async_monthly_candidate(day1)
            else:
                candidate_date = await self._async_monthly_candidate(day1)
                while (candidate_date.month - self._first_month) % self._period != 0:
                    candidate_date = await self._async_monthly_candidate(
                        candidate_date + relativedelta(days=1)
                    )
                return candidate_date
        elif self._frequency == "annual":
            return await self._async_annual_candidate(day1)
        elif self._frequency == "group":
            candidate_date = None
            try:
                for entity_id in self._entities:
                    entity = self.hass.data[const.DOMAIN][const.SENSOR_PLATFORM][
                        entity_id
                    ]
                    next_date = await entity.async_next_date(day1)
                    if next_date is not None and (
                        candidate_date is None or next_date < candidate_date
                    ):
                        candidate_date = next_date
            except KeyError as error:
                raise ValueError from error
            except TypeError as error:
                _LOGGER.error("(%s) Please add entities for the group.", self._name)
                raise ValueError from error
            return candidate_date
        _LOGGER.error("(%s) Unknown frequency %s", self._name, self._frequency)
        raise ValueError

    async def _async_ready_for_update(self) -> bool:
        """Check if the entity is ready for the update.

        Skip the update if the sensor was updated today
        Except for the sensors with with next date today and after the expiration time
        For group sensors wait for update of the sensors in the group
        """
        current_date_time = now()
        today = current_date_time.date()
        try:
            ready_for_update = bool(self._last_updated.date() != today)  # type: ignore
        except AttributeError:
            ready_for_update = True
        if self._frequency == "group":
            members_ready = True
            for entity_id in self._entities:
                state_object = self.hass.states.get(entity_id)
                try:
                    # Wait for all members to get updated
                    if (
                        state_object.attributes.get(const.ATTR_LAST_UPDATED).date()
                        != today
                    ):
                        members_ready = False
                        break
                    # A member got updated after the group update
                    if (
                        state_object.attributes.get(const.ATTR_LAST_UPDATED)
                        > self._last_updated
                    ):
                        ready_for_update = True
                except AttributeError:
                    members_ready = False
                    break
                except TypeError:
                    ready_for_update = True
            if ready_for_update and not members_ready:
                ready_for_update = False
        else:
            try:
                if self._next_date == today and (
                    (
                        isinstance(self.expire_after, time)
                        and current_date_time.time() >= self.expire_after
                    )
                    or (
                        isinstance(self.last_collection, datetime)
                        and self.last_collection.date() == today
                    )
                ):
                    ready_for_update = True
            except (AttributeError, TypeError):
                pass
        return ready_for_update

    def date_inside(self, dat: date) -> bool:
        """Check if the date is inside first and last date."""
        month = dat.month
        if self._first_month <= self._last_month:
            return bool(month >= self._first_month and month <= self._last_month)
        return bool(month <= self._last_month or month >= self._first_month)

    def move_to_range(self, day: date) -> date:
        """If the date is not in range, move to the range."""
        if not self.date_inside(day):
            year = day.year
            month = day.month
            if self._first_month <= self._last_month and month > self._last_month:
                _LOGGER.debug(
                    "(%s) %s outside the range, lookig from %s next year",
                    self._name,
                    day,
                    const.MONTH_OPTIONS[self._first_month - 1],
                )
                return date(year + 1, self._first_month, 1)
            else:
                _LOGGER.debug(
                    "(%s) %s outside the range, searching from %s",
                    self._name,
                    day,
                    const.MONTH_OPTIONS[self._first_month - 1],
                )
                return date(year, self._first_month, 1)
        return day

    async def _async_find_next_date(self, first_date: date) -> Optional[date]:
        """Get date within configured date range."""
        # Today's collection can be triggered by past collection with offset
        if self._frequency == "blank":
            return None
        # Move starting date if today is out of range
        day1 = self.move_to_range(first_date)
        next_date = None
        while next_date is None:
            try:
                next_date = await self._async_find_candidate_date(day1)
            except (TypeError, ValueError):
                return None
            if next_date is None:
                return None
            # Check if the date is within the range
            new_date = self.move_to_range(next_date)
            if new_date != next_date:
                day1 = new_date  # continue from next year
                next_date = None
            else:
                # Date is before starting date
                if next_date < first_date:
                    next_date = None
                day1 += relativedelta(days=1)  # look from the next day
        return next_date

    async def _async_load_collection_dates(self) -> None:
        """Fill the collection dates list."""
        if self._frequency == "blank":
            return
        today = now().date()
        start_date = end_date = date(today.year - 1, 1, 1)
        end_date = date(today.year + 1, 12, 31)

        self._collection_dates.clear()
        try:
            next_date = await self._async_find_next_date(start_date)
        except asyncio.TimeoutError:
            _LOGGER.error("(%s) Timeout loading collection dates", self._name)
            return

        while (
            next_date is not None and next_date >= start_date and next_date <= end_date
        ):
            self._collection_dates.append(next_date)
            next_date = await self._async_find_next_date(next_date + timedelta(days=1))
        self._collection_dates.sort()

    async def add_date(self, collection_date: date) -> None:
        """Add date to _collection_dates."""
        if collection_date not in self._collection_dates:
            self._collection_dates.append(collection_date)
            self._collection_dates.sort()
        else:
            _LOGGER.error(
                "%s not added to %s - already on the collection schedule",
                collection_date,
                self.name,
            )

    async def remove_date(self, collection_date: date) -> None:
        """Remove date from _collection dates."""
        try:
            self._collection_dates.remove(collection_date)
        except ValueError:
            _LOGGER.error(
                "%s not removed from %s - not in the collection schedule",
                collection_date,
                self.name,
            )

    async def async_next_date(
        self, first_date: date, ignore_today=False
    ) -> Optional[date]:
        """Get next date from self._collection_dates."""
        current_date_time = now()
        for d in self._collection_dates:  # pylint: disable=invalid-name
            if d < first_date:
                continue
            if not ignore_today and d == current_date_time.date():
                expiration = (
                    self.expire_after
                    if self.expire_after is not None
                    else time(23, 59, 59)
                )
                if current_date_time.time() > expiration or (
                    self.last_collection is not None
                    and self.last_collection.date() == current_date_time.date()
                    and current_date_time.time() >= self.last_collection.time()
                ):
                    continue
            return d
        return None

    async def async_update(self) -> None:
        """Get the latest data and updates the states."""
        if not await self._async_ready_for_update() or not self.hass.is_running:
            return

        _LOGGER.debug("(%s) Calling update", self._name)
        await self._async_load_collection_dates()
        _LOGGER.debug(
            "(%s) Dates loaded, firing a garbage_collection_loaded event", self._name
        )
        event_data = {
            "entity_id": self.entity_id,
            "collection_dates": helpers.dates_to_texts(self._collection_dates),
        }
        self.hass.bus.async_fire("garbage_collection_loaded", event_data)
        if not self._manual and self._frequency != "blank":
            await self.async_update_state()

    async def async_update_state(self) -> None:
        """Pick the first event from collection dates, update attributes."""
        _LOGGER.debug("(%s) Looking for next collection", self._name)
        today = now().date()
        self._next_date = await self.async_next_date(today)
        self._last_updated = now()
        if self._next_date is not None:
            _LOGGER.debug(
                "(%s) next_date (%s), today (%s)", self._name, self._next_date, today
            )
            self._days = (self._next_date - today).days
            next_date_txt = self._next_date.strftime(self._date_format)
            _LOGGER.debug(
                "(%s) Found next collection date: %s, that is in %d days",
                self._name,
                next_date_txt,
                self._days,
            )
            if self._days > 1:
                if bool(self._verbose_state):
                    self._state = self._verbose_format.format(
                        date=next_date_txt, days=self._days
                    )
                    # self._state = "on_date"
                else:
                    self._state = 2
                self._icon = self._icon_normal
            else:
                if self._days == 0:
                    if bool(self._verbose_state):
                        self._state = const.STATE_TODAY
                    else:
                        self._state = self._days
                    self._icon = self._icon_today
                elif self._days == 1:
                    if bool(self._verbose_state):
                        self._state = const.STATE_TOMORROW
                    else:
                        self._state = self._days
                    self._icon = self._icon_tomorrow
        else:
            self._days = None
