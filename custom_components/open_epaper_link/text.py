from homeassistant.components.text import TextEntity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN
from .util import set_ap_config_item


class APConfigTextBase(TextEntity):
    def __init__(self, hub, key, name, icon):
        self._hub = hub
        self._key = key
        self._attr_name = f"AP {name}"
        self._attr_unique_id = f"{hub._id}_{key}"
        self._attr_icon = icon
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def available(self) -> bool:
        return self._hub.ap_config_loaded.is_set() and self._key in self._hub.ap_config

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "ap")},
            "name": "OpenEPaperLink AP",
            "model": "esp32",
            "manufacturer": "OpenEPaperLink",
        }

    @property
    def native_value(self):
        return self._hub.ap_config.get(self._key)

    async def async_set_value(self, value: str) -> None:
        await set_ap_config_item(self._hub, self._key, value)

    @callback
    def _handle_ap_config_update(self):
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass,
                f"{DOMAIN}_ap_config_update",
                self._handle_ap_config_update,
            )
        )


async def async_setup_entry(hass, config_entry, async_add_entities):
    hub = hass.data[DOMAIN][config_entry.entry_id]
    entities = [
        APConfigTextBase(hub, "alias", "Alias", "mdi:rename-box"),
        APConfigTextBase(hub, "repo", "Repository", "mdi:source-repository"),
    ]
    async_add_entities(entities)