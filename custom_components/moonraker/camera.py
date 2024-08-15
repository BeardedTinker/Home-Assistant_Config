"""Support for Moonraker camera."""

from __future__ import annotations

import logging

from homeassistant.components.camera import Camera
from homeassistant.components.mjpeg.camera import MjpegCamera
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_URL,
    CONF_OPTION_CAMERA_STREAM,
    CONF_OPTION_CAMERA_SNAPSHOT,
    CONF_OPTION_CAMERA_PORT,
    CONF_OPTION_THUMBNAIL_PORT,
    DOMAIN,
    METHODS,
    PRINTSTATES,
)

_LOGGER = logging.getLogger(__name__)
DEFAULT_PORT = 80

hardcoded_camera = {
    "name": "webcam",
    "location": "printer",
    "service": "mjpegstreamer-adaptive",
    "target_fps": "15",
    "stream_url": "/webcam/?action=stream",
    "snapshot_url": "/webcam/?action=snapshot",
    "flip_horizontal": False,
    "flip_vertical": False,
    "rotation": 0,
    "source": "database",
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the available Moonraker camera."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    camera_cnt = 0

    try:
        if (
            config_entry.options.get(CONF_OPTION_CAMERA_STREAM) is not None
            and config_entry.options.get(CONF_OPTION_CAMERA_STREAM) != ""
        ):
            hardcoded_camera["stream_url"] = config_entry.options.get(
                CONF_OPTION_CAMERA_STREAM
            )
            hardcoded_camera["snapshot_url"] = config_entry.options.get(
                CONF_OPTION_CAMERA_SNAPSHOT
            )
            async_add_entities(
                [MoonrakerCamera(config_entry, coordinator, hardcoded_camera, 100)]
            )
            camera_cnt += 1
        else:
            cameras = await coordinator.async_fetch_data(METHODS.SERVER_WEBCAMS_LIST)
            for camera_id, camera in enumerate(cameras["webcams"]):
                async_add_entities(
                    [MoonrakerCamera(config_entry, coordinator, camera, camera_id)]
                )
                camera_cnt += 1
    except Exception:
        _LOGGER.info("Could not add any cameras from the API list")

    if camera_cnt == 0:
        _LOGGER.info("No Camera in the list, trying hardcoded")
        async_add_entities(
            [MoonrakerCamera(config_entry, coordinator, hardcoded_camera, 0)]
        )

    async_add_entities(
        [
            PreviewCamera(
                config_entry,
                coordinator,
                async_get_clientsession(hass, verify_ssl=False),
            )
        ]
    )


class MoonrakerCamera(MjpegCamera):
    """Representation of an Moonraker Camera Stream."""

    def __init__(self, config_entry, coordinator, camera, camera_id) -> None:
        """Initialize as a subclass of MjpegCamera."""

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)}
        )
        if (
            config_entry.options.get(CONF_OPTION_CAMERA_PORT) is not None
            and config_entry.options.get(CONF_OPTION_CAMERA_PORT) != ""
        ):
            self.port = config_entry.options.get(CONF_OPTION_CAMERA_PORT)
        else:
            self.port = DEFAULT_PORT

        if camera["stream_url"].startswith("http"):
            self.url = ""
        else:
            self.url = f"http://{config_entry.data.get(CONF_URL)}:{self.port}"

        _LOGGER.info(f"Connecting to camera: {self.url}{camera['stream_url']}")

        super().__init__(
            device_info=self._attr_device_info,
            mjpeg_url=f"{self.url}{camera['stream_url']}",
            name=f"{coordinator.api_device_name} {camera['name']}",
            still_image_url=f"{self.url}{camera['snapshot_url']}",
            unique_id=f"{config_entry.entry_id}_{camera['name']}_{camera_id}",
        )


class PreviewCamera(Camera):
    """Representation of the gcode thumnail."""

    _attr_is_streaming = False

    def __init__(self, config_entry, coordinator, session) -> None:
        """Initialize as a subclass of Camera for the Thumbnail Preview."""

        super().__init__()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, config_entry.entry_id)}
        )
        self.url = config_entry.data.get(CONF_URL)
        self.coordinator = coordinator
        self._attr_name = f"{coordinator.api_device_name} Thumbnail"
        self._attr_unique_id = f"{config_entry.entry_id}_thumbnail"
        self._session = session
        self._current_pic = None
        self._current_path = ""

        if (
            config_entry.options.get(CONF_OPTION_THUMBNAIL_PORT) is not None
            and config_entry.options.get(CONF_OPTION_THUMBNAIL_PORT) != ""
        ):
            self.port = config_entry.options.get(CONF_OPTION_THUMBNAIL_PORT)
        else:
            self.port = DEFAULT_PORT

    async def async_camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        """Return current camera image."""
        _LOGGER.debug("Trying to get thumbnail ")
        if (
            self.coordinator.data["status"]["print_stats"]["state"]
            != PRINTSTATES.PRINTING.value
        ):
            _LOGGER.debug("Not printing, no thumbnail")
            return None

        del width, height

        new_path = self.coordinator.data["thumbnails_path"]

        _LOGGER.debug(f"Thumbnail new_path: {new_path}")
        if self._current_path == new_path and self._current_pic is not None:
            _LOGGER.debug("no change in thumbnail, returning cached")
            return self._current_pic

        if new_path == "" or new_path is None:
            self._current_pic = None
            self._current_path = ""
            _LOGGER.debug("Empty path, no thumbnail")
            return None

        new_path = new_path.replace(" ", "%20")

        _LOGGER.debug(
            f"Fetching new thumbnail: http://{self.url}:{self.port}/server/files/gcodes/{new_path}"
        )
        response = await self._session.get(
            f"http://{self.url}:{self.port}/server/files/gcodes/{new_path}"
        )

        self._current_path = new_path
        self._current_pic = await response.read()

        return self._current_pic
