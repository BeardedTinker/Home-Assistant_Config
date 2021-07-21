"""Reolink Camera Media Source Implementation."""
import datetime as dt
import logging
import os
import secrets
from typing import Dict, List, Optional, Tuple
from urllib.parse import quote_plus, unquote_plus
from aiohttp import web

from dateutil import relativedelta
from homeassistant.components.http.const import KEY_AUTHENTICATED

# from homeassistant.components.http.auth import async_sign_path

# from homeassistant.components.http import current_request
# from homeassistant.components.http.const import KEY_HASS_REFRESH_TOKEN_ID

from homeassistant.core import HomeAssistant, callback

import homeassistant.util.dt as dt_utils

from homeassistant.components.http import HomeAssistantView

from homeassistant.components.media_player.errors import BrowseError
from homeassistant.components.media_player.const import (
    MEDIA_CLASS_DIRECTORY,
    MEDIA_CLASS_VIDEO,
    MEDIA_TYPE_VIDEO,
)
from homeassistant.components.media_source.const import MEDIA_MIME_TYPES
from homeassistant.components.media_source.error import MediaSourceError, Unresolvable
from homeassistant.components.media_source.models import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
)

from homeassistant.components.stream import create_stream

from homeassistant.helpers.event import async_call_later

from .base import ReolinkBase, searchtime_to_datetime

# from . import typings

from .const import (
    BASE,
    DOMAIN,
    DOMAIN_DATA,
    LONG_TOKENS,
    MEDIA_SOURCE,
    SHORT_TOKENS,
    THUMBNAIL_EXTENSION as EXTENSION,
    THUMBNAIL_URL,
    VOD_URL,
)

_LOGGER = logging.getLogger(__name__)
# MIME_TYPE = "rtmp/mp4"
# MIME_TYPE = "video/mp4"
MIME_TYPE = "application/x-mpegURL"

NAME = "Reolink IP Camera"

STORAGE_VERSION = 1


class IncompatibleMediaSource(MediaSourceError):
    """Incompatible media source attributes."""


async def async_get_media_source(hass: HomeAssistant):
    """Set up Reolink media source."""

    _LOGGER.debug("Creating REOLink Media Source")
    source = ReolinkMediaSource(hass)
    hass.http.register_view(ReolinkSourceThumbnailView(hass))
    hass.http.register_view(ReolinkSourceVODView(hass))

    return source


