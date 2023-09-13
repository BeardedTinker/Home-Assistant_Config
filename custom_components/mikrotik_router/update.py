"""Support for the Mikrotik Router update service."""
from __future__ import annotations

from logging import getLogger
from requests import get as requests_get
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.components.update import (
    UpdateEntity,
    UpdateDeviceClass,
    UpdateEntityFeature,
)

from .coordinator import MikrotikCoordinator
from .entity import MikrotikEntity, async_add_entities
from .update_types import (
    SENSOR_TYPES,
    SENSOR_SERVICES,
)

_LOGGER = getLogger(__name__)
DEVICE_UPDATE = "device_update"


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    _async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up entry for component"""
    dispatcher = {
        "MikrotikRouterOSUpdate": MikrotikRouterOSUpdate,
        "MikrotikRouterBoardFWUpdate": MikrotikRouterBoardFWUpdate,
    }
    await async_add_entities(hass, config_entry, dispatcher)


# ---------------------------
#   MikrotikRouterOSUpdate
# ---------------------------
class MikrotikRouterOSUpdate(MikrotikEntity, UpdateEntity):
    """Define an Mikrotik Controller Update entity."""

    def __init__(
        self,
        coordinator: MikrotikCoordinator,
        entity_description,
        uid: str | None = None,
    ):
        """Set up device update entity."""
        super().__init__(coordinator, entity_description, uid)

        self._attr_supported_features = UpdateEntityFeature.INSTALL
        self._attr_supported_features |= UpdateEntityFeature.BACKUP
        self._attr_supported_features |= UpdateEntityFeature.RELEASE_NOTES
        self._attr_title = self.entity_description.title

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return self._data[self.entity_description.data_attribute]

    @property
    def installed_version(self) -> str:
        """Version installed and in use."""
        return self._data["installed-version"]

    @property
    def latest_version(self) -> str:
        """Latest version available for install."""
        return self._data["latest-version"]

    async def options_updated(self) -> None:
        """No action needed."""

    async def async_install(self, version: str, backup: bool, **kwargs: Any) -> None:
        """Install an update."""
        if backup:
            self.coordinator.execute("/system/backup", "save", None, None)

        self.coordinator.execute("/system/package/update", "install", None, None)

    async def async_release_notes(self) -> str:
        """Return the release notes."""
        try:
            response = await self.coordinator.hass.async_add_executor_job(
                requests_get,
                f"https://mikrotik.com/download/changelogs?ax=loadLog&val={self._data['latest-version']}",
            )

            if response.status_code == 200:
                return response.text.replace(chr(10), "<br />")

        except Exception as e:
            _LOGGER.warning("Failed to download release notes (%s)", e)

        return "Failed to download release notes"

    @property
    def release_url(self) -> str:
        """URL to the full release notes of the latest version available."""
        return "https://mikrotik.com/download/changelogs"


# ---------------------------
#   MikrotikRouterBoardFWUpdate
# ---------------------------
class MikrotikRouterBoardFWUpdate(MikrotikEntity, UpdateEntity):
    """Define an Mikrotik Controller Update entity."""

    TYPE = DEVICE_UPDATE
    _attr_device_class = UpdateDeviceClass.FIRMWARE

    def __init__(
        self,
        coordinator: MikrotikCoordinator,
        entity_description,
        uid: str | None = None,
    ):
        """Set up device update entity."""
        super().__init__(coordinator, entity_description, uid)

        self._attr_supported_features = UpdateEntityFeature.INSTALL
        self._attr_title = self.entity_description.title

    @property
    def is_on(self) -> bool:
        """Return true if device is on."""
        return (
            self.data["routerboard"]["current-firmware"]
            != self.data["routerboard"]["upgrade-firmware"]
        )

    @property
    def installed_version(self) -> str:
        """Version installed and in use."""
        return self._data["current-firmware"]

    @property
    def latest_version(self) -> str:
        """Latest version available for install."""
        return self._data["upgrade-firmware"]

    async def options_updated(self) -> None:
        """No action needed."""

    async def async_install(self, version: str, backup: bool, **kwargs: Any) -> None:
        """Install an update."""
        self.coordinator.execute("/system/routerboard", "upgrade", None, None)
        self.coordinator.execute("/system", "reboot", None, None)
