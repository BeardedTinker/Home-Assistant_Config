"""Base entity model."""
from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.helpers.entity import DeviceInfo, Entity
from music_assistant.common.models.enums import EventType
from music_assistant.common.models.event import MassEvent

from .const import DEFAULT_NAME, DOMAIN

if TYPE_CHECKING:
    from music_assistant.client import MusicAssistantClient
    from music_assistant.common.models.player import Player


class MassBaseEntity(Entity):
    """Base Entity from Music Assistant Player."""

    _attr_has_entity_name = True

    def __init__(self, mass: MusicAssistantClient, player_id: str) -> None:
        """Initialize MediaPlayer entity."""
        self.mass = mass
        self.player_id = player_id
        self._attr_should_poll = False
        player = mass.players.get_player(player_id)
        dev_mod = player.device_info.model or player.name
        model = f"{dev_man} {dev_mod}" if (dev_man := player.device_info.manufacturer) else dev_mod
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, player_id)},
            manufacturer=DEFAULT_NAME,
            model=model,
            name=player.display_name,
            configuration_url=mass.server_url,
        )

    async def async_added_to_hass(self) -> None:
        """Register callbacks."""
        await self.async_on_update()
        self.async_on_remove(
            self.mass.subscribe(self.__on_mass_update, EventType.PLAYER_UPDATED, self.player_id)
        )
        self.async_on_remove(
            self.mass.subscribe(
                self.__on_mass_update,
                EventType.QUEUE_UPDATED,
            )
        )

    @property
    def player(self) -> Player:
        """Return the Mass Player attached to this HA entity."""
        player = self.mass.players.get_player(self.player_id)
        assert player is not None
        return player

    @property
    def unique_id(self) -> str | None:
        """Return unique id for entity."""
        _base = f"mass_{self.player_id}"
        if hasattr(self, "entity_description"):
            return f"{_base}_{self.entity_description.key}"
        return _base

    @property
    def available(self) -> bool:
        """Return availability of entity."""
        return self.player.available and self.mass.connection.connected

    async def __on_mass_update(self, event: MassEvent) -> None:
        """Call when we receive an event from MusicAssistant."""
        if event == EventType.QUEUE_UPDATED and event.object_id != self.player.active_source:
            return
        await self.async_on_update()
        self.async_write_ha_state()

    async def async_on_update(self) -> None:
        """Handle player updates."""