class ReolinkMediaSource(MediaSource):
    """Provide Reolink camera recordings as media sources."""

    name: str = NAME

    def __init__(self, hass: HomeAssistant):
        """Initialize Reolink source."""
        super().__init__(DOMAIN)
        self.hass = hass
        self._last_token: dt.datetime = None

    @property
    def _short_security_token(self):
        def clear_token():
            tokens.remove(token)

        data: dict = self.hass.data.setdefault(DOMAIN_DATA, {})
        data = data.setdefault(MEDIA_SOURCE, {})
        tokens: List[str] = data.setdefault(SHORT_TOKENS, [])
        if len(tokens) < 1 or (
            self._last_token and (self._last_token - dt_utils.now()).seconds >= 1800
        ):
            self._last_token = dt_utils.now()
            tokens.append(secrets.token_hex())
            async_call_later(self.hass, 3600, clear_token)
        token = next(iter(tokens), None)
        return token

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve a media item to a playable item."""
        _, camera_id, event_id = async_parse_identifier(item)

        data: dict = self.hass.data[self.domain]
        entry: dict = data.get(camera_id) if camera_id else None
        base: ReolinkBase = entry.get(BASE) if entry else None
        if not base:
            raise BrowseError("Camera does not exist.")

        file = unquote_plus(event_id)
        if not file:
            raise BrowseError("Event does not exist.")
        _LOGGER.debug("file = %s", file)

        url = await base.api.get_vod_source(file)
        _LOGGER.debug("Load VOD %s", url)
        stream = create_stream(self.hass, url, {})
        stream.add_provider("hls", timeout=3600)
        url: str = stream.endpoint_url("hls")
        # the media browser seems to have a problem with the master_playlist
        # ( it does not load the referenced playlist ) so we will just
        # force the reference playlist instead, this seems to work
        # though technically wrong
        url = url.replace("master_", "")
        _LOGGER.debug("Proxy %s", url)
        return PlayMedia(url, MIME_TYPE)

    async def async_browse_media(
        self, item: MediaSourceItem, media_types: Tuple[str] = MEDIA_MIME_TYPES
    ) -> BrowseMediaSource:
        """Browse media."""

        try:
            source, camera_id, event_id = async_parse_identifier(item)
        except Unresolvable as err:
            raise BrowseError(str(err)) from err

        _LOGGER.debug("Browsing %s, %s, %s", source, camera_id, event_id)

        data: dict = self.hass.data[self.domain]
        entry: dict = data.get(camera_id) if camera_id else None
        base: ReolinkBase = entry.get(BASE) if entry else None
        if camera_id and not base:
            raise BrowseError("Camera does not exist.")

        if event_id and not "/" in event_id:
            raise BrowseError("Event does not exist.")

        return await self._async_browse_media(source, camera_id, event_id, base)

    async def _async_browse_media(
        self,
        source: str,
        camera_id: str = None,
        event_id: str = None,
        base: ReolinkBase = None,
    ) -> BrowseMediaSource:
        """ actual browse after input validation """

        start_date: dt.datetime = None

        def create_item(title: str, path: str, thumbnail: bool = False):
            nonlocal self, camera_id, event_id, start_date

            if not title or not path:
                if event_id and "/" in event_id:
                    year, *rest = event_id.split("/", 3)
                    month = rest[0] if len(rest) > 0 else None
                    day = rest[1] if len(rest) > 1 else None

                    start_date = dt.datetime.combine(
                        dt.date(
                            int(year),
                            int(month) if month else 1,
                            int(day) if day else 1,
                        ),
                        dt.time.min,
                        dt_utils.now().tzinfo,
                    )

                    title = f"{start_date.date()}"
                    path = f"{source}/{camera_id}/{event_id}"
                elif base:
                    title = base.name
                    path = f"{source}/{camera_id}"
                else:
                    title = self.name
                    path = source + "/"

            media_class = (
                MEDIA_CLASS_DIRECTORY
                if not event_id or "/" in event_id
                else MEDIA_CLASS_VIDEO
            )

            media = BrowseMediaSource(
                domain=self.domain,
                identifier=path,
                media_class=media_class,
                media_content_type=MEDIA_TYPE_VIDEO,
                title=title,
                can_play=not bool(media_class == MEDIA_CLASS_DIRECTORY),
                can_expand=bool(media_class == MEDIA_CLASS_DIRECTORY),
            )

            if thumbnail:
                url = THUMBNAIL_URL.format(camera_id=camera_id, event_id=event_id)
                # cannot do authsign as we are in a websocket and isloated from auth and context
                # we will continue to use custom tokens
                # request = current_request.get()
                # refresh_token_id = request.get(KEY_HASS_REFRESH_TOKEN_ID)
                # if not refresh_token_id:
                #     _LOGGER.debug("no token? %s", list(request.keys()))

                # # leave expiration 30 seconds?
                # media.thumbnail = async_sign_path(
                #     self.hass, refresh_token_id, url, dt.timedelta(seconds=30)
                # )
                media.thumbnail = f"{url}?token={self._short_security_token}"

            if not media.can_play and not media.can_expand:
                _LOGGER.debug(
                    "Camera %s with event %s without media url found",
                    camera_id,
                    event_id,
                )
                raise IncompatibleMediaSource

            return media

        def create_root_children():
            nonlocal base, camera_id

            children = []
            data: Dict[str, dict] = self.hass.data[self.domain]
            for entry_id in data:
                entry = data[entry_id]
                if not isinstance(entry, dict) or not BASE in entry:
                    continue
                base = entry[BASE]
                if not base.api.hdd_info:
                    continue
                camera_id = entry_id
                child = create_item(None, None)
                children.append(child)

            return children

        async def create_day_children():
            nonlocal event_id

            children = []
            end_date = dt_utils.now()
            start_date = dt.datetime.combine(
                end_date.date().replace(day=1), dt.time.min
            )
            if base.playback_months > 1:
                start_date -= relativedelta.relativedelta(
                    months=int(base.playback_months)
                )

            search, _ = await base.api.send_search(start_date, end_date, True)

            if not search is None:
                for status in search:
                    year = status["year"]
                    month = status["mon"]
                    for day, flag in enumerate(status["table"], start=1):
                        if flag == "1":
                            event_id = f"{year}/{month}/{day}"
                            child = create_item(None, None)
                            children.append(child)

            children.reverse()
            return children

        async def create_vod_children():
            nonlocal base, start_date, event_id

            children = []
            end_date = dt.datetime.combine(
                start_date.date(), dt.time.max, start_date.tzinfo
            )

            _, files = await base.send_search(start_date, end_date)

            for file in files:
                end_date = searchtime_to_datetime(file["EndTime"], end_date.tzinfo)
                start_date = searchtime_to_datetime(file["StartTime"], end_date.tzinfo)
                event_id = str(start_date.timestamp())
                evt_id = f"{camera_id}/{quote_plus(file['name'])}"
                # self._file_cache[evt_id] = file["name"]
                thumbnail = os.path.isfile(
                    f"{base.thumbnail_path}/{event_id}.{EXTENSION}"
                )

                time = start_date.time()
                duration = end_date - start_date
                child = create_item(
                    f"{time} {duration}", f"{source}/{evt_id}", thumbnail
                )
                children.append(child)

            children.reverse()

            return children

        if base and event_id and not "/" in event_id:
            event = base.in_memory_events[event_id]
            start_date = event.start

        media = create_item(None, None)

        if not media.can_expand:
            return media

        if not camera_id:
            media.children = create_root_children()
            return media

        if not start_date:
            media.children = await create_day_children()
        else:
            media.children = await create_vod_children()

        return media


class ReolinkSourceVODView(HomeAssistantView):
    """ VOD security handler """

    url = VOD_URL
    name = "api:" + DOMAIN + ":video"
    cors_allowed = True
    requires_auth = False

    def __init__(self, hass: HomeAssistant):
        """Initialize media view """

        self.hass = hass

    async def get(
        self, request: web.Request, camera_id: str, event_id: str
    ) -> web.Response:
        """ start a GET request. """

        authenticated = request.get(KEY_AUTHENTICATED, False)
        if not authenticated:
            token: str = request.query.get("token")
            if not token:
                raise web.HTTPUnauthorized()

            data: dict = self.hass.data.get(DOMAIN_DATA)
            data = data.get(MEDIA_SOURCE) if data else None
            tokens: List[str] = data.get(LONG_TOKENS) if data else None
            if not tokens or not token in tokens:
                raise web.HTTPUnauthorized()

        if not camera_id or not event_id:
            raise web.HTTPNotFound()

        data: Dict[str, dict] = self.hass.data[DOMAIN]
        base: ReolinkBase = (
            data[camera_id].get(BASE, None) if camera_id in data else None
        )
        if not base:
            _LOGGER.debug("camera %s not found", camera_id)
            raise web.HTTPNotFound()

        file = unquote_plus(event_id)
        url = await base.api.get_vod_source(file)
        return web.HTTPTemporaryRedirect(url)


class ReolinkSourceThumbnailView(HomeAssistantView):
    """ Thumbnial view handler """

    url = THUMBNAIL_URL
    name = "api:" + DOMAIN + ":image"
    cors_allowed = True
    requires_auth = False

    def __init__(self, hass: HomeAssistant):
        """Initialize media view """

        self.hass = hass

    async def get(
        self,
        request: web.Request,  # pylint: disable=unused-argument
        camera_id: str,
        event_id: str,
    ) -> web.Response:
        """ start a GET request. """

        authenticated = request.get(KEY_AUTHENTICATED, False)
        if not authenticated:
            token: str = request.query.get("token")
            if not token:
                raise web.HTTPUnauthorized()

            data: dict = self.hass.data.get(DOMAIN_DATA)
            data = data.get(MEDIA_SOURCE) if data else None
            tokens: List[str] = data.get(SHORT_TOKENS) if data else None
            if not tokens or not token in tokens:
                raise web.HTTPUnauthorized()

        if not camera_id or not event_id:
            raise web.HTTPNotFound()

        data: Dict[str, dict] = self.hass.data[DOMAIN]
        base: ReolinkBase = (
            data[camera_id].get(BASE, None) if camera_id in data else None
        )
        if not base:
            _LOGGER.debug("camera %s not found", camera_id)
            raise web.HTTPNotFound()

        thumbnail = f"{base.thumbnail_path}/{event_id}.{EXTENSION}"
        return web.FileResponse(thumbnail)


@callback
def async_parse_identifier(
    item: MediaSourceItem,
) -> Tuple[str, str, Optional[str]]:
    """Parse identifier."""
    if not item.identifier:
        return "events", "", None

    source, path = item.identifier.lstrip("/").split("/", 1)

    if source != "events":
        raise Unresolvable("Unknown source directory.")

    if "/" in path:
        camera_id, event_id = path.split("/", 1)

        return source, camera_id, event_id

    return source, path, None
