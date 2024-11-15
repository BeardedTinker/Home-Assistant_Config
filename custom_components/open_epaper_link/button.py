from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
import requests
import json
import logging

from .hw_map import get_hw_dimensions
from .util import send_tag_cmd, reboot_ap
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    hub = hass.data[DOMAIN][entry.entry_id]
    buttons = []
    for tag_mac in hub.esls:
        buttons.append(ClearPendingTagButton(hass, tag_mac, hub))
        buttons.append(ForceRefreshButton(hass, tag_mac, hub))
        buttons.append(RebootTagButton(hass, tag_mac, hub))
        buttons.append(ScanChannelsButton(hass, tag_mac, hub))
        buttons.append(IdentifyTagButton(hass,tag_mac,hub))
    buttons.append(RebootAPButton(hass, hub))
    async_add_entities(buttons)

class ClearPendingTagButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, tag_mac: str, hub) -> None:
        """Initialize the button."""
        self.hass = hass
        self._tag_mac = tag_mac
        self._entity_id = f"{DOMAIN}.{tag_mac}"
        self._hub = hub
        self._attr_name = f"{hub.data[tag_mac]['tagname']} Clear Pending"
        self._attr_unique_id = f"{tag_mac}_clear_pending"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = "mdi:broom"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._tag_mac)},
        }

    async def async_press(self) -> None:
        await send_tag_cmd(self.hass, self._entity_id, "clear")

class ForceRefreshButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, tag_mac: str, hub) -> None:
        """Initialize the button."""
        self.hass = hass
        self._tag_mac = tag_mac
        self._entity_id = f"{DOMAIN}.{tag_mac}"
        self._hub = hub
        self._attr_name = f"{hub.data[tag_mac]['tagname']} Force Refresh"
        self._attr_unique_id = f"{tag_mac}_force_refresh"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:refresh"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._tag_mac)},
        }

    async def async_press(self) -> None:
        await send_tag_cmd(self.hass, self._entity_id, "refresh")

class RebootTagButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, tag_mac: str, hub) -> None:
        """Initialize the button."""
        self.hass = hass
        self._tag_mac = tag_mac
        self._entity_id = f"{DOMAIN}.{tag_mac}"
        self._hub = hub
        self._attr_name = f"{hub.data[tag_mac]['tagname']} Reboot"
        self._attr_unique_id = f"{tag_mac}_reboot"
        self._attr_entity_category = EntityCategory.CONFIG
        self._attr_icon = "mdi:restart"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._tag_mac)},
        }

    async def async_press(self) -> None:
        await send_tag_cmd(self.hass, self._entity_id, "reboot")

class ScanChannelsButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, tag_mac: str, hub) -> None:
        """Initialize the button."""
        self.hass = hass
        self._tag_mac = tag_mac
        self._entity_id = f"{DOMAIN}.{tag_mac}"
        self._hub = hub
        self._attr_name = f"{hub.data[tag_mac]['tagname']} Scan Channels"
        self._attr_unique_id = f"{tag_mac}_scan_channels"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:wifi"

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._tag_mac)},
        }

    async def async_press(self) -> None:
        await send_tag_cmd(self.hass, self._entity_id, "scan")

class RebootAPButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, hub) -> None:
        """Initialize the button."""
        self.hass = hass
        self._hub = hub
        self._attr_name = "Reboot AP"
        self._attr_unique_id = "reboot_ap"
        self._attr_icon = "mdi:restart"

    @property
    def available(self) -> bool:
        return self._hub.online

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, "ap")},
        }

    async def async_press(self) -> None:
        await reboot_ap(self.hass)

class IdentifyTagButton(ButtonEntity):
    def __init__(self, hass: HomeAssistant, tag_mac: str, hub) -> None:
        self.hass = hass
        self._tag_mac = tag_mac
        self._hub = hub
        self._attr_name = f"{hub.data[tag_mac]['tagname']} Identify"
        self._attr_unique_id = f"{tag_mac}_identify"
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_icon = "mdi:eye"

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._tag_mac)},
        }

    async def async_press(self) -> None:
        ip = self._hub.data["ap"]["ip"]
        tag_name = self._hub.data[self._tag_mac]['tagname']
        tag_data = self._hub.data[self._tag_mac]
        width, height = get_hw_dimensions(self._hub.data[self._tag_mac]["hwtype"])

        title_font = f"fonts/bahnschrift30"
        info_font = f"fonts/bahnschrift20"
        title_y = height // 6
        mac_y = 2 * height // 6
        info_start_y = 2 * height // 6 + 10
        line_height = height // 10
        json_template = []
        if tag_name != self._tag_mac:
            json_template.append({"text": [width // 2, title_y, f"Tag: {tag_name}", title_font, 2, 4]})
        json_template.append({"text": [width // 2, mac_y, f"MAC: {self._tag_mac}", info_font, 1, 4]})

        more_info = [
            f"Battery: {tag_data.get('battery', 'N/A')}mV",
            # f"Temp: {tag_data.get('temperature', 'N/A')}°C",
            f"RSSI: {tag_data.get('rssi', 'N/A')}dB",
            f"LQI: {tag_data.get('lqi', 'N/A')}",
            f"HW: {tag_data.get('hwstring', 'N/A')} ({width}x{height})",
            f"AP: {ip}"
        ]

        for i, info in enumerate(more_info):
            y_position = info_start_y + i * line_height + 8
            json_template.append({"text": [10, y_position, info, info_font, 1, 0]})  # Left-aligned

        url = f"http://{ip}/jsonupload"
        payload = {
            "mac": self._tag_mac,
            "json": json.dumps(json_template),
        }

        try:
            response = await self.hass.async_add_executor_job(
                lambda: requests.post(url, data=payload)
            )
            if response.status_code == 200:
                _LOGGER.info(f"Sent identify command to tag {self._tag_mac}")
        except requests.RequestException as err:
            _LOGGER.error(f"Failed to send identify command to tag {self._tag_mac}: {err}")