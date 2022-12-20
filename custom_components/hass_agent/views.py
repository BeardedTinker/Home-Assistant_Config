from typing import Any
from homeassistant.components.http.view import HomeAssistantView
from aiohttp import web

from homeassistant.core import HomeAssistant

from homeassistant.helpers import entity_registry as er

from .const import DOMAIN


class MediaPlayerThumbnailView(HomeAssistantView):
    url = "/api/hass_agent/{media_player:.*}/thumbnail.png"

    name = "api:hass_agent:media_player_thumbnails"

    requires_auth = False

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass

    async def get(
        self,
        request: web.Request,
        **kwargs: Any,
    ) -> web.Response:

        media_player = kwargs["media_player"]

        entity_registry = er.async_get(self.hass)

        entity = entity_registry.async_get(media_player)

        thumbnail = self.hass.data[DOMAIN][entity.config_entry_id]["thumbnail"]

        if thumbnail is None:
            return web.Response(status=500)

        return web.Response(
            body=thumbnail,
            content_type="image/png",
            status=200,
            headers={"Content-Length": f"{len(thumbnail)}"},
        )
