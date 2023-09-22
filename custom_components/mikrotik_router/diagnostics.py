"""Diagnostics support for Mikrotik Router."""
from __future__ import annotations
from typing import Any
from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, TO_REDACT


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    data_coordinator = hass.data[DOMAIN][config_entry.entry_id].data_coordinator
    tracker_coordinator = hass.data[DOMAIN][config_entry.entry_id].data_coordinator

    return {
        "entry": {
            "data": async_redact_data(config_entry.data, TO_REDACT),
            "options": async_redact_data(config_entry.options, TO_REDACT),
        },
        "data": async_redact_data(data_coordinator.data, TO_REDACT),
        "tracker": async_redact_data(tracker_coordinator.data, TO_REDACT),
    }
