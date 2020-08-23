"""Sensor platform for garbage_collection."""
import logging
from datetime import date, datetime, time, timedelta
from typing import Any, List

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
    month_starts_on = first_of_month.weekday()
    return first_of_month + relativedelta(
        days=collection_day - month_starts_on + (n - 1) * 7
    )


def nth_weekday_date(n: int, date_of_month: date, collection_day: int) -> date:
    """Find nth weekday of the month."""
    first_of_month = date(date_of_month.year, date_of_month.month, 1)
    month_starts_on = first_of_month.weekday()
    # 1st of the month is before the day of collection
    # (so 1st collection week the week when month starts)
    if collection_day >= month_starts_on:
        return first_of_month + relativedelta(
            days=collection_day - month_starts_on + (n - 1) * 7
        )
    else:  # Next week
        return first_of_month + relativedelta(
            days=7 - month_starts_on + collection_day + (n - 1) * 7
        )


def to_date(day: Any) -> date:
    """Convert datetime or text to date, if not already datetime."""
    if day is None:
        return None
    if type(day) == date:
        return day
    if type(day) == datetime:
        return day.date()
    return date.fromisoformat(day)


def parse_datetime(text: str):
    """Parse text to datetime object."""
    try:
        return parse(text)
    except Exception:
        return None


def parse_date(text: str):
    """Parse text to date object."""
    try:
        return parse(text).date()
    except Exception:
        return None


