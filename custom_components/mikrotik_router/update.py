"""Support for the Mikrotik Router update service."""

from __future__ import annotations

import asyncio
from logging import getLogger
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

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
from packaging.version import Version

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
            session = async_get_clientsession(self.hass)
            """Get concatenated changelogs from installed_version to latest_version in reverse order."""
            versions_to_fetch = generate_version_list(
                self._data["installed-version"], self._data["latest-version"]
            )

            tasks = [fetch_changelog(session, version) for version in versions_to_fetch]
            changelogs = await asyncio.gather(*tasks)

            # Combine all non-empty changelogs, maintaining reverse order
            combined_changelogs = "\n\n".join(filter(None, changelogs))
            return combined_changelogs.replace("*) ", "- ")

        except Exception as e:
            _LOGGER.warning("Failed to download release notes (%s)", e)

        return "Error fetching release notes."

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


async def fetch_changelog(session, version: str) -> str:
    """Asynchronously fetch the changelog for a given version."""
    url = f"https://cdn.mikrotik.com/routeros/{version}/CHANGELOG"
    try:
        async with session.get(url) as response:
            if response.status == 200:
                text = await response.text()
                return text.replace("*) ", "- ")
    except Exception as e:
        pass
    return ""


def generate_version_list(start_version: str, end_version: str) -> list:
    """Generate a list of version strings from start_version to end_version in reverse order."""
    start = Version(start_version)
    end = Version(end_version)
    versions = []

    current = end
    while current >= start:
        versions.append(str(current))
        current = decrement_version(current, start)

    return versions


def decrement_version(version: Version, start_version: Version) -> Version:
    """Decrement version by the smallest possible step without going below start_version."""
    if version.micro > 0:
        next_patch = version.micro - 1
        return Version(f"{version.major}.{version.minor}.{next_patch}")
    elif version.minor > 0:
        next_minor = version.minor - 1
        return Version(
            f"{version.major}.{next_minor}.999"
        )  # Assuming .999 as max patch version
    else:
        next_major = version.major - 1
        return Version(
            f"{next_major}.999.999"
        )  # Assuming .999 as max minor and patch version
