"""Set of functions to handle date and text conversion."""
from datetime import date, datetime
from typing import Any, List, Optional

import voluptuous as vol
from dateutil.parser import ParserError, parse


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


def parse_datetime(text: str) -> Optional[datetime]:
    """Parse text to datetime object."""
    try:
        return parse(text)
    except (ParserError, TypeError):
        return None


def dates_to_texts(dates: List[date]) -> List[str]:
    """Convert list of dates to texts."""
    converted: List[str] = []
    for record in dates:
        try:
            converted.append(record.isoformat())
        except ValueError:
            continue
    return converted


def date_text(value: Any) -> str:
    """Have to store date as text - datetime is not JSON serialisable."""
    if value is None or value == "":
        return ""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date().strftime("%Y-%m-%d")
    except ValueError as error:
        raise vol.Invalid(f"Invalid date: {value}") from error


def time_text(value: Any) -> str:
    """Have to store time as text - datetime is not JSON serialisable."""
    if value is None or value == "":
        return ""
    try:
        return datetime.strptime(value, "%H:%M").time().strftime("%H:%M")
    except ValueError as error:
        raise vol.Invalid(f"Invalid date: {value}") from error


def string_to_list(string) -> List:
    """Convert comma separated text to list."""
    if isinstance(string, list):
        return string  # Already list
    if string is None or string == "":
        return []
    return list(map(lambda x: x.strip("'\" "), string.split(",")))


def month_day_text(value: Any) -> str:
    """Validate format month/day."""
    if value is None or value == "":
        return ""
    try:
        return datetime.strptime(value, "%m/%d").date().strftime("%m/%d")
    except ValueError as error:
        raise vol.Invalid(f"Invalid date: {value}") from error


def is_date(record: str) -> bool:
    """Validate yyyy-mm-dd format."""
    if date == "":
        return True
    try:
        datetime.strptime(record, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def is_dates(dates: List) -> bool:
    """Validate list of dates (yyyy-mm-dd, yyyy-mm-dd)."""
    if not dates:
        return True
    check = True
    for record in dates:
        if not is_date(record):
            check = False
    return check


def is_month_day(record) -> bool:
    """Validate mm/dd format."""
    try:
        datetime.strptime(record, "%m/%d")
        return True
    except ValueError:
        return False
