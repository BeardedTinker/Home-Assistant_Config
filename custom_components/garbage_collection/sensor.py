"""Sensor platform for garbage_collection."""
import asyncio
import logging
from datetime import date, datetime, time, timedelta
from typing import Any, List, Optional, Union

import holidays
import homeassistant.util.dt as dt_util
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from homeassistant.const import ATTR_HIDDEN, CONF_ENTITIES, CONF_NAME, WEEKDAYS
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.restore_state import RestoreEntity

from .calendar import EntitiesCalendarData
from .const import (
    ATTR_DAYS,
    ATTR_HOLIDAYS,
    ATTR_LAST_COLLECTION,
    ATTR_LAST_UPDATED,
    ATTR_NEXT_DATE,
    CALENDAR_NAME,
    CALENDAR_PLATFORM,
    CONF_COLLECTION_DAYS,
    CONF_DATE,
    CONF_DATE_FORMAT,
    CONF_EXCLUDE_DATES,
    CONF_EXPIRE_AFTER,
    CONF_FIRST_DATE,
    CONF_FIRST_MONTH,
    CONF_FIRST_WEEK,
    CONF_FREQUENCY,
    CONF_HOLIDAY_IN_WEEK_MOVE,
    CONF_HOLIDAY_MOVE_OFFSET,
    CONF_HOLIDAY_POP_NAMED,
    CONF_ICON_NORMAL,
    CONF_ICON_TODAY,
    CONF_ICON_TOMORROW,
    CONF_INCLUDE_DATES,
    CONF_LAST_MONTH,
    CONF_MOVE_COUNTRY_HOLIDAYS,
    CONF_OBSERVED,
    CONF_OFFSET,
    CONF_PERIOD,
    CONF_PROV,
    CONF_STATE,
    CONF_VERBOSE_FORMAT,
    CONF_VERBOSE_STATE,
    CONF_WEEK_ORDER_NUMBER,
    CONF_WEEKDAY_ORDER_NUMBER,
    DEFAULT_DATE_FORMAT,
    DEFAULT_VERBOSE_FORMAT,
    DEVICE_CLASS,
    DOMAIN,
    MONTH_OPTIONS,
    SENSOR_PLATFORM,
    STATE_TODAY,
    STATE_TOMORROW,
)

_LOGGER = logging.getLogger(__name__)

SCAN_INTERVAL = timedelta(seconds=60)
THROTTLE_INTERVAL = timedelta(seconds=60)


_LOGGER = logging.getLogger(__name__)


