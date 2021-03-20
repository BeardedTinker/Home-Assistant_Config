""" Typing declarations for strongly typed dictionaries """

from typing import Any, Dict, List, TypedDict
from datetime import datetime, date

VodEvent = TypedDict(
    "VodEvent",
    {
        "start": datetime,
        "end": datetime,
        "file": str,
        "thumbnail": Any,
    },
    total=False,
)

MediaSourceCacheEntry = TypedDict(
    "MediaSourceCacheEntry",
    {
        "entry_id": str,
        "unique_id": str,
        "event_id": str,
        "name": str,
        "playback_months": int,
        "playback_thumbnails": bool,
        "playback_thumbnail_offset": int,
        "playback_day_entries": List[date],
        "playback_events": Dict[str, VodEvent],
    },
    total=False,
)
