""" Utility functions """

from typing import Union
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry
from homeassistant.helpers.device_registry import DeviceEntry, DeviceRegistry


async def async_get_device_entries(
    hass: HomeAssistant, device: Union[str, DeviceEntry]
):
    """ Get entires for the device """

    registry = await entity_registry.async_get_registry(hass)
    if isinstance(device, str):
        device_registry: DeviceRegistry = (
            await hass.helpers.device_registry.async_get_registry()
        )
        device_entry = device_registry.async_get(device)
    else:
        device_entry = device

    entries = (
        entity_registry.async_entries_for_device(registry, device_entry.id)
        if device_entry
        else None
    )

    return (device_entry, entries)