async def async_setup_platform(hass, _, async_add_entities, discovery_info=None):
    """Create garbage collection entities defined in YAML and add them to HA."""
    async_add_entities([GarbageCollection(hass, discovery_info)], True)


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Create garbage collection entities defined in config_flow and add them to HA."""
    async_add_devices(
        [GarbageCollection(hass, config_entry.data, config_entry.title)], True
    )


def nth_week_date(n: int, date_of_month: date, collection_day: int) -> date:
    """Find weekday in the nth week of the month."""
    first_of_month = date(date_of_month.year, date_of_month.month, 1)
    return first_of_month + relativedelta(
        days=collection_day - first_of_month.weekday() + (n - 1) * 7
    )


def nth_weekday_date(n: int, date_of_month: date, collection_day: int) -> date:
    """Find nth weekday of the month."""
    first_of_month = date(date_of_month.year, date_of_month.month, 1)
    # 1st of the month is before the day of collection
    # (so 1st collection week the week when month starts)
    if collection_day >= first_of_month.weekday():
        return first_of_month + relativedelta(
            days=collection_day - first_of_month.weekday() + (n - 1) * 7
        )
    return first_of_month + relativedelta(
        days=7 - first_of_month.weekday() + collection_day + (n - 1) * 7
    )


def to_date(day: Any) -> date:
    """Convert datetime or text to date, if not already datetime."""
    if day is None:
        raise ValueError
    if type(day) == date:
        return day
    if type(day) == datetime:
        return day.date()
    return date.fromisoformat(day)


def parse_datetime(text: str) -> Optional[datetime]:
    """Parse text to datetime object."""
    try:
        return parse(text)
    except Exception:
        return None


def parse_date(text: str) -> Optional[date]:
    """Parse text to date object."""
    try:
        return parse(text).date()
    except Exception:
        return None


def to_dates(dates: List[Any]) -> List[date]:
    """Convert list of text to datetimes, if not already datetimes."""
    converted = []  # type: List[date]
    for day in dates:
        try:
            converted.append(to_date(day))
        except ValueError:
            continue
    return converted


class GarbageCollection(RestoreEntity):
    """GarbageCollection Sensor class."""

    def __init__(self, hass, config, title=None):
        """Read configuration and initialise class variables."""
        self.config = config
        self._name = title if title is not None else config.get(CONF_NAME)
        self._hidden = config.get(ATTR_HIDDEN, False)
        self._frequency = config.get(CONF_FREQUENCY)
        self._collection_days = config.get(CONF_COLLECTION_DAYS)
        first_month = config.get(CONF_FIRST_MONTH)
        if first_month in MONTH_OPTIONS:
            self._first_month = MONTH_OPTIONS.index(first_month) + 1
        else:
            self._first_month = 1
        last_month = config.get(CONF_LAST_MONTH)
        if last_month in MONTH_OPTIONS:
            self._last_month = MONTH_OPTIONS.index(last_month) + 1
        else:
            self._last_month = 12
        self._weekday_order_numbers = config.get(CONF_WEEKDAY_ORDER_NUMBER)
        self._week_order_numbers = config.get(CONF_WEEK_ORDER_NUMBER)
        self._monthly_force_week_numbers = bool(
            self._week_order_numbers is not None and len(self._week_order_numbers) != 0
        )
        self._include_dates = to_dates(config.get(CONF_INCLUDE_DATES, []))
        self._exclude_dates = to_dates(config.get(CONF_EXCLUDE_DATES, []))
        self._country_holidays = config.get(CONF_MOVE_COUNTRY_HOLIDAYS)
        self._holiday_move_offset = config.get(CONF_HOLIDAY_MOVE_OFFSET, 1)
        self._holiday_pop_named = config.get(CONF_HOLIDAY_POP_NAMED)
        self._holiday_in_week_move = config.get(CONF_HOLIDAY_IN_WEEK_MOVE)
        self._holiday_prov = config.get(CONF_PROV)
        self._holiday_state = config.get(CONF_STATE)
        self._holiday_observed = config.get(CONF_OBSERVED, True)
        self._holidays = []
        self._holidays_log = ""
        self._period = config.get(CONF_PERIOD)
        self._first_week = config.get(CONF_FIRST_WEEK)
        try:
            self._first_date = to_date(config.get(CONF_FIRST_DATE))
        except ValueError:
            self._first_date = None
        self._next_date = None
        self._last_updated = None
        self.last_collection = None
        self._days = None
        self._date = config.get(CONF_DATE)
        self._entities = config.get(CONF_ENTITIES)
        self._verbose_state = config.get(CONF_VERBOSE_STATE)
        self._state = "" if bool(self._verbose_state) else 2
        self._offset = config.get(CONF_OFFSET, 0)
        self._icon_normal = config.get(CONF_ICON_NORMAL)
        self._icon_today = config.get(CONF_ICON_TODAY)
        self._icon_tomorrow = config.get(CONF_ICON_TOMORROW)
        exp = config.get(CONF_EXPIRE_AFTER)
        self.expire_after = (
            None if exp is None else datetime.strptime(exp, "%H:%M").time()
        )
        self._date_format = config.get(CONF_DATE_FORMAT, DEFAULT_DATE_FORMAT)
        self._verbose_format = config.get(CONF_VERBOSE_FORMAT, DEFAULT_VERBOSE_FORMAT)
        self._icon = self._icon_normal

    async def async_load_holidays(self, today: date) -> None:
        """Load the holidays from from a date."""
        self._holidays_log = ""
        log = ""
        year_from_today = today + relativedelta(years=1)
        self._holidays.clear()
        if self._country_holidays is not None and self._country_holidays != "":
            this_year = today.year
            years = [this_year - 1, this_year, this_year + 1]
            _LOGGER.debug(
                "(%s) Country Holidays with parameters: "
                "country: %s, prov: %s, state: %s, observed: %s",
                self._name,
                self._country_holidays,
                self._holiday_prov,
                self._holiday_state,
                self._holiday_observed,
            )
            kwargs = {"years": years}
            if self._holiday_state is not None and self._holiday_state != "":
                kwargs["state"] = self._holiday_state
            if self._holiday_prov is not None and self._holiday_prov != "":
                kwargs["prov"] = self._holiday_prov
            if (
                self._holiday_observed is not None
                and type(self._holiday_observed) == bool
                and not self._holiday_observed
            ):
                kwargs["observed"] = self._holiday_observed
            hol = holidays.CountryHoliday(self._country_holidays, **kwargs)
            if self._holiday_pop_named is not None:
                for pop in self._holiday_pop_named:
                    try:
                        hol.pop_named(pop)
                    except Exception as err:
                        _LOGGER.error("(%s) Holiday not removed (%s)", self._name, err)
            try:
                for d, name in hol.items():
                    self._holidays.append(d)
                    log += f"\n  {d}: {name}"
                    if d >= today and d <= year_from_today:
                        self._holidays_log += f"\n  {d}: {name}"
            except KeyError:
                _LOGGER.error(
                    "(%s) Invalid country code (%s)",
                    self._name,
                    self._country_holidays,
                )
            _LOGGER.debug("(%s) Found these holidays: %s", self._name, log)

    async def async_added_to_hass(self):
        """When sensor is added to hassio, add it to calendar."""
        await super().async_added_to_hass()
        if DOMAIN not in self.hass.data:
            self.hass.data[DOMAIN] = {}
        if SENSOR_PLATFORM not in self.hass.data[DOMAIN]:
            self.hass.data[DOMAIN][SENSOR_PLATFORM] = {}
        self.hass.data[DOMAIN][SENSOR_PLATFORM][self.entity_id] = self

        state = await self.async_get_last_state()
        if state is not None:
            self.last_collection = parse_datetime(
                state.attributes.get(ATTR_LAST_COLLECTION)
            )

        if not self.hidden:
            if CALENDAR_PLATFORM not in self.hass.data[DOMAIN]:
                self.hass.data[DOMAIN][CALENDAR_PLATFORM] = EntitiesCalendarData(
                    self.hass
                )
                _LOGGER.debug("Creating garbage_collection calendar")
                self.hass.async_create_task(
                    async_load_platform(
                        self.hass,
                        CALENDAR_PLATFORM,
                        DOMAIN,
                        {"name": CALENDAR_NAME},
                        {"name": CALENDAR_NAME},
                    )
                )
            self.hass.data[DOMAIN][CALENDAR_PLATFORM].add_entity(self.entity_id)

    async def async_will_remove_from_hass(self):
        """When sensor is added to hassio, remove it."""
        await super().async_will_remove_from_hass()
        del self.hass.data[DOMAIN][SENSOR_PLATFORM][self.entity_id]
        self.hass.data[DOMAIN][CALENDAR_PLATFORM].remove_entity(self.entity_id)

    @property
    def unique_id(self):
        """Return a unique ID to use for this sensor."""
        return self.config.get("unique_id", None)

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self.config.get("unique_id", None))},
            "name": self.config.get("name"),
            "manufacturer": "Garbage Collection",
        }

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

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
    def device_state_attributes(self):
        """Return the state attributes."""
        res = {}
        if self._next_date is None:
            res[ATTR_NEXT_DATE] = None
        else:
            res[ATTR_NEXT_DATE] = datetime(
                self._next_date.year, self._next_date.month, self._next_date.day
            ).astimezone()
        res[ATTR_DAYS] = self._days
        res[ATTR_LAST_COLLECTION] = self.last_collection
        res[ATTR_LAST_UPDATED] = self._last_updated
        res[ATTR_HOLIDAYS] = self._holidays_log
        return res

    @property
    def device_class(self):
        """Return the class of the sensor."""
        return DEVICE_CLASS

    def __repr__(self):
        """Return main sensor parameters."""
        return (
            f"Garbagecollection[ name: {self._name}, "
            f"entity_id: {self.entity_id}, "
            f"state: {self.state}\n"
            f"config: {self.config}]"
        )

    def date_inside(self, dat: date) -> bool:
        """Check if the date is inside first and last date."""
        month = dat.month
        if self._first_month <= self._last_month:
            return bool(month >= self._first_month and month <= self._last_month)
        return bool(month <= self._last_month or month >= self._first_month)

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

    async def _async_find_candidate_date(self, day1: date) -> date:
        """Find the next possible date starting from day1.

        Only based on calendar, not looking at include/exclude days.
        """
        week = day1.isocalendar()[1]
        weekday = day1.weekday()
        year = day1.year
        if self._frequency in ["weekly", "even-weeks", "odd-weeks", "every-n-weeks"]:
            # Everything except montthly
            # convert to every-n-weeks
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
        elif self._frequency == "every-n-days":
            try:
                if (day1 - self._first_date).days % self._period == 0:
                    return day1
                offset = self._period - ((day1 - self._first_date).days % self._period)
            except TypeError:
                raise ValueError(
                    f"({self._name}) Please configure first_date and period "
                    "for every-n-days collection frequency."
                )
            return day1 + relativedelta(days=offset)
        elif self._frequency == "monthly":
            # Monthly
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
            # Annual
            try:
                conf_date = datetime.strptime(self._date, "%m/%d").date()
            except TypeError:
                raise ValueError(
                    f"({self._name}) Please configure the date "
                    "for annual collection frequency."
                )
            candidate_date = date(year, conf_date.month, conf_date.day)
            if candidate_date < day1:
                candidate_date = date(year + 1, conf_date.month, conf_date.day)
            return candidate_date
        elif self._frequency == "group":
            candidate_date = None  # type: ignore
            try:
                for entity_id in self._entities:
                    entity = self.hass.data[DOMAIN][SENSOR_PLATFORM][entity_id]
                    d = await entity.async_find_next_date(day1)
                    if candidate_date is None or d < candidate_date:
                        candidate_date = d
            except KeyError:
                raise ValueError
            except TypeError:
                _LOGGER.error("(%s) Please add entities for the group.", self._name)
                raise ValueError
            return candidate_date
        _LOGGER.error("(%s) Unknown frequency %s", self._name, self._frequency)
        raise ValueError

    async def _async_skip_holidays(self, date_candidate: date) -> date:
        """Skip holidays."""
        if self._holiday_in_week_move:
            holidays_in_week = list(
                filter(
                    lambda date: date
                    >= (date_candidate - relativedelta(days=date_candidate.weekday()))
                    and date <= date_candidate,
                    self._holidays,
                )
            )
            if len(holidays_in_week) > 0:
                _LOGGER.debug(
                    "(%s) Move possible collection day, "
                    "because public holiday in week on %s",
                    self._name,
                    date_candidate,
                )
                date_candidate = self._skip_holiday(date_candidate)
        while date_candidate in self._holidays:
            _LOGGER.debug(
                "(%s) Skipping public holiday on %s", self._name, date_candidate
            )
            date_candidate = self._skip_holiday(date_candidate)
        return date_candidate

    def _insert_include_date(
        self, day1: date, next_date: Union[date, None]
    ) -> Union[date, None]:
        """Add include dates."""
        include_dates = list(filter(lambda date: date >= day1, self._include_dates))
        if len(include_dates) > 0 and (
            next_date is None or include_dates[0] < next_date
        ):
            _LOGGER.debug(
                "(%s) Inserting include_date %s", self._name, include_dates[0]
            )
            return include_dates[0]
        return next_date

    def _skip_holiday(self, day: date) -> date:
        """Move holidays by holiday move offset."""
        skip_days = (
            1
            if self._holiday_move_offset is None or self._holiday_move_offset == 0
            else self._holiday_move_offset
        )
        return day + relativedelta(days=skip_days)

    async def _async_ready_for_update(self) -> bool:
        """Check if the entity is ready for the update.

        Skip the update if the sensor was updated today
        Except for the sensors with with next date today and after the expiration time
        For group sensors wait for update of the sensors in the group
        """
        now = dt_util.now()
        today = now.date()
        try:
            ready_for_update = bool(self._last_updated.date() != today)
        except AttributeError:
            ready_for_update = True
        if self._frequency == "group":
            members_ready = True
            for entity_id in self._entities:
                state_object = self.hass.states.get(entity_id)
                try:
                    # Wait for all members to get updated
                    if state_object.attributes.get(ATTR_LAST_UPDATED).date() != today:
                        members_ready = False
                        break
                    # A member got updated after the group update
                    if (
                        state_object.attributes.get(ATTR_LAST_UPDATED)
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
                    now.time() >= self.expire_after
                    or self.last_collection.date() == today
                ):
                    ready_for_update = True
            except (AttributeError, TypeError):
                pass
        return ready_for_update

    def move_to_range(self, day: date) -> date:
        """If the date is not in range, move to the range."""
        if not (day in self._include_dates or self.date_inside(day)):
            year = day.year
            month = day.month
            if self._first_month <= self._last_month and month > self._last_month:
                _LOGGER.debug(
                    "(%s) %s outside the range, lookig from %s next year",
                    self._name,
                    day,
                    MONTH_OPTIONS[self._first_month - 1],
                )
                return date(year + 1, self._first_month, 1)
            else:
                _LOGGER.debug(
                    "(%s) %s outside the range, searching from %s",
                    self._name,
                    day,
                    MONTH_OPTIONS[self._first_month - 1],
                )
                return date(year, self._first_month, 1)
        return day

    async def async_find_next_date(self, first_date: date, ignore_today=False):
        """Get date within configured date range."""
        # Today's collection can be triggered by past collection with offset
        if self._holiday_in_week_move:
            look_back = max(
                self._offset, self._holiday_move_offset, first_date.weekday()
            )
        else:
            look_back = max(self._offset, self._holiday_move_offset)
        day1 = first_date - relativedelta(days=look_back)
        # Move starting date if today is out of range
        day1 = self.move_to_range(day1)
        next_date = None
        while next_date is None:
            try:
                next_date = await self._async_find_candidate_date(day1) + relativedelta(
                    days=self._offset
                )
                next_date = await self._async_skip_holidays(next_date)
            except ValueError:
                raise
            # Check if the date is within the range
            new_date = self.move_to_range(next_date)
            if new_date != next_date:
                day1 = new_date  # continue from next year
                next_date = None
            else:
                # Date is before starting date
                if next_date < first_date:
                    next_date = None
                # Today's expiration
                now = dt_util.now()
                if not ignore_today and next_date == now.date():
                    expiration = (
                        self.expire_after
                        if self.expire_after is not None
                        else time(23, 59, 59)
                    )
                    if now.time() > expiration or (
                        self.last_collection is not None
                        and self.last_collection.date() == now.date()
                        and now.time() >= self.last_collection.time()
                    ):
                        next_date = None
                # Remove exclude dates
                if next_date in self._exclude_dates:
                    _LOGGER.debug(
                        "(%s) Skipping exclude_date %s", self._name, next_date
                    )
                    next_date = None
                day1 += relativedelta(days=1)  # look from the next day
        next_date = self._insert_include_date(first_date, next_date)
        return next_date

    async def async_update(self) -> None:
        """Get the latest data and updates the states."""
        if not await self._async_ready_for_update():
            return
        _LOGGER.debug("(%s) Calling update", self._name)
        now = dt_util.now()
        today = now.date()
        self._last_updated = now
        try:
            await asyncio.wait_for(self.async_load_holidays(today), timeout=10)
            self._next_date = await asyncio.wait_for(
                self.async_find_next_date(today), timeout=10
            )
        except asyncio.TimeoutError:
            _LOGGER.error("(%s) Timeout looking for the new date", self._name)
            self._next_date = None
        if self._next_date is not None:
            self._days = (self._next_date - today).days
            next_date_txt = self._next_date.strftime(self._date_format)
            _LOGGER.debug(
                "(%s) Found next date: %s, that is in %d days",
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
                        self._state = STATE_TODAY
                    else:
                        self._state = self._days
                    self._icon = self._icon_today
                elif self._days == 1:
                    if bool(self._verbose_state):
                        self._state = STATE_TOMORROW
                    else:
                        self._state = self._days
                    self._icon = self._icon_tomorrow
        else:
            self._days = None
