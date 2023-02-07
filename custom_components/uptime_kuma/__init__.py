"""The Uptime Kuma integration."""
from __future__ import annotations

from pyuptimekuma import (
    UptimeKuma,
    UptimeKumaConnectionException,
    UptimeKumaException,
    UptimeKumaMonitor,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_PASSWORD,
    CONF_PORT,
    CONF_USERNAME,
    CONF_VERIFY_SSL,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import COORDINATOR_UPDATE_INTERVAL, DOMAIN, LOGGER, PLATFORMS


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Uptime Kuma from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    host: str = entry.data[CONF_HOST]
    port: int = entry.data[CONF_PORT]
    username: str = entry.data[CONF_USERNAME]
    password: str = entry.data[CONF_PASSWORD]
    verify_ssl: bool = entry.data[CONF_VERIFY_SSL]
    uptime_kuma_api = UptimeKuma(
        async_get_clientsession(hass),
        f"{host}:{port}",
        username,
        password,
        verify_ssl,
    )
    dev_reg = dr.async_get(hass)
    hass.data[DOMAIN][entry.entry_id] = coordinator = UptimeKumaDataUpdateCoordinator(
        hass,
        config_entry_id=entry.entry_id,
        dev_reg=dev_reg,
        api=uptime_kuma_api,
    )

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


class UptimeKumaDataUpdateCoordinator(DataUpdateCoordinator):
    """Data update coordinator for Uptime Kuma"""

    data: list[UptimeKumaMonitor]
    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry_id: str,
        dev_reg: dr.DeviceRegistry,
        api: UptimeKuma,
    ) -> None:
        """Initialize coordinator."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=COORDINATOR_UPDATE_INTERVAL,
        )
        self._config_entry_id = config_entry_id
        self._device_registry = dev_reg
        self.api = api

    async def _async_update_data(self) -> dict | None:
        """Update data."""
        try:
            response = await self.api.async_get_monitors()
        except UptimeKumaConnectionException as exception:
            raise UpdateFailed(exception) from exception
        except UptimeKumaException as exception:
            raise UpdateFailed(exception) from exception

        monitors: list[UptimeKumaMonitor] = response.data

        current_monitors = {
            list(device.identifiers)[0][1]
            for device in dr.async_entries_for_config_entry(
                self._device_registry, self._config_entry_id
            )
        }
        new_monitors = {str(monitor.monitor_name) for monitor in monitors}
        if stale_monitors := current_monitors - new_monitors:
            for monitor_id in stale_monitors:
                if device := self._device_registry.async_get_device(
                    {(DOMAIN, monitor_id)}
                ):
                    self._device_registry.async_remove_device(device.id)

        # If there are new monitors, we should reload the config entry so we can
        # create new devices and entities.
        if self.data and new_monitors - {
            str(monitor.monitor_name) for monitor in self.data
        }:
            self.hass.async_create_task(
                self.hass.config_entries.async_reload(self._config_entry_id)
            )
            return None

        return monitors
        # return await super()._async_update_data()
