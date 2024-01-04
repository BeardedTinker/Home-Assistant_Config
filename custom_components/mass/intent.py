"""Intents for the client integration."""
from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import voluptuous as vol
from homeassistant.components.conversation import ATTR_AGENT_ID, ATTR_TEXT
from homeassistant.components.conversation import SERVICE_PROCESS as CONVERSATION_SERVICE
from homeassistant.components.conversation.const import DOMAIN as CONVERSATION_DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import intent

from . import DOMAIN
from .const import CONF_OPENAI_AGENT_ID
from .media_player import ATTR_MEDIA_ID, ATTR_MEDIA_TYPE, ATTR_RADIO_MODE, MassPlayer

if TYPE_CHECKING:
    pass
if TYPE_CHECKING:
    pass


INTENT_PLAY_MEDIA_ON_MEDIA_PLAYER = "MassPlayMediaOnMediaPlayer"
NAME_SLOT = "name"
AREA_SLOT = "area"
QUERY_SLOT = "query"
SLOT_VALUE = "value"


async def async_setup_intents(hass: HomeAssistant) -> None:
    """Set up the climate intents."""
    intent.async_register(hass, MassPlayMediaOnMediaPlayerHandler())


class MassPlayMediaOnMediaPlayerHandler(intent.IntentHandler):
    """Handle PlayMediaOnMediaPlayer intents."""

    intent_type = INTENT_PLAY_MEDIA_ON_MEDIA_PLAYER
    slot_schema = {vol.Any(NAME_SLOT, AREA_SLOT): cv.string, vol.Optional(QUERY_SLOT): cv.string}

    async def async_handle(self, intent_obj: intent.Intent) -> intent.IntentResponse:
        """Handle the intent."""
        slots = self.async_validate_slots(intent_obj.slots)
        config_entry = await self._get_loaded_config_entry(intent_obj.hass)

        query: str = slots.get(QUERY_SLOT, {}).get(SLOT_VALUE)
        if query is not None:
            service_data: dict[str, Any] = {}
            service_data[ATTR_AGENT_ID] = config_entry.data.get(CONF_OPENAI_AGENT_ID)
            service_data[ATTR_TEXT] = query

        name: str | None = slots.get("name", {}).get("value")
        if name == "all":
            # Don't match on name if targeting all entities
            name = None
        # Look up area first to fail early
        area_name = slots.get("area", {}).get("value")
        area: ar.AreaEntry | None = None
        if area_name is not None:
            areas = ar.async_get(intent_obj.hass)
            area = areas.async_get_area(area_name) or areas.async_get_area_by_name(area_name)
            if area is None:
                raise intent.IntentHandleError(f"No area named {area_name}")

        state = await self._get_matched_state(intent_obj, name, area)
        actual_player = MassPlayer(
            intent_obj.hass.data[DOMAIN][config_entry.entry_id].mass,
            state.attributes.get("mass_player_id"),
        )
        if actual_player is None:
            raise intent.IntentHandleError(f"No Mass media player found for name {name}")

        media_id, media_type = await self._get_media_id_and_media_type_from_query_result(
            intent_obj.hass, service_data, intent_obj
        )
        await actual_player.async_play_media(
            media_id=media_id, media_type=media_type, extra={ATTR_RADIO_MODE: False}
        )
        response = intent_obj.create_response()
        response.response_type = intent.IntentResponseType.ACTION_DONE
        if area_name is not None:
            response.async_set_speech(f"Playing selection in {area.normalized_name}")
        if name is not None:
            response.async_set_speech(f"Playing selection on {name}")
        return response

    async def _get_media_id_and_media_type_from_query_result(
        self, hass: HomeAssistant, service_data: dict[str, Any], intent_obj: intent.Intent
    ) -> str:
        """Get  from the query."""
        ai_response = await hass.services.async_call(
            CONVERSATION_DOMAIN,
            CONVERSATION_SERVICE,
            {**service_data},
            blocking=True,
            context=intent_obj.context,
            return_response=True,
        )
        json_payload = json.loads(ai_response["response"]["speech"]["plain"]["speech"])
        media_id = json_payload.get(ATTR_MEDIA_ID)
        media_type = json_payload.get(ATTR_MEDIA_TYPE)
        return media_id, media_type

    async def _get_loaded_config_entry(self, hass: HomeAssistant) -> str:
        """Get the correct config entry."""
        config_entries = hass.config_entries.async_entries(DOMAIN)
        for config_entry in config_entries:
            if config_entry.state == ConfigEntryState.LOADED:
                return config_entry
        return None

    async def _get_matched_state(
        self, intent_obj: intent.Intent, name: str | None, area: ar.AreaEntry | None
    ) -> State:
        mass_states: set[str] = set()
        initial_states = intent_obj.hass.states.async_all()
        for state in initial_states:
            if state.attributes.get("mass_player_id") is not None:
                mass_states.add(state)

        states = list(
            intent.async_match_states(
                intent_obj.hass,
                name=name,
                area=area,
                states=mass_states,
            )
        )

        if not states:
            raise intent.IntentHandleError("No entities matched")

        if len(states) > 1:
            raise intent.IntentHandleError("Multiple entities matched")

        return states[0]
