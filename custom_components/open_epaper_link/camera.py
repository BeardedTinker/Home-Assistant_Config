from __future__ import annotations
from .const import DOMAIN
from .util import get_image_path
import logging
import datetime
import mimetypes
import os
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.components.camera import Camera
from homeassistant.const import ATTR_ENTITY_ID, CONF_FILE_PATH, CONF_NAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER: Final = logging.getLogger(__name__)

async def async_setup_entry(hass, config_entry, async_add_entities):
    hub = hass.data[DOMAIN][config_entry.entry_id]
    new_devices = []
    for esls in hub.esls:
        if hub.data[esls]["lqi"] != 100 or hub.data[esls]["rssi"] != 100:
            image_path = get_image_path(hass, "open_epaper_link." + str(esls).lower())
            if os.path.exists(image_path):
                camera = LocalFile(esls, image_path, hub)
                new_devices.append(camera)
            else:
                _LOGGER.warning(f"Could not find image for ESL {esls}")
    if new_devices:
        async_add_entities(new_devices,True)

class LocalFile(Camera):

    def __init__(self, esls, file_path,hub):
        super().__init__()
        Camera.__init__(self)
        self._attr_unique_id = f"{esls}_cam"
        self._hub = hub
        self._name = hub.data[esls]["tagname"] + " Content"
        self._eslid = esls
        self.check_file_path_access(file_path)
        self._file_path = file_path
        content, _ = mimetypes.guess_type(file_path)
        if content is not None:
            self.content_type = content
    @property
    def device_info(self) -> DeviceInfo:
        return {
            "identifiers": {(DOMAIN, self._eslid)}
        }

    @property
    def name(self):
        return self._name

    def camera_image(
        self, width: int | None = None, height: int | None = None
    ) -> bytes | None:
        try:
            with open(self._file_path, "rb") as file:
                return file.read()
        except FileNotFoundError:
            _LOGGER.warning(f"Could not read image from file: {self._file_path}")
            return None
        except IOError as error:
            _LOGGER.error(f"Could not read image from file: {error}")
            return None

    def check_file_path_access(self, file_path):
        """Check that filepath given is readable."""

    def update_file_path(self, file_path):
        self._file_path = file_path
        self.schedule_update_ha_state()

    @property
    def extra_state_attributes(self):
        return {"file_path": self._file_path}
