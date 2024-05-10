"""MediaPlayer platform for Music Assistant integration."""

from __future__ import annotations

import asyncio
import os
from collections.abc import Mapping
from contextlib import suppress
from typing import TYPE_CHECKING, Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components import media_source
from homeassistant.components.homeassistant.exposed_entities import async_expose_entity
from homeassistant.components.media_player import (
    BrowseMedia,
    MediaPlayerDeviceClass,
    MediaPlayerEnqueue,
    MediaPlayerEntity,
)
from homeassistant.components.media_player.browse_media import (
    async_process_play_media_url,
)
from homeassistant.components.media_player.const import (
    ATTR_MEDIA_ANNOUNCE,
    ATTR_MEDIA_ENQUEUE,
    ATTR_MEDIA_EXTRA,
    MediaPlayerEntityFeature,
)
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import STATE_IDLE, STATE_OFF, STATE_PAUSED, STATE_PLAYING
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,
)
from music_assistant.common.helpers.datetime import from_utc_timestamp
from music_assistant.common.models.enums import (
    EventType,
    MediaType,
    PlayerFeature,
    PlayerState,
    QueueOption,
    RepeatMode,
)
from music_assistant.common.models.errors import MediaNotFoundError
from music_assistant.common.models.event import MassEvent
from music_assistant.common.models.media_items import MediaItemType

from .const import (
    ATTR_ACTIVE_QUEUE,
    ATTR_GROUP_LEADER,
    ATTR_GROUP_MEMBERS,
    ATTR_MASS_PLAYER_ID,
    ATTR_MASS_PLAYER_TYPE,
    ATTR_QUEUE_INDEX,
    ATTR_QUEUE_ITEMS,
    ATTR_STREAM_TITLE,
    DOMAIN,
)
from .entity import MassBaseEntity
from .helpers import get_mass
from .media_browser import async_browse_media

if TYPE_CHECKING:
    from music_assistant.client import MusicAssistantClient
    from music_assistant.common.models.player import Player
    from music_assistant.common.models.player_queue import PlayerQueue

SUPPORTED_FEATURES = (
    MediaPlayerEntityFeature.PAUSE
    | MediaPlayerEntityFeature.VOLUME_SET
    | MediaPlayerEntityFeature.STOP
    | MediaPlayerEntityFeature.PREVIOUS_TRACK
    | MediaPlayerEntityFeature.NEXT_TRACK
    | MediaPlayerEntityFeature.SHUFFLE_SET
    | MediaPlayerEntityFeature.REPEAT_SET
    | MediaPlayerEntityFeature.TURN_ON
    | MediaPlayerEntityFeature.TURN_OFF
    | MediaPlayerEntityFeature.PLAY
    | MediaPlayerEntityFeature.PLAY_MEDIA
    | MediaPlayerEntityFeature.VOLUME_STEP
    | MediaPlayerEntityFeature.CLEAR_PLAYLIST
    | MediaPlayerEntityFeature.BROWSE_MEDIA
    | MediaPlayerEntityFeature.MEDIA_ENQUEUE
    | MediaPlayerEntityFeature.MEDIA_ANNOUNCE
)

STATE_MAPPING = {
    PlayerState.IDLE: STATE_IDLE,
    PlayerState.PLAYING: STATE_PLAYING,
    PlayerState.PAUSED: STATE_PAUSED,
}

QUEUE_OPTION_MAP = {
    # map from HA enqueue options to MA enqueue options
    # which are the same but just in case
    MediaPlayerEnqueue.ADD: QueueOption.ADD,
    MediaPlayerEnqueue.NEXT: QueueOption.NEXT,
    MediaPlayerEnqueue.PLAY: QueueOption.PLAY,
    MediaPlayerEnqueue.REPLACE: QueueOption.REPLACE,
}

SERVICE_PLAY_MEDIA_ADVANCED = "play_media"
SERVICE_PLAY_ANNOUNCEMEMT = "play_announcement"
ATTR_RADIO_MODE = "radio_mode"
ATTR_MEDIA_ID = "media_id"
ATTR_MEDIA_TYPE = "media_type"
ATTR_ARTIST = "artist"
ATTR_ALBUM = "album"
ATTR_URL = "url"
ATTR_USE_PRE_ANNOUNCE = "use_pre_announce"
ATTR_ANNOUNCE_VOLUME = "announce_volume"

# pylint: disable=too-many-public-methods


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Music Assistant MediaPlayer(s) from Config Entry."""
    mass = get_mass(hass, config_entry.entry_id)
    added_ids = set()

    async def handle_player_added(event: MassEvent) -> None:
        """Handle Mass Player Added event."""
        if event.object_id in added_ids:
            return
        added_ids.add(event.object_id)
        async_add_entities([MassPlayer(mass, event.object_id)])

    # register listener for new players
    config_entry.async_on_unload(
        mass.subscribe(handle_player_added, EventType.PLAYER_ADDED)
    )
    # add all current players
    for player in mass.players:
        added_ids.add(player.player_id)
        async_add_entities([MassPlayer(mass, player.player_id)])

    # add platform service for play_media with advanced options
    platform = async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_PLAY_MEDIA_ADVANCED,
        {
            vol.Required(ATTR_MEDIA_ID): vol.All(cv.ensure_list, [cv.string]),
            vol.Optional(ATTR_MEDIA_TYPE): vol.Coerce(MediaType),
            vol.Exclusive(ATTR_MEDIA_ENQUEUE, "enqueue_announce"): vol.Coerce(
                QueueOption
            ),
            vol.Exclusive(ATTR_MEDIA_ANNOUNCE, "enqueue_announce"): cv.boolean,
            vol.Optional(ATTR_ARTIST): cv.string,
            vol.Optional(ATTR_ALBUM): cv.string,
            vol.Optional(ATTR_RADIO_MODE): vol.Coerce(bool),
            vol.Optional(ATTR_USE_PRE_ANNOUNCE): vol.Coerce(bool),
            vol.Optional(ATTR_ANNOUNCE_VOLUME): vol.Coerce(int),
        },
        "_async_play_media_advanced",
    )
    platform.async_register_entity_service(
        SERVICE_PLAY_ANNOUNCEMEMT,
        {
            vol.Required(ATTR_URL): cv.string,
            vol.Optional(ATTR_USE_PRE_ANNOUNCE): vol.Coerce(bool),
            vol.Optional(ATTR_ANNOUNCE_VOLUME): vol.Coerce(int),
        },
        "_async_play_announcement",
    )


class MassPlayer(MassBaseEntity, MediaPlayerEntity):
    """Representation of MediaPlayerEntity from Music Assistant Player."""

    # pylint: disable=abstract-method,too-many-instance-attributes

    _attr_name = None

    def __init__(self, mass: MusicAssistantClient, player_id: str) -> None:
        """Initialize MediaPlayer entity."""
        super().__init__(mass, player_id)
        self._attr_icon = self.player.icon.replace("mdi-", "mdi:")
        self._attr_media_image_remotely_accessible = True
        self._attr_supported_features = SUPPORTED_FEATURES
        if PlayerFeature.SYNC in self.player.supported_features:
            self._attr_supported_features |= MediaPlayerEntityFeature.GROUPING
        self._attr_device_class = MediaPlayerDeviceClass.SPEAKER
        self._attr_media_position_updated_at = None
        self._attr_media_position = None
        self._attr_media_duration = None
        self._attr_media_album_artist = None
        self._attr_media_artist = None
        self._attr_media_album_name = None
        self._attr_media_title = None
        self._attr_media_content_id = None
        self._attr_media_content_type = "music"
        self._attr_media_image_url = None
        self._prev_time = 0

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        await super().async_added_to_hass()
        # we need to get the hass object in order to get our config entry
        # and expose the player to the conversation component, assuming that
        # the config entry has the option enabled.
        await self._expose_players_assist()

        # we subscribe to player queue time update but we only
        # accept a state change on big time jumps (e.g. seeking)
        async def queue_time_updated(event: MassEvent) -> None:
            if event.object_id != self.player.active_source:
                return
            if abs(self._prev_time - event.data) > 5:
                await self.async_on_update()
                self.async_write_ha_state()
            self._prev_time = event.data

        self.async_on_remove(
            self.mass.subscribe(
                queue_time_updated,
                EventType.QUEUE_TIME_UPDATED,
            )
        )

    @property
    def extra_state_attributes(self) -> Mapping[str, Any]:
        """Return additional state attributes."""
        player = self.player
        queue = self.mass.player_queues.get(player.active_source)
        attrs = {
            ATTR_MASS_PLAYER_ID: self.player_id,
            ATTR_MASS_PLAYER_TYPE: player.type.value,
            ATTR_GROUP_MEMBERS: player.group_childs,
            ATTR_GROUP_LEADER: player.synced_to,
            ATTR_ACTIVE_QUEUE: player.active_source,
            ATTR_QUEUE_ITEMS: queue.items if queue else None,
            ATTR_QUEUE_INDEX: queue.current_index if queue else None,
        }
        # add optional stream_title for radio streams
        if (
            queue
            and queue.current_item
            and queue.current_item.streamdetails
            and queue.current_item.streamdetails.stream_title
        ):
            attrs[ATTR_STREAM_TITLE] = queue.current_item.streamdetails.stream_title
        elif (
            queue
            and queue.current_item
            and queue.current_item.media_type == MediaType.RADIO
            and queue.current_item.media_item
            and queue.current_item.media_item.metadata
        ):
            attrs[ATTR_STREAM_TITLE] = (
                queue.current_item.media_item.metadata.description
            )
        return attrs

    async def async_on_update(self) -> None:
        """Handle player updates."""
        # ruff: noqa: PLR0915
        # pylint: disable=too-many-statements
        if not self.available:
            return
        player = self.player
        queue = self.mass.player_queues.get(player.active_source)
        # update generic attributes
        if player.powered:
            self._attr_state = STATE_MAPPING[self.player.state]
        else:
            self._attr_state = STATE_OFF
        self._attr_group_members = player.group_childs
        self._attr_volume_level = player.volume_level / 100
        self._attr_is_volume_muted = player.volume_muted
        self._update_media_attributes(player, queue)
        self._update_media_image_url(player, queue)

    async def async_media_play(self) -> None:
        """Send play command to device."""
        if queue := self.mass.player_queues.get(self.player.active_source):
            await self.mass.player_queues.queue_command_play(queue.queue_id)
        else:
            await self.mass.players.player_command_play(self.player_id)

    async def async_media_pause(self) -> None:
        """Send pause command to device."""
        if queue := self.mass.player_queues.get(self.player.active_source):
            await self.mass.player_queues.queue_command_pause(queue.queue_id)
        else:
            await self.mass.players.player_command_pause(self.player_id)

    async def async_media_stop(self) -> None:
        """Send stop command to device."""
        if queue := self.mass.player_queues.get(self.player.active_source):
            await self.mass.player_queues.queue_command_stop(queue.queue_id)
        else:
            await self.mass.players.player_command_stop(self.player_id)

    async def async_media_next_track(self) -> None:
        """Send next track command to device."""
        if queue := self.mass.player_queues.get(self.player.active_source):
            await self.mass.player_queues.queue_command_next(queue.queue_id)

    async def async_media_previous_track(self) -> None:
        """Send previous track command to device."""
        if queue := self.mass.player_queues.get(self.player.active_source):
            await self.mass.player_queues.queue_command_previous(queue.queue_id)

    async def async_media_seek(self, position: float) -> None:
        """Send seek command."""
        position = int(position)
        if queue := self.mass.player_queues.get(self.player.active_source):
            await self.mass.player_queues.queue_command_seek(queue.queue_id, position)

    async def async_mute_volume(self, mute: bool) -> None:
        """Mute the volume."""
        await self.mass.players.player_command_volume_mute(self.player_id, mute)

    async def async_set_volume_level(self, volume: float) -> None:
        """Send new volume_level to device."""
        volume = int(volume * 100)
        await self.mass.players.player_command_volume_set(self.player_id, volume)

    async def async_volume_up(self) -> None:
        """Send new volume_level to device."""
        await self.mass.players.player_command_volume_up(self.player_id)

    async def async_volume_down(self) -> None:
        """Send new volume_level to device."""
        await self.mass.players.player_command_volume_down(self.player_id)

    async def async_turn_on(self) -> None:
        """Turn on device."""
        await self.mass.players.player_command_power(self.player_id, True)

    async def async_turn_off(self) -> None:
        """Turn off device."""
        await self.mass.players.player_command_power(self.player_id, False)

    async def async_set_shuffle(self, shuffle: bool) -> None:
        """Set shuffle state."""
        if queue := self.mass.player_queues.get(self.player.active_source):
            await self.mass.player_queues.queue_command_shuffle(queue.queue_id, shuffle)

    async def async_set_repeat(self, repeat: str) -> None:
        """Set repeat state."""
        if queue := self.mass.player_queues.get(self.player.active_source):
            await self.mass.player_queues.queue_command_repeat(
                queue.queue_id, RepeatMode(repeat)
            )

    async def async_clear_playlist(self) -> None:
        """Clear players playlist."""
        if queue := self.mass.player_queues.get(self.player.active_source):
            await self.mass.player_queues.queue_command_clear(queue.queue_id)

    async def async_play_media(
        self,
        media_type: str,
        media_id: str | list[str],
        enqueue: MediaPlayerEnqueue | None = None,
        announce: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """Send the play_media command to the media player."""
        if isinstance(media_id, str) and media_source.is_media_source_id(media_id):
            # Handle media_source
            sourced_media = await media_source.async_resolve_media(
                self.hass, media_id, self.entity_id
            )
            media_id = sourced_media.url
            media_id = async_process_play_media_url(self.hass, media_id)

        if announce:
            await self._async_play_announcement(
                media_id,
                use_pre_announce=kwargs[ATTR_MEDIA_EXTRA].get("use_pre_announce"),
                announce_volume=kwargs[ATTR_MEDIA_EXTRA].get("announce_volume"),
            )
            return

        # forward to our advanced play_media handler
        await self._async_play_media_advanced(
            media_id=media_id if isinstance(media_id, list) else [media_id],
            enqueue=enqueue,
            media_type=media_type,
            radio_mode=kwargs[ATTR_MEDIA_EXTRA].get(ATTR_RADIO_MODE),
        )

    async def async_join_players(self, group_members: list[str]) -> None:
        """Join `group_members` as a player group with the current player."""
        player_ids: list[str] = []
        for child_entity_id in group_members:
            # resolve HA entity_id to MA player_id
            if (hass_state := self.hass.states.get(child_entity_id)) is None:
                continue
            if (mass_player_id := hass_state.attributes.get("mass_player_id")) is None:
                continue
            player_ids.append(mass_player_id)
        await self.mass.players.cmd_sync_many(self.player_id, player_ids)

    async def async_unjoin_player(self) -> None:
        """Remove this player from any group."""
        await self.mass.players.player_command_unsync(self.player_id)

    async def _async_play_media_advanced(
        self,
        media_id: list[str],
        artist: str | None = None,
        album: str | None = None,
        enqueue: MediaPlayerEnqueue | QueueOption | None = None,
        radio_mode: bool | None = None,
        media_type: str | None = None,
    ) -> None:
        """Send the play_media command to the media player."""
        # pylint: disable=too-many-arguments
        media_uris: list[str] = []
        # work out (all) uri(s) to play
        for media_id_str in media_id:
            # URL or URI string
            if "://" in media_id_str:
                media_uris.append(media_id_str)
                continue
            # try content id as library id
            if media_type and media_id_str.isnumeric():
                with suppress(MediaNotFoundError):
                    item = await self.mass.music.get_item(
                        media_type, media_id_str, "library"
                    )
                    media_uris.append(item.uri)
                    continue
            # try local accessible filename
            elif await asyncio.to_thread(os.path.isfile, media_id_str):
                media_uris.append(media_id_str)
                continue
            # last resort: lookup by name/search
            if item := await self._get_item_by_name(
                media_id_str, artist, album, media_type
            ):
                media_uris.append(item.uri)

        if not media_uris:
            raise MediaNotFoundError(
                f"Could not resolve {media_id} to playable media item"
            )

        # determine active queue to send the play request to
        if queue := self.mass.player_queues.get(self.player.active_source):
            queue_id = queue.queue_id
        else:
            queue_id = self.player_id

        await self.mass.player_queues.play_media(
            queue_id, media=media_uris, option=enqueue, radio_mode=radio_mode
        )

    async def _async_play_announcement(
        self,
        url: str,
        use_pre_announce: bool | None = None,
        announce_volume: int | None = None,
    ) -> None:
        """Send the play_announcement command to the media player."""
        await self.mass.players.play_announcement(
            self.player_id, url, use_pre_announce, announce_volume
        )

    async def async_browse_media(
        self, media_content_type=None, media_content_id=None
    ) -> BrowseMedia:
        """Implement the websocket media browsing helper."""
        return await async_browse_media(
            self.hass, self.mass, media_content_id, media_content_type
        )

    async def _get_item_by_name(
        self,
        name: str,
        artist: str | None = None,
        album: str | None = None,
        media_type: str | None = None,
    ) -> MediaItemType | None:
        """Try to find a media item (such as a playlist) by name."""
        # pylint: disable=too-many-nested-blocks
        searchname = name.lower()
        library_functions = [
            x
            for x in (
                self.mass.music.get_library_playlists,
                self.mass.music.get_library_radios,
                self.mass.music.get_library_tracks,
                self.mass.music.get_library_albums,
                self.mass.music.get_library_artists,
            )
            if not media_type or media_type.lower() in x.__name__
        ]
        # prefer (exact) lookup in the library by name
        for func in library_functions:
            result = await func(search=searchname)
            for item in result.items:
                # handle optional artist filter
                if (
                    artist
                    and (artists := getattr(item, "artists", None))
                    and not any(x for x in artists if x.name.lower() == artist.lower())
                ):
                    continue
                # handle optional album filter
                if (
                    album
                    and (item_album := getattr(item, "album", None))
                    and item_album.name.lower() != album.lower()
                ):
                    continue
                if searchname == item.name.lower():
                    return item
        # nothing found in the library, fallback to global search
        search_name = name
        if album and artist:
            search_name = f"{artist} - {album} - {name}"
        elif album:
            search_name = f"{album} - {name}"
        elif artist:
            search_name = f"{artist} - {name}"
        result = await self.mass.music.search(
            search_query=search_name,
            media_types=[media_type] if media_type else MediaType.ALL,
            limit=5,
        )
        for results in (
            result.tracks,
            result.albums,
            result.playlists,
            result.artists,
            result.radio,
        ):
            for item in results:
                # simply return the first item because search is already sorted by best match
                return item
        return None

    def _update_media_image_url(
        self, player: Player, queue: PlayerQueue | None
    ) -> None:
        """Update image URL for the active queue item."""
        if queue is None or queue.current_item is None:
            self._attr_media_image_url = None
            return
        if image_url := self.mass.get_media_item_image_url(queue.current_item):
            self._attr_media_image_remotely_accessible = (
                self.mass.server_url not in image_url
            )
            self._attr_media_image_url = image_url
            return
        self._attr_media_image_url = None

    def _update_media_attributes(
        self, player: Player, queue: PlayerQueue | None
    ) -> None:
        """Update media attributes for the active queue item."""
        # pylint: disable=too-many-statements
        self._attr_media_artist = None
        self._attr_media_album_artist = None
        self._attr_media_album_name = None
        self._attr_media_title = None
        self._attr_media_content_id = None
        self._attr_media_duration = None
        self._attr_media_position = None
        self._attr_media_position_updated_at = None

        if queue is None and player.current_media:
            # player has some external source active
            self._attr_media_content_id = player.current_media.uri
            self._attr_app_id = player.active_source
            self._attr_media_title = player.current_media.title
            self._attr_media_artist = player.current_media.artist
            self._attr_media_album_name = player.current_media.album
            self._attr_media_duration = player.current_media.duration
            # TODO: grab these from the player directly if it supports other sources than MA?
            self._attr_shuffle = None
            self._attr_repeat = None
            self._attr_media_position = player.elapsed_time
            self._attr_media_position_updated_at = from_utc_timestamp(
                player.elapsed_time_last_updated
            )
            self._prev_time = player.elapsed_time
            return

        if queue is None:
            # player is completely idle without any source active
            self._attr_source = player.active_source
            self._attr_app_id = player.active_source
            return

        # player has MA as active source (either a group player or the players own queue)
        self._attr_app_id = DOMAIN
        self._attr_shuffle = queue.shuffle_enabled
        self._attr_repeat = queue.repeat_mode.value
        if not (cur_item := queue.current_item):
            # queue is empty
            return

        self._attr_media_content_id = queue.current_item.uri
        self._attr_media_duration = queue.current_item.duration
        self._attr_media_position = queue.elapsed_time
        self._attr_media_position_updated_at = from_utc_timestamp(
            queue.elapsed_time_last_updated
        )
        self._prev_time = queue.elapsed_time

        # handle stream title (radio station icy metadata)
        if (stream_details := cur_item.streamdetails) and stream_details.stream_title:
            self._attr_media_album_name = cur_item.name
            if " - " in stream_details.stream_title:
                stream_title_parts = stream_details.stream_title.split(" - ", 1)
                self._attr_media_title = stream_title_parts[1]
                self._attr_media_artist = stream_title_parts[0]
            else:
                self._attr_media_title = stream_details.stream_title
            return

        if not (media_item := cur_item.media_item):
            # queue is not playing a regular media item (edge case?!)
            self._attr_media_title = cur_item.name
            return

        # queue is playing regular media item
        self._attr_media_title = media_item.name

        if media_item.media_type == MediaType.TRACK:
            self._attr_media_artist = getattr(media_item, "artist_str", None)
            if media_item.version:
                self._attr_media_title += f" ({media_item.version})"
            if media_item.album:
                self._attr_media_album_name = media_item.album.name
                self._attr_media_album_artist = getattr(
                    media_item.album, "artist_str", None
                )

    async def _expose_players_assist(self) -> None:
        """Get the correct config entry."""
        hass = self.hass
        config_entries = hass.config_entries.async_entries(DOMAIN)
        for config_entry in config_entries:
            if (
                config_entry.state == ConfigEntryState.SETUP_IN_PROGRESS
                and config_entry.data.get("expose_players_assist")
            ):
                async_expose_entity(hass, "conversation", self.entity_id, True)
