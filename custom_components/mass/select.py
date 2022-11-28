"""Support for select platform for Music Assistant config options."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from music_assistant import MusicAssistant
from music_assistant.models.enums import (
    ContentType,
    CrossFadeMode,
    EventType,
    RepeatMode,
)
from music_assistant.models.event import MassEvent

from .const import DOMAIN
from .entity import MassBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MusicAssistant select platform."""
    mass: MusicAssistant = hass.data[DOMAIN]
    added_ids = set()

    async def async_add_number_entities(event: MassEvent) -> None:
        """Add select entities from Music Assistant Player."""
        if event.object_id in added_ids:
            return
        added_ids.add(event.object_id)
        async_add_entities(
            [
                CrossfadeModeEntity(mass, event.data),
                RepeatModeEntity(mass, event.data),
                StreamTypeEntity(mass, event.data),
                MaxSampleRateEntity(mass, event.data),
            ]
        )

    # register listener for new players
    config_entry.async_on_unload(
        mass.subscribe(async_add_number_entities, EventType.PLAYER_ADDED)
    )

    # add all current items in controller
    for player in mass.players:
        await async_add_number_entities(
            MassEvent(EventType.PLAYER_ADDED, object_id=player.player_id, data=player)
        )


class CrossfadeModeEntity(MassBaseEntity, SelectEntity):
    """Representation of a select entity to set the crossfade mode."""

    _attr_options = [x.value for x in CrossFadeMode]

    entity_description = SelectEntityDescription(
        key="crossfade_duration",
        icon="mdi:camera-timer",
        entity_category=EntityCategory.CONFIG,
        name="Crossfade mode",
    )

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        return self.queue.settings.crossfade_mode.value

    def select_option(self, option: str) -> None:
        """Change the selected option."""
        self.queue.settings.crossfade_mode = CrossFadeMode(option)


class RepeatModeEntity(MassBaseEntity, SelectEntity):
    """Representation of a select entity to set the repeat mode."""

    _attr_options = [x.value for x in RepeatMode]

    entity_description = SelectEntityDescription(
        key="repeat_mode",
        icon="mdi:repeat",
        entity_category=EntityCategory.CONFIG,
        name="Repeat mode",
    )

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        return self.queue.settings.repeat_mode.value

    def select_option(self, option: str) -> None:
        """Change the selected option."""
        self.queue.settings.repeat_mode = RepeatMode(option)


class StreamTypeEntity(MassBaseEntity, SelectEntity):
    """Representation of a select entity to set the streamtype."""

    _attr_options = ["mp3", "flac", "wav", "alac"]

    entity_description = SelectEntityDescription(
        key="stream_type",
        icon="mdi:cast-audio",
        entity_category=EntityCategory.CONFIG,
        name="Contenttype to stream to the player",
        entity_registry_enabled_default=False,
    )

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        return self.queue.settings.stream_type.value

    def select_option(self, option: str) -> None:
        """Change the selected option."""
        self.queue.settings.stream_type = ContentType(option)


class MaxSampleRateEntity(MassBaseEntity, SelectEntity):
    """Representation of a select entity to set the max_sample_rate."""

    _attr_options = [
        "44100",
        "48000",
        "88200",
        "96000",
        "176400",
        "192000",
        "352800",
        "384000",
    ]

    entity_description = SelectEntityDescription(
        key="max_sample_rate",
        icon="mdi:cast-audio",
        entity_category=EntityCategory.CONFIG,
        name="Maximum sample rate to send to the player.",
        entity_registry_enabled_default=False,
    )

    @property
    def current_option(self) -> str | None:
        """Return the selected entity option to represent the entity state."""
        return str(self.queue.settings.max_sample_rate)

    def select_option(self, option: str) -> None:
        """Change the selected option."""
        self.queue.settings.max_sample_rate = int(option)
