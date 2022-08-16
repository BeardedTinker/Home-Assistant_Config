"""Support for the Mikrotik Router update service."""

import logging
from typing import Any
from requests import get as requests_get
from homeassistant.components.update import (
    UpdateEntity,
    UpdateDeviceClass,
    UpdateEntityFeature,
)
from .model import model_async_setup_entry, MikrotikEntity
from .update_types import (
    SENSOR_TYPES,
    SENSOR_SERVICES,
)

_LOGGER = logging.getLogger(__name__)
DEVICE_UPDATE = "device_update"


# ---------------------------
#   async_setup_entry
# ---------------------------
async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up entry for component"""
    dispatcher = {
        "MikrotikRouterOSUpdate": MikrotikRouterOSUpdate,
        "MikrotikRouterBoardFWUpdate": MikrotikRouterBoardFWUpdate,
    }
    await model_async_setup_entry(
        hass,
        config_entry,
        async_add_entities,
        SENSOR_SERVICES,
        SENSOR_TYPES,
        dispatcher,
    )


# ---------------------------
#   MikrotikRouterOSUpdate
# ---------------------------
class MikrotikRouterOSUpdate(MikrotikEntity, UpdateEntity):
    """Define an Mikrotik Controller Update entity."""

    TYPE = DEVICE_UPDATE
    _attr_device_class = UpdateDeviceClass.FIRMWARE

    def __init__(
        self,
        inst,
        uid: "",
        mikrotik_controller,
        entity_description,
    ):
        """Set up device update entity."""
        super().__init__(inst, uid, mikrotik_controller, entity_description)

        self._attr_supported_features = UpdateEntityFeature.INSTALL
        self._attr_supported_features |= UpdateEntityFeature.BACKUP
        self._attr_supported_features |= UpdateEntityFeature.RELEASE_NOTES

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
            self._ctrl.execute("/system/backup", "save", None, None)

        self._ctrl.execute("/system/package/update", "install", None, None)

    async def async_release_notes(self) -> str:
        """Return the release notes."""
        try:
            response = await self._ctrl.hass.async_add_executor_job(
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

    def __init__(
        self,
        inst,
        uid: "",
        mikrotik_controller,
        entity_description,
    ):
        """Set up device update entity."""
        super().__init__(inst, uid, mikrotik_controller, entity_description)
        _LOGGER.error(self._data)

        self._attr_supported_features = UpdateEntityFeature.INSTALL

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
        self._ctrl.execute("/system/routerboard", "upgrade", None, None)
        self._ctrl.execute("/system", "reboot", None, None)
