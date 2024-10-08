from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import EntityCategory
import logging
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