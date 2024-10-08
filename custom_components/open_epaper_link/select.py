from __future__ import annotations

from html.entities import html5

from homeassistant.components.select import SelectEntity
from homeassistant.core import callback
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN

import logging

from .util import set_ap_config_item

_LOGGER = logging.getLogger(__name__)

class APConfigSelectBase(SelectEntity):
    def __init__(self, hub, key, name, icon, options):
        self._hub = hub
        self._key = key
        self._attr_name = f"AP {name}"
        self._attr_unique_id = f"{hub._id}_{key}"
        self._attr_icon = icon
        self._attr_options = options
        self._attr_entity_category = EntityCategory.CONFIG
        self._options_map = {}
        self._attr_options = list(self._options_map.values())

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "ap")},
            "name": "OpenEPaperLink AP",
            "model": "esp32",
            "manufacturer": "OpenEPaperLink",
        }
    @property
    def available(self) -> bool:
        return self._hub.ap_config_loaded.is_set() and self._key in self._hub.ap_config

    @property
    def current_option(self) -> str:
        value = self._hub.ap_config.get(self._key)
        return self._options_map.get(value)

    async def async_select_option(self, option: str) -> None:
        value = get_key_from_value(self._options_map,option)
        if value is not None:
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

class APChannelSelect(APConfigSelectBase):
    def __init__(self, hub, key, name, icon, options):
        super().__init__(hub, key, name, icon, options)
        self._options_map = {
            0: "auto",
            11: "11",
            15: "15",
            20: "20",
            25: "25",
            26: "26"
        }
        self._attr_options = list(self._options_map.values())

class APBrightnessSelect(APConfigSelectBase):
    def __init__(self, hub, key, name, icon, options):
        super().__init__(hub, key, name, icon, options)
        self._options_map = {
            0: "off",
            15: "10%",
            31: "25%",
            127: "50%",
            191: "75%",
            255: "100%"
        }
        self._attr_options = list(self._options_map.values())

class APTFTBrightnessSelect(APConfigSelectBase):
    def __init__(self, hub, key, name, icon, options):
        super().__init__(hub, key, name, icon, options)
        self._options_map = {
            0: "off",
            20: "10%",
            64: "25%",
            128: "50%",
            192: "75%",
            255: "100%"
        }
        self._attr_options = list(self._options_map.values())

class APMaxSleepSelect(APConfigSelectBase):
    def __init__(self, hub, key, name, icon, options):
        super().__init__(hub, key, name, icon, options)
        self._options_map = {
            0: "shortest (40 sec)",
            5: "5 min",
            10: "10 min",
            30: "30 min",
            60: "1 hour"
        }
        self._attr_options = list(self._options_map.values())

class APLockInventorySelect(APConfigSelectBase):
    def __init__(self, hub, key, name, icon, options):
        super().__init__(hub, key, name, icon, options)
        self._options_map = {
            0: "no",
            1: "locked: don't add new tags",
            2: "learning: only add booting tags"

        }
        self._attr_options = list(self._options_map.values())

class APWifiPowerSelect(APConfigSelectBase):
    def __init__(self, hub, key, name, icon, options):
        super().__init__(hub, key, name, icon, options)
        self._options_map = {
            78: "19.5 dBm",
            76: "19.0 dBm",
            74: "18.5 dBm",
            68: "17.0 dBm",
            60: "15.0 dBm",
            52: "13.0 dBm",
            44: "11.0 dBm",
            34: "8.5 dBm",
            28: "7.0 dBm",
            20: "5.0 dBm",
            8: "2.0 dBm",
        }
        self._attr_options = list(self._options_map.values())

class APContentLanguageSelect(APConfigSelectBase):
    def __init__(self, hub, key, name, icon, options):
        super().__init__(hub, key, name, icon, options)
        self._options_map = {
            0: "EN English",
            1: "NL Nederlands",
            2: "DE Deutsch",
            4: "FR Français",
            3: "NO Norsk",
            5: "CZ Čeština",
            6: "SK Slovenčina",
            7: "PL Polski",
            8: "ES Español",
            9: "SV Svenska",
            10: "DK Dansk",
            11: "ET Eesti"
        }
        self._attr_options = list(self._options_map.values())

class APTimeHourSelect(APConfigSelectBase):
    def __init__(self, hub, key, name, icon, options):
        super().__init__(hub, key, name, icon, options)
        self._attr_options = [f"{hour:02d}:00" for hour in range(24)]

    @property
    def current_option(self) -> str | None:
        """Return the current selected option."""
        if not self.available:
            return None
        hour = self._hub.ap_config.get(self._key)
        if hour is not None:
            return f"{int(hour):02d}:00"
        return None

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        hour = int(option.split(':')[0])
        await set_ap_config_item(self._hub, self._key, hour)

class APTimezoneSelect(APConfigSelectBase):
    def __init__(self, hub, key, name, icon, options):
        super().__init__(hub, key, name, icon, options)
        self._options_map = {
            "CET-1CEST-2,M3.5.0/02:00:00,M10.5.0/03:00:00": "Central European Time",
            "EET-2EEST-3,M3.5.0/03:00:00,M10.5.0/04:00:00": "Athens, Greece",
            "GMT+0IST-1,M3.5.0/01:00:00,M10.5.0/02:00:00": "Dublin, Ireland",
            # "EET-2EEST-3,M3.5.0/03:00:00,M10.5.0/04:00:00": "Helsinki, Finland",
            "WET-0WEST-1,M3.5.0/01:00:00,M10.5.0/02:00:00": "Lisbon, Portugal",
            "GMT+0BST-1,M3.5.0/01:00:00,M10.5.0/02:00:00": "London, Great Britain",
            "EET-2EEST,M3.5.0/3,M10.5.0/4": "Kyiv, Ukraine",
            "HAW10": "Hawaii Time",
            "AKST9AKDT": "Alaska Time",
            "PST8PDT": "Pacific Time",
            "MST7MDT": "Mountain Time",
            "MST7": "Arizona, no DST",
            "CST6CDT": "Central Time",
            "EST5EDT": "Eastern Time",
            "EST-10EDT-11,M10.5.0/02:00:00,M3.5.0/03:00:00": "Melbourne, Sydney",
            "WST-8": "Perth",
            "EST-10": "Brisbane",
            "CST-9:30CDT-10:30,M10.5.0/02:00:00,M3.5.0/03:00:00": "Adelaide",
            "CST-9:30": "Darwin",
            "EST-10EDT-11,M10.1.0/02:00:00,M3.5.0/03:00:00": "Hobart",
            "NZST-12NZDT-13,M9.4.0/02:00:00,M4.1.0/03:00:00": "New Zealand",
            "JST-9": "Tokyo",
            "WIB-7": "Jakarta",
            "GMT+2": "Jerusalem",
            "SGT-8": "Singapore",
            "ULAT-8ULAST,M3.5.0/2,M9.5.0/2": "Ulaanbaatar, Mongolia",
            "BRST+3BRDT+2,M10.3.0,M2.3.0": "Brazil, Sao Paulo",
            "UTC+3": "Argentina",
            "CST+6": "Central America"
        }
        self._attr_options = list(self._options_map.values())

async def async_setup_entry(hass, config_entry, async_add_entities):
    hub = hass.data[DOMAIN][config_entry.entry_id]
    entities = [
        APChannelSelect(hub, "channel", "IEEE 802.15.4 channel", "mdi:wifi", []),
        APBrightnessSelect(hub, "led", "RGB LED brightness", "mdi:brightness-5", []),
        APTFTBrightnessSelect(hub, "tft", "TFT brightness", "mdi:brightness-5", []),
        APMaxSleepSelect(hub, "maxsleep", "Maximum Sleep", "mdi:sleep", []),
        APLockInventorySelect(hub, "lock", "Lock tag inventory", "mdi:lock", []),
        APWifiPowerSelect(hub, "wifipower", "Wifi power", "wifi-strength", []),
        APContentLanguageSelect(hub, "language", "Language", "mdi:translate", []),
        APTimeHourSelect(hub,"sleeptime1","No updates between 1 (from)","mdi:sleep",[]),
        APTimeHourSelect(hub,"sleeptime2","No updates between 2 (to)","mdi:sleep",[]),
        APConfigSelectBase(hub, "subghzchannel", "Sub-GHz Channel", "mdi:radio-tower", [str(i) for i in range(0, 10)]),
        APTimezoneSelect(hub, "timezone", "Timezone", "mdi:earth-clock", [])
    ]
    async_add_entities(entities)

def get_key_from_value(options_map, val):
    return list(options_map.keys())[list(options_map.values()).index(val)]