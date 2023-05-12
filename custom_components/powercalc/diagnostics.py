from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: ConfigEntry,
) -> dict:
    """Return diagnostics for a config entry."""
    return {
        "entry": entry.as_dict(),
    }
