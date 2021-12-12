from __future__ import annotations
from .nuki import NukiCoordinator
from .constants import DOMAIN, PLATFORMS

from homeassistant.core import HomeAssistant
from homeassistant.helpers import service

# from homeassistant.helpers import device_registry
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
)

import logging

OPENER_TYPE = 1
LOCK_TYPE = 0

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    data = entry.as_dict()["data"]
    _LOGGER.debug(f"async_setup_entry: {data}")

    coordinator = NukiCoordinator(hass, entry, data)
    await coordinator.async_config_entry_first_refresh()
    hass.data[DOMAIN][entry.entry_id] = coordinator

    for p in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, p))
    return True


async def async_unload_entry(hass: HomeAssistant, entry):
    await hass.data[DOMAIN][entry.entry_id].unload()
    for p in PLATFORMS:
        await hass.config_entries.async_forward_entry_unload(entry, p)
    hass.data[DOMAIN].pop(entry.entry_id)
    return True


async def async_setup(hass: HomeAssistant, config) -> bool:
    hass.data[DOMAIN] = dict()

    async def async_reboot(call):
        for entry_id in await service.async_extract_config_entry_ids(hass, call):
            await hass.data[DOMAIN][entry_id].do_reboot()

    async def async_fwupdate(call):
        for entry_id in await service.async_extract_config_entry_ids(hass, call):
            await hass.data[DOMAIN][entry_id].do_fwupdate()

    async def async_delete_callback(call):
        for entry_id in await service.async_extract_config_entry_ids(hass, call):
            await hass.data[DOMAIN][entry_id].do_delete_callback(call.data.get("callback"))

    hass.services.async_register(DOMAIN, "bridge_reboot", async_reboot)
    hass.services.async_register(DOMAIN, "bridge_fwupdate", async_fwupdate)
    hass.services.async_register(
        DOMAIN, "bridge_delete_callback", async_delete_callback)

    return True


class NukiEntity(CoordinatorEntity):

    def __init__(self, coordinator, device_id: str):
        super().__init__(coordinator)
        self.device_id = device_id

    def set_id(self, prefix: str, suffix: str):
        self.id_prefix = prefix
        self.id_suffix = suffix

    def set_name(self, name: str):
        self._attr_name_suffix = name

    @property
    def name_suffix(self):
        return self._attr_name_suffix

    @property
    def get_name(self):
        return "Nuki %s" % (self.data.get("name", self.device_id))

    @property
    def name(self) -> str:
        return "%s %s" % (self.get_name, self.name_suffix)

    @property
    def unique_id(self) -> str:
        return "nuki-%s-%s" % (self.device_id, self.id_suffix)

    @property
    def available(self):
        if "nukiId" not in self.data:
            return False
        return super().available

    @property
    def data(self) -> dict:
        return self.coordinator.device_data(self.device_id)

    @property
    def last_state(self) -> dict:
        return self.data.get("lastKnownState", {})

    @property
    def model(self) -> str:
        if self.coordinator.is_lock(self.device_id):
            return "Nuki Smart Lock"
        if self.coordinator.is_opener(self.device_id):
            return "Nuki Opener"

    @property
    def device_info(self):
        return {
            "identifiers": {("id", self.device_id)},
            "name": self.get_name,
            "manufacturer": "Nuki",
            "model": self.model,
            "sw_version": self.data.get("firmwareVersion"),
            "via_device": (
                "id",
                self.coordinator.info_data().get("ids", {}).get("hardwareId")
            )
        }


class NukiBridge(CoordinatorEntity):
    def set_id(self, suffix: str):
        self.id_suffix = suffix

    def set_name(self, name: str):
        self.name_suffix = name

    @property
    def name(self) -> str:
        return "Nuki Bridge %s" % (self.name_suffix)

    @property
    def unique_id(self) -> str:
        return "nuki-bridge-%s-%s" % (self.get_id, self.id_suffix)

    @property
    def data(self) -> dict:
        return self.coordinator.data.get("bridge_info", {})

    @property
    def get_id(self):
        return self.data.get("ids", {}).get("hardwareId")

    @property
    def device_info(self):
        model = "Hardware Bridge" if self.data.get(
            "bridgeType", 1) else "Software Bridge"
        versions = self.data.get("versions", {})
        return {
            "identifiers": {("id", self.get_id)},
            "name": "Nuki Bridge",
            "manufacturer": "Nuki",
            "model": model,
            "sw_version": versions.get("firmwareVersion"),
        }
