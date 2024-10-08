"""Diagnostics support for Blitzortung."""

from typing import Any

from homeassistant.core import HomeAssistant

from . import BlitzortungConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, config_entry: BlitzortungConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    return {
        "config_entry": config_entry.as_dict(),
        "coordinator": vars(config_entry.runtime_data),
    }
