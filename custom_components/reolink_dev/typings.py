""" Typing Definitions """

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class VoDEventThumbnail:
    """ VoD Event Thumbnail """

    url: str = None
    exists: bool = None
    path: str = None


@dataclass
class VoDEvent:
    """ VoD Event """

    event_id: str = None
    start: datetime = None
    duration: timedelta = None
    file: str = None
    url: str = None
    thumbnail: VoDEventThumbnail = None