def to_dates(dates: List[Any]) -> List[date]:
    """Convert list of text to datetimes, if not already datetimes."""
    converted = []
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
        self.__name = title if title is not None else config.get(CONF_NAME)
        self.__hidden = config.get(ATTR_HIDDEN, False)
        self.__frequency = config.get(CONF_FREQUENCY)
        self.__collection_days = config.get(CONF_COLLECTION_DAYS)
        first_month = config.get(CONF_FIRST_MONTH)
        if first_month in MONTH_OPTIONS:
            self.__first_month = MONTH_OPTIONS.index(first_month) + 1
        else:
            self.__first_month = 1
        last_month = config.get(CONF_LAST_MONTH)
        if last_month in MONTH_OPTIONS:
            self.__last_month = MONTH_OPTIONS.index(last_month) + 1
        else:
            self.__last_month = 12
        self._weekday_order_numbers = config.get(CONF_WEEKDAY_ORDER_NUMBER)
        self._week_order_numbers = config.get(CONF_WEEK_ORDER_NUMBER)
        self.__monthly_force_week_numbers = bool(
            self._week_order_numbers is not None and len(self._week_order_numbers) != 0
        )
        self.__include_dates = to_dates(config.get(CONF_INCLUDE_DATES, []))
        self.__exclude_dates = to_dates(config.get(CONF_EXCLUDE_DATES, []))
        self.__country_holidays = config.get(CONF_MOVE_COUNTRY_HOLIDAYS)
        self.__holiday_move_offset = config.get(CONF_HOLIDAY_MOVE_OFFSET, 1)
        self.__holiday_pop_named = config.get(CONF_HOLIDAY_POP_NAMED)
        self.__holiday_in_week_move = config.get(CONF_HOLIDAY_IN_WEEK_MOVE)
        self.__holiday_prov = config.get(CONF_PROV)
        self.__holiday_state = config.get(CONF_STATE)
        self.__holiday_observed = config.get(CONF_OBSERVED, True)
        self.__holidays = []
        self.__period = config.get(CONF_PERIOD)
        self.__first_week = config.get(CONF_FIRST_WEEK)
        self.__first_date = to_date(config.get(CONF_FIRST_DATE))
        self.__next_date = None
        self.__last_updated = None
        self.last_collection = None
        self.__days = None
        self.__date = config.get(CONF_DATE)
        self.__entities = config.get(CONF_ENTITIES)
        self.__verbose_state = config.get(CONF_VERBOSE_STATE)
        self.__state = "" if bool(self.__verbose_state) else 2
        self.__offset = config.get(CONF_OFFSET, 0)
        self.__icon_normal = config.get(CONF_ICON_NORMAL)
        self.__icon_today = config.get(CONF_ICON_TODAY)
        self.__icon_tomorrow = config.get(CONF_ICON_TOMORROW)
        exp = config.get(CONF_EXPIRE_AFTER)
        self.__expire_after = (
            None if exp is None else datetime.strptime(exp, "%H:%M").time()
        )
        self.__date_format = config.get(CONF_DATE_FORMAT, DEFAULT_DATE_FORMAT)
        self.__verbose_format = config.get(CONF_VERBOSE_FORMAT, DEFAULT_VERBOSE_FORMAT)
        self.__icon = self.__icon_normal

    async def async_load_holidays(self, today: date) -> None:
        """Load the holidays from from a date."""
        holidays_log = ""
        self.__holidays.clear()
        if self.__country_holidays is not None and self.__country_holidays != "":
            this_year = today.year
            years = [this_year, this_year + 1]
            _LOGGER.debug(
                "(%s) Country Holidays with parameters: "
                "country: %s, prov: %s, state: %s, observed: %s",
                self.__name,
                self.__country_holidays,
                self.__holiday_prov,
                self.__holiday_state,
                self.__holiday_observed,
            )
            kwargs = {"years": years}
            if self.__holiday_state is not None and self.__holiday_state != "":
                kwargs["state"] = self.__holiday_state
            if self.__holiday_prov is not None and self.__holiday_prov != "":
                kwargs["prov"] = self.__holiday_prov
            if (
                self.__holiday_observed is not None
                and type(self.__holiday_observed) == bool
                and not self.__holiday_observed
            ):
                kwargs["observed"] = self.__holiday_observed
            hol = holidays.CountryHoliday(self.__country_holidays, **kwargs)
            if self.__holiday_pop_named is not None:
                for pop in self.__holiday_pop_named:
                    try:
                        hol.pop_named(pop)
                    except Exception as err:
                        _LOGGER.error("(%s) Holiday not removed (%s)", self.__name, err)
            try:
                for d, name in hol.items():
                    if d >= today:
                        self.__holidays.append(d)
                        holidays_log += f"\n  {d}: {name}"
            except KeyError:
                _LOGGER.error(
                    "(%s) Invalid country code (%s)",
                    self.__name,
                    self.__country_holidays,
                )
            _LOGGER.debug("(%s) Found these holidays: %s", self.__name, holidays_log)

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
            self.__last_updated = parse_datetime(
                state.attributes.get(ATTR_LAST_UPDATED)
            )
            self.__next_date = parse_date(state.attributes.get(ATTR_NEXT_DATE))
            self.__days = state.attributes.get(ATTR_DAYS)
            self.__state = state.state

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
        return self.__name

    @property
    def hidden(self):
        """Return the hidden attribute."""
        return self.__hidden

    @property
    def state(self):
        """Return the state of the sensor."""
        return self.__state

    @property
    def icon(self):
        """Return the entity icon."""
        return self.__icon

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        res = {}
        if self.__next_date is None:
            res[ATTR_NEXT_DATE] = None
        else:
            res[ATTR_NEXT_DATE] = datetime(
                self.__next_date.year, self.__next_date.month, self.__next_date.day
            ).astimezone()
        res[ATTR_DAYS] = self.__days
        res[ATTR_LAST_COLLECTION] = self.last_collection
        res[ATTR_LAST_UPDATED] = self.__last_updated
        return res

    @property
    def device_class(self):
        """Return the class of the sensor."""
        return DEVICE_CLASS

    def __repr__(self):
        """Return main sensor parameters."""
        return (
            f"Garbagecollection[ name: {self.__name}, "
            f"entity_id: {self.entity_id}, "
            f"state: {self.state}\n"
            f"config: {self.config}]"
        )

    def date_inside(self, dat: date) -> bool:
        """Check if the date is inside first and last date."""
        month = dat.month
        if self.__first_month <= self.__last_month:
            return bool(month >= self.__first_month and month <= self.__last_month)
        else:
            return bool(month <= self.__last_month or month >= self.__first_month)

    async def __async_monthly_candidate(self, day1: date) -> date:
        """Calculate possible date, for monthly frequency."""
        if self.__monthly_force_week_numbers:
            for week_order_number in self._week_order_numbers:
                candidate_date = nth_week_date(
                    week_order_number, day1, WEEKDAYS.index(self.__collection_days[0])
                )
                # date is today or in the future -> we have the date
                if candidate_date >= day1:
                    return candidate_date
        else:
            for weekday_order_number in self._weekday_order_numbers:
                candidate_date = nth_weekday_date(
                    weekday_order_number,
                    day1,
                    WEEKDAYS.index(self.__collection_days[0]),
                )
                # date is today or in the future -> we have the date
                if candidate_date >= day1:
                    return candidate_date
        if day1.month == 12:
            next_collection_month = date(day1.year + 1, 1, 1)
        else:
            next_collection_month = date(day1.year, day1.month + 1, 1)
        if self.__monthly_force_week_numbers:
            return nth_week_date(
                self._week_order_numbers[0],
                next_collection_month,
                WEEKDAYS.index(self.__collection_days[0]),
            )
        else:
            return nth_weekday_date(
                self._weekday_order_numbers[0],
                next_collection_month,
                WEEKDAYS.index(self.__collection_days[0]),
            )

    async def __async_find_candidate_date(self, day1: date) -> date:
        """Find the next possible date starting from day1.

        Only based on calendar, not looking at include/exclude days.
        """
        week = day1.isocalendar()[1]
        weekday = day1.weekday()
        year = day1.year
        if self.__frequency in ["weekly", "even-weeks", "odd-weeks", "every-n-weeks"]:
            # Everything except montthly
            # convert to every-n-weeks
            if self.__frequency == "weekly":
                period = 1
                first_week = 1
            elif self.__frequency == "even-weeks":
                period = 2
                first_week = 2
            elif self.__frequency == "odd-weeks":
                period = 2
                first_week = 1
            else:
                period = self.__period
                first_week = self.__first_week
            offset = -1
            if (week - first_week) % period == 0:  # Collection this week
                for day_name in self.__collection_days:
                    day_index = WEEKDAYS.index(day_name)
                    if day_index >= weekday:  # Collection still did not happen
                        offset = day_index - weekday
                        break
            iterate_by_week = 7 - weekday + WEEKDAYS.index(self.__collection_days[0])
            while offset == -1:  # look in following weeks
                candidate = day1 + relativedelta(days=iterate_by_week)
                week = candidate.isocalendar()[1]
                if (week - first_week) % period == 0:
                    offset = iterate_by_week
                    break
                iterate_by_week += 7
            return day1 + relativedelta(days=offset)
        elif self.__frequency == "every-n-days":
            try:
                if (day1 - self.__first_date).days % self.__period == 0:
                    return day1
                offset = self.__period - (
                    (day1 - self.__first_date).days % self.__period
                )
            except TypeError:
                _LOGGER.error(
                    "(%s) Please configure first_date and period "
                    "for every-n-days collection frequency.",
                    self.__name,
                )
                return None
            return day1 + relativedelta(days=offset)
        elif self.__frequency == "monthly":
            # Monthly
            if self.__period is None or self.__period == 1:
                return await self.__async_monthly_candidate(day1)
            else:
                candidate_date = await self.__async_monthly_candidate(day1)
                while (candidate_date.month - self.__first_month) % self.__period != 0:
                    candidate_date = await self.__async_monthly_candidate(
                        candidate_date + relativedelta(days=1)
                    )
                return candidate_date
        elif self.__frequency == "annual":
            # Annual
            try:
                conf_date = datetime.strptime(self.__date, "%m/%d").date()
            except TypeError:
                _LOGGER.error(
                    "(%s) Please configure the date for annual collection frequency.",
                    self.__name,
                )
                return None
            candidate_date = date(year, conf_date.month, conf_date.day)
            if candidate_date < day1:
                candidate_date = date(year + 1, conf_date.month, conf_date.day)
            return candidate_date
        elif self.__frequency == "group":
            candidate_date = None
            try:
                for entity_id in self.__entities:
                    entity = self.hass.data[DOMAIN][SENSOR_PLATFORM][entity_id]
                    d = await entity.async_find_next_date(day1)
                    if candidate_date is None or d < candidate_date:
                        candidate_date = d
            except KeyError:
                return None
            except TypeError:
                _LOGGER.error("(%s) Please add entities for the group.", self.__name)
                return None
            return candidate_date
        else:
            _LOGGER.debug("(%s) Unknown frequency %s", self.__name, self.__frequency)
            return None

    async def __async_candidate_date_with_holidays(self, day1: date) -> date:
        """Find candidate date, automatically skip holidays."""
        first_day = day1
        # Check if there are holidays within holiday offset that would fall into day1
        if len(self.__holidays) > 0 and self.__holiday_move_offset > 0:
            check_near = list(
                filter(
                    lambda date: date + relativedelta(days=self.__holiday_move_offset)
                    >= day1
                    and date <= day1,
                    self.__holidays,
                )
            )
            if len(check_near) > 0:
                first_day -= relativedelta(days=self.__holiday_move_offset)
        while True:
            next_date = await self.__async_find_candidate_date(first_day)
            if next_date is None:
                return None
            if bool(self.__holiday_in_week_move):
                start_date = next_date - relativedelta(days=next_date.weekday())
                delta = relativedelta(days=1)
                while start_date <= next_date:
                    if start_date in self.__holidays:
                        _LOGGER.debug(
                            "(%s) Move possible collection day, "
                            "because public holiday in week on %s",
                            self.__name,
                            start_date,
                        )
                        next_date = self.__skip_holiday(next_date)
                        break
                    start_date += delta
            while next_date in self.__holidays:
                _LOGGER.debug(
                    "(%s) Skipping public holiday on %s", self.__name, next_date
                )
                next_date = self.__skip_holiday(next_date)
            if next_date >= day1:
                return next_date
            first_day += relativedelta(days=1)

    def __insert_include_date(self, day1: date, next_date: date) -> date:
        """Add include dates."""
        include_dates = list(filter(lambda date: date >= day1, self.__include_dates))
        if len(include_dates) > 0 and include_dates[0] < next_date:
            _LOGGER.debug(
                "(%s) Inserting include_date %s", self.__name, include_dates[0]
            )
            return include_dates[0]
        else:
            return next_date

    def __skip_holiday(self, day: date) -> date:
        """Move holidays by holiday move offset."""
        skip_days = (
            1
            if self.__holiday_move_offset is None or self.__holiday_move_offset == 0
            else self.__holiday_move_offset
        )
        return day + relativedelta(days=skip_days)

    async def __async_candidate_with_incl_excl(self, day1: date) -> date:
        """Find the next date starting from day1."""
        first_day = day1 - relativedelta(days=self.__offset)
        i = 0
        while True:
            next_date = self.__insert_include_date(
                first_day, await self.__async_candidate_date_with_holidays(first_day)
            )
            if next_date is None:
                return None
            date_ok = True
            # Ifit is today and after expiration, search from tomorrow
            now = dt_util.now()
            expiration = (
                self.__expire_after
                if self.__expire_after is not None
                else time(23, 59, 59)
            )
            if next_date == now.date():
                if (
                    self.last_collection is not None
                    and self.last_collection.date() == next_date
                    and now.time() >= self.last_collection.time()
                ):
                    date_ok = False
                elif now.time() >= expiration:
                    _LOGGER.debug("(%s) Today's collection expired", self.__name)
                    self.last_collection = datetime.combine(next_date, expiration)
                    date_ok = False
            if next_date in self.__exclude_dates:
                _LOGGER.debug("(%s) Skipping exclude_date %s", self.__name, next_date)
                date_ok = False
            if date_ok:
                return next_date + relativedelta(days=self.__offset)
            first_day = next_date + relativedelta(days=1)
            i += 1
            if i > 365:
                _LOGGER.error("(%s) Cannot find any suitable date", self.__name)
                return None

    async def __async_ready_for_update(self) -> bool:
        """Check if the entity is ready for the update.

        Skip the update if the sensor was updated today
        Except for the sensors with with next date today and after the expiration time
        For group sensors wait for update of the sensors in the group
        """
        now = dt_util.now()
        today = now.date()
        ready_for_update = bool(
            self.__last_updated is None or self.__last_updated.date() != today
        )
        if self.__frequency == "group":
            members_ready = True
            for entity_id in self.__entities:
                state_object = self.hass.states.get(entity_id)
                if (
                    state_object is None
                    or state_object.attributes.get(ATTR_LAST_UPDATED).date() != today
                ):
                    members_ready = False
                    break
            if ready_for_update and not members_ready:
                ready_for_update = False
        else:
            if self.__next_date == today and (
                (self.__expire_after is not None and now.time() >= self.__expire_after)
                or (
                    self.last_collection is not None
                    and self.last_collection.date() == today
                )
            ):
                ready_for_update = True
        return ready_for_update

    async def async_find_next_date(self, today: date) -> date:
        """Get date within configured date range."""
        year = today.year
        month = today.month
        if self.date_inside(today):
            next_date = await self.__async_candidate_with_incl_excl(today)
            if next_date is not None:
                if not self.date_inside(next_date):
                    if self.__first_month <= self.__last_month:
                        next_year = date(year + 1, self.__first_month, 1)
                        next_date = await self.__async_candidate_with_incl_excl(
                            next_year
                        )
                        _LOGGER.debug(
                            "(%s) Did not find a date this year, "
                            "lookig at next year",
                            self.__name,
                        )
                    else:
                        next_year = date(year, self.__first_month, 1)
                        next_date = await self.__async_candidate_with_incl_excl(
                            next_year
                        )
                        _LOGGER.debug(
                            "(%s) Date not within the range, "
                            "searching again from %s",
                            self.__name,
                            MONTH_OPTIONS[self.__first_month - 1],
                        )
        else:
            if self.__first_month <= self.__last_month and month > self.__last_month:
                next_year = date(year + 1, self.__first_month, 1)
                next_date = await self.__async_candidate_with_incl_excl(next_year)
                _LOGGER.debug(
                    "(%s) Date outside range, lookig at next year", self.__name
                )
            else:
                next_year = date(year, self.__first_month, 1)
                next_date = await self.__async_candidate_with_incl_excl(next_year)
                _LOGGER.debug(
                    "(%s) Current date is outside of the range, "
                    "starting from first month",
                    self.__name,
                )
        return next_date

    async def async_update(self) -> None:
        """Get the latest data and updates the states."""
        now = dt_util.now()
        today = now.date()
        if not await self.__async_ready_for_update():
            # _LOGGER.debug(
            #     "(%s) Skipping the update, already did it today",
            #     self.__name)
            return
        _LOGGER.debug("(%s) Calling update", self.__name)
        await self.async_load_holidays(today)
        self.__last_updated = now
        self.__next_date = await self.async_find_next_date(today)
        if self.__next_date is not None:
            self.__days = (self.__next_date - today).days
            next_date_txt = self.__next_date.strftime(self.__date_format)
            _LOGGER.debug(
                "(%s) Found next date: %s, that is in %d days",
                self.__name,
                next_date_txt,
                self.__days,
            )
            if self.__days > 1:
                if bool(self.__verbose_state):
                    self.__state = self.__verbose_format.format(
                        date=next_date_txt, days=self.__days
                    )
                    # self.__state = "on_date"
                else:
                    self.__state = 2
                self.__icon = self.__icon_normal
            else:
                if self.__days == 0:
                    if bool(self.__verbose_state):
                        self.__state = STATE_TODAY
                    else:
                        self.__state = self.__days
                    self.__icon = self.__icon_today
                elif self.__days == 1:
                    if bool(self.__verbose_state):
                        self.__state = STATE_TOMORROW
                    else:
                        self.__state = self.__days
                    self.__icon = self.__icon_tomorrow
        else:
            self.__days = None
