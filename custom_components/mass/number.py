"""Support for number platform for Music Assistant config options."""
from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, SIGNAL_STRENGTH_DECIBELS, TIME_SECONDS
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from music_assistant import MusicAssistant
from music_assistant.models.enums import EventType
from music_assistant.models.event import MassEvent

from .const import DOMAIN
from .entity import MassBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MusicAssistant number platform."""
    mass: MusicAssistant = hass.data[DOMAIN]
    added_ids = set()

    async def async_add_number_entities(event: MassEvent) -> None:
        """Add number entities from Music Assistant Player."""
        if event.object_id in added_ids:
            return
        added_ids.add(event.object_id)
        async_add_entities(
            [
                CrossfadeDurationEntity(mass, event.data),
                VolumeNormalizationTargetEntity(mass, event.data),
                AnnounceVolumeEntity(mass, event.data),
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


class CrossfadeDurationEntity(MassBaseEntity, NumberEntity):
    """Representation of a number entity to set the crossfade duration."""

    entity_description = NumberEntityDescription(
        key="crossfade_duration",
        icon="mdi:camera-timer",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=TIME_SECONDS,
        name="Crossfade duration",
        native_max_value=10,
        native_min_value=0,
        native_step=1,
    )

    @property
    def native_value(self) -> int:
        """Return current value."""
        return self.queue.settings.crossfade_duration

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        self.queue.settings.crossfade_duration = int(value)


class VolumeNormalizationTargetEntity(MassBaseEntity, NumberEntity):
    """Representation of a number entity to set the volume normalization target."""

    entity_description = NumberEntityDescription(
        key="volume_normalization_target",
        icon="mdi:chart-bar",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=SIGNAL_STRENGTH_DECIBELS,
        name="Volume normalization target",
        native_max_value=0,
        native_min_value=-40,
        native_step=1,
        entity_registry_enabled_default=False,
    )

    @property
    def native_value(self) -> float:
        """Return current value."""
        return self.queue.settings.volume_normalization_target

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        self.queue.settings.volume_normalization_target = value


class AnnounceVolumeEntity(MassBaseEntity, NumberEntity):
    """Representation of a number entity to set the announce volume."""

    entity_description = NumberEntityDescription(
        key="announce_volume_increase",
        icon="mdi:camera-timer",
        entity_category=EntityCategory.CONFIG,
        native_unit_of_measurement=PERCENTAGE,
        name="Announcements Volume increase (relative)",
        native_max_value=100,
        native_min_value=0,
        native_step=1,
    )

    @property
    def native_value(self) -> int:
        """Return current value."""
        return self.queue.settings.announce_volume_increase

    async def async_set_native_value(self, value: float) -> None:
        """Set new value."""
        self.queue.settings.announce_volume_increase = int(value)
