"""Custom services for the Music Assistant integration."""
from __future__ import annotations

from typing import Optional

import voluptuous as vol
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.service import ServiceCall
from music_assistant import MusicAssistant
from music_assistant.models.enums import MediaType, QueueOption, RepeatMode
from music_assistant.models.errors import MusicAssistantError
from music_assistant.models.media_items import MediaItemType

from .const import DOMAIN

CMD_PLAY = "play"
CMD_PAUSE = "pause"
CMD_NEXT = "next"
CMD_PREVIOUS = "previous"
CMD_STOP = "stop"
CMD_CLEAR = "clear"
CMD_PLAY_MEDIA = "play_media"
CMD_SHUFFLE_ON = "shuffle_on"
CMD_SHUFFLE_OFF = "shuffle_off"
CMD_REPEAT = "repeat"
CMD_SNAPSHOT_CREATE = "snapshot_create"
CMD_SNAPSHOT_RESTORE = "snapshot_restore"
CMD_PLAY_ANNOUNCEMENT = "play_announcement"


def validate_command_data(data: dict) -> dict:
    """Validate command args/mode."""
    cmd = data["command"]
    if cmd == CMD_REPEAT and "repeat_mode" not in data:
        raise vol.Invalid("Missing repeat_mode")
    if cmd == CMD_PLAY_MEDIA and "enqueue_mode" not in data:
        raise vol.Invalid("Missing enqueue_mode")
    if cmd in (CMD_PLAY_MEDIA, CMD_PLAY_ANNOUNCEMENT):
        if not data.get("uri"):
            raise vol.Invalid("No URI specified")
    return data


QueueCommandServiceSchema = vol.Schema(
    vol.All(
        {
            "entity_id": cv.entity_ids,
            "command": str,
            "uri": vol.Union(str, [str], None),
            "radio_mode": vol.Optional(bool),
            "repeat_mode": vol.Optional(vol.Coerce(RepeatMode)),
            "enqueue_mode": vol.Optional(vol.Coerce(QueueOption)),
        },
        validate_command_data,
    )
)


@callback
def register_services(hass: HomeAssistant, mass: MusicAssistant):
    """Register custom services."""

    async def handle_queue_command(call: ServiceCall) -> None:
        """Handle queue_command service."""
        data = call.data
        cmd = data["command"]
        if isinstance(data["entity_id"], list):
            entity_ids = data["entity_id"]
        else:
            entity_ids = [data["entity_id"]]
        for entity_id in entity_ids:
            entity = hass.states.get(entity_id)
            entity_id = entity.attributes.get("source_entity_id", entity_id)
            player = mass.players.get_player(entity_id)
            queue = player.active_queue
            if cmd == CMD_PLAY:
                await queue.play()
            elif cmd == CMD_PAUSE:
                await queue.pause()
            elif cmd == CMD_NEXT:
                await queue.next()
            elif cmd == CMD_PREVIOUS:
                await queue.previous()
            elif cmd == CMD_STOP:
                await queue.stop()
            elif cmd == CMD_CLEAR:
                await queue.clear()
            elif cmd == CMD_PLAY_MEDIA:
                media_items = []
                uris = data["uri"] if isinstance(data["uri"], list) else [data["uri"]]
                for uri in uris:
                    try:
                        media_items.append(await mass.music.get_item_by_uri(uri))
                    except MusicAssistantError as err:
                        # try again with item by name
                        if item := await get_item_by_name(mass, uri):
                            media_items.append(item)
                        else:
                            raise vol.Invalid(f"Invalid uri: {uri}") from err
                await queue.play_media(
                    media_items,
                    data["enqueue_mode"],
                    radio_mode=data.get("radio_mode", False),
                )
            elif cmd == CMD_SHUFFLE_ON:
                queue.settings.shuffle_enabled = True
            elif cmd == CMD_SHUFFLE_OFF:
                queue.settings.shuffle_enabled = False
            elif cmd == CMD_REPEAT:
                queue.settings.repeat_mode = [data["repeat_mode"]]
            elif cmd == CMD_SNAPSHOT_CREATE:
                await queue.snapshot_create()
            elif cmd == CMD_SNAPSHOT_RESTORE:
                await queue.snapshot_restore()
            elif cmd == CMD_PLAY_ANNOUNCEMENT:
                await queue.play_announcement(data["uri"])

    hass.services.async_register(
        DOMAIN, "queue_command", handle_queue_command, schema=QueueCommandServiceSchema
    )


async def get_item_by_name(
    mass: MusicAssistant, name: str, media_type: Optional[MediaType] = None
) -> MediaItemType | None:
    """Try to find a media item (such as a playlist) by name."""
    # iterate media controllers one by one,
    # start with playlists and radio as those are the most common one
    for mtype in (
        MediaType.PLAYLIST,
        MediaType.RADIO,
        MediaType.ALBUM,
        MediaType.TRACK,
        MediaType.ARTIST,
    ):
        if media_type is not None and mtype != media_type:
            continue
        ctrl = mass.music.get_controller(mtype)
        async for item in ctrl.iter_db_items(search=name):
            if name.lower() == item.name.lower():
                return item
    # last resort: global search - pick the top most item
    for item in await mass.music.search(name):
        if media_type is not None and item.media_type != media_type:
            continue
        if name.lower() == item.name.lower():
            return item
    return None
