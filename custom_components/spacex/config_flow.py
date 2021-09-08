"""Config flow for SpaceX Launches and Starman."""
from spacexpypi import SpaceX

from homeassistant.helpers import config_entry_flow

from .const import DOMAIN


async def _async_has_devices(hass) -> bool:
    """Return if there are devices that can be discovered."""
    api_client = SpaceX()

    devices = await api_client.get_next_launch()
    return len(devices) > 0


config_entry_flow.register_discovery_flow(
    DOMAIN,
    "SpaceX Launches and Starman",
    _async_has_devices,
)
