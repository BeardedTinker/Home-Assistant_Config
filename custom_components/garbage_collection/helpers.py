"""Set of functions to handle date and text conversion."""
from __future__ import annotations

from datetime import date, datetime
from typing import Any

import homeassistant.util.dt as dt_util
import voluptuous as vol
from dateutil.parser import ParserError, parse


def now() -> datetime:
    """Return current date and time. Needed for testing."""
    return dt_util.now()


def to_date(day: Any) -> date:
    """Convert datetime or text to date, if not already datetime.

    Used for the first date for every_n_days (configured as text)
    """
    if day is None:
        raise ValueError
    if isinstance(day, date):
        return day
    if isinstance(day, datetime):
        return day.date()
    return date.fromisoformat(day)


def parse_datetime(text: str) -> datetime | None:
    """Parse text to datetime object."""
    try:
        return parse(text)
    except (ParserError, TypeError):
        return None


def dates_to_texts(dates: list[date]) -> list[str]:
    """Convert list of dates to texts."""
    converted: list[str] = []
    for record in dates:
        try:
            converted.append(record.isoformat())
        except ValueError:
            continue
    return converted


def time_text(value: Any) -> str:
    """Have to store time as text - datetime is not JSON serialisable."""
    if value is None or value == "":
        return ""
    try:
        return datetime.strptime(value, "%H:%M").time().strftime("%H:%M")
    except ValueError as error:
        raise vol.Invalid(f"Invalid date: {value}") from error


def month_day_text(value: Any) -> str:
    """Validate format month/day."""
    if value is None or value == "":
        return ""
    try:
        return datetime.strptime(value, "%m/%d").date().strftime("%m/%d")
    except ValueError as error:
        raise vol.Invalid(f"Invalid date: {value}") from error
