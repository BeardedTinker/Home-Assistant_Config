"""This component provides support for Reolink IP VoD support."""
from urllib.parse import quote_plus
from dataclasses import dataclass
import datetime as dt
import asyncio
import logging
import os

from dateutil import relativedelta
from homeassistant.core import CALLBACK_TYPE, HomeAssistant
import homeassistant.util.dt as dt_utils
from homeassistant.config_entries import ConfigEntry

from homeassistant.components.sensor import DEVICE_CLASS_TIMESTAMP, SensorEntity

from .const import (
    BASE,
    DOMAIN,
    DOMAIN_DATA,
    LAST_EVENT,
    THUMBNAIL_EXTENSION,
    THUMBNAIL_URL,
    VOD_URL,
)
from .entity import ReolinkEntity
from .base import ReolinkBase, searchtime_to_datetime
from .typings import VoDEvent, VoDEventThumbnail

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_devices):
    """Set up the Reolink IP Camera switches."""
    devices = []
    base: ReolinkBase = hass.data[DOMAIN][config_entry.entry_id][BASE]

    # TODO : add playback (based off of hdd_info) to api capabilities
    await base.api.get_switch_capabilities()
    if base.api.hdd_info:
        devices.append(LastEventSensor(hass, config_entry))

    async_add_devices(devices, update_before_add=False)


@dataclass
class _Attrs:
    oldest_day: dt.datetime = None
    most_recent_day: dt.datetime = None
    last_event: VoDEvent = None


class LastEventSensor(ReolinkEntity, SensorEntity):
    """An implementation of a Reolink IP camera sensor."""

    def __init__(self, hass: HomeAssistant, config: ConfigEntry):
        """Initialize a Reolink camera."""
        ReolinkEntity.__init__(self, hass, config)
        SensorEntity.__init__(self)
        self._attrs = _Attrs()
        self._bus_listener: CALLBACK_TYPE = None
        self._entry_id = config.entry_id

    async def async_added_to_hass(self) -> None:
        """Entity created."""
        await super().async_added_to_hass()
        self._bus_listener = self.hass.bus.async_listen(
            self._base.event_id, self.handle_event
        )
        self._hass.async_add_job(self._update_event_range)

    async def async_will_remove_from_hass(self):
        """Entity removed"""
        if self._bus_listener:
            self._bus_listener()
            self._bus_listener = None
        await super().async_will_remove_from_hass()

    async def request_refresh(self):
        """ force an update of the sensor """
        await super().request_refresh()
        self._hass.async_add_job(self._update_event_range)

    async def async_update(self):
        """ polling update """
        await super().async_update()
        self._hass.async_add_job(self._update_event_range)

    async def _update_event_range(self):
        end = dt_utils.now()
        start = self._attrs.most_recent_day
        if not start:
            start = dt.datetime.combine(end.date().replace(day=1), dt.time.min)
            if self._base.playback_months > 1:
                start -= relativedelta.relativedelta(
                    months=int(self._base.playback_months)
                )
        search, _ = await self._base.send_search(start, end, True)
        if not search or len(search) < 1:
            return
        entry = search[0]
        self._attrs.oldest_day = dt.datetime(
            entry["year"],
            entry["mon"],
            next((i for (i, e) in enumerate(entry["table"], start=1) if e == "1")),
            tzinfo=end.tzinfo,
        )
        entry = search[-1]
        start = self._attrs.most_recent_day = dt.datetime(
            entry["year"],
            entry["mon"],
            len(entry["table"])
            - next(
                (
                    i
                    for (i, e) in enumerate(reversed(entry["table"]), start=0)
                    if e == "1"
                )
            ),
            tzinfo=end.tzinfo,
        )
        end = dt.datetime.combine(start.date(), dt.time.max, tzinfo=end.tzinfo)
        _, files = await self._base.send_search(start, end)
        file = files[-1] if files and len(files) > 0 else None
        if file is None:
            return

        filename = file.get("name", "")
        if len(filename) == 0:
            _LOGGER.info("Search command provided a file record without a name: %s", str(file))

        end = searchtime_to_datetime(file["EndTime"], start.tzinfo)
        start = searchtime_to_datetime(file["StartTime"], end.tzinfo)
        last = self._attrs.last_event = VoDEvent(
            str(start.timestamp()),
            start,
            end - start,
            filename,
        )
        last.url = VOD_URL.format(
            camera_id=self._entry_id, event_id=quote_plus(filename)
        )
        thumbnail = last.thumbnail = VoDEventThumbnail(
            THUMBNAIL_URL.format(camera_id=self._entry_id, event_id=last.event_id),
            path=os.path.join(
                self._base.thumbnail_path, f"{last.event_id}.{THUMBNAIL_EXTENSION}"
            ),
        )
        thumbnail.exists = os.path.isfile(thumbnail.path)
        data: dict = self._hass.data.setdefault(DOMAIN_DATA, {})
        data = data.setdefault(self._base.unique_id, {})
        data[LAST_EVENT] = last
        self._state = True

        self.async_schedule_update_ha_state()

    async def handle_event(self, event):
        """Handle incoming event for VoD update"""

        if "motion" not in event.data:
            return

        await self._hass.async_add_job(self._update_event_range)

    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"reolink_lastevent_{self._base.unique_id}"

    @property
    def name(self):
        """Return the name of this sensor."""
        return f"{self._base.name} Last Event"

    @property
    def device_class(self):
        """Device class of the sensor."""
        return DEVICE_CLASS_TIMESTAMP

    @property
    def state(self):
        """Return the state of the sensor."""
        if not self._state:
            return None

        date = (
            self._attrs.last_event.start
            if self._attrs.last_event and self._attrs.last_event.start
            else None
        )
        if not date:
            return None

        return date.isoformat()

    @property
    def icon(self):
        """Icon of the sensor."""
        return "mdi:history"

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attrs = super().extra_state_attributes

        if self._state:
            if attrs is None:
                attrs = {}

            if self._attrs.oldest_day:
                attrs["oldest_day"] = self._attrs.oldest_day.isoformat()
            if self._attrs.last_event:
                if self._attrs.last_event.event_id:
                    attrs["vod_event_id"] = self._attrs.last_event.event_id
                    if self._attrs.last_event.thumbnail:
                        attrs["has_thumbnail"] = (
                            "true"
                            if self._attrs.last_event.thumbnail.exists
                            else "false"
                        )

                        attrs["thumbnail_path"] = self._attrs.last_event.thumbnail.path
                if self._attrs.last_event.duration:
                    attrs["duration"] = str(self._attrs.last_event.duration)

        return attrs
