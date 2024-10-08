from __future__ import annotations
import asyncio
import random
import websocket
import socket
import aiohttp
import async_timeout
import backoff
import time
import json
import logging
import os
from threading import Thread
from typing import Any
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers import device_registry as dr

from .button import ClearPendingTagButton
from .const import DOMAIN
from .hw_map import is_in_hw_map, get_hw_string, get_hw_dimensions

_LOGGER: Final = logging.getLogger(__name__)

# Time to wait before trying to reconnect on disconnections.
_RECONNECT_SECONDS : int = 30

#Hub class for handling communication
class Hub:
    #the init function starts the thread for all other communication
    def __init__(self, hass: HomeAssistant, host: str, cfgentry: str) -> None:
        self._host = host
        self._cfgenty = cfgentry
        self._hass = hass
        self._name = host
        self._id = host.lower()
        self.esls = []
        self.data = dict()
        self.data["ap"] = dict()
        self.data["ap"]["ip"] =  self._host
        self.data["ap"]["systime"] = None
        self.data["ap"]["heap"] = None
        self.data["ap"]["recordcount"] = None
        self.data["ap"]["dbsize"] = None
        self.data["ap"]["littlefsfree"] = None
        self.ap_config = {}
        self.ap_config_loaded = asyncio.Event()
        self._hass.async_create_task(self.fetch_ap_config())
        self.eventloop = asyncio.get_event_loop()
        thread = Thread(target=self.connection_thread)
        thread.start()
        self.online = True
    #parses websocket messages
    def on_message(self,ws, message) -> None:
        data =  json.loads('{' + message.split("{", 1)[-1])
        if 'sys' in data:
            sys = data.get('sys')
            systime = sys.get('currtime')
            heap = sys.get('heap')
            recordcount = sys.get('recordcount')
            dbsize = sys.get('dbsize')
            littlefsfree = sys.get('littlefsfree')
            apstate = sys.get('apstate')
            runstate = sys.get('runstate')
            temp = sys.get('temp')
            rssi = sys.get('rssi')
            wifistatus = sys.get('wifistatus')
            wifissid = sys.get('wifissid')
            self._hass.states.set(DOMAIN + ".ip", self._host,{"icon": "mdi:ip","friendly_name": "AP IP","should_poll": False})
            self.data["ap"] = dict()
            self.data["ap"]["ip"] =  self._host
            self.data["ap"]["systime"] = systime
            self.data["ap"]["heap"] = heap
            self.data["ap"]["recordcount"] = recordcount
            self.data["ap"]["dbsize"] = dbsize
            self.data["ap"]["littlefsfree"] = littlefsfree
            self.data["ap"]["rssi"] = rssi
            self.data["ap"]["apstate"] = apstate
            self.data["ap"]["runstate"] = runstate
            self.data["ap"]["temp"] = temp
            self.data["ap"]["wifistatus"] = wifistatus
            self.data["ap"]["wifissid"] = wifissid
        elif 'tags' in data:
            tag = data.get('tags')[0]
            tagmac = tag.get('mac')
            lastseen = tag.get('lastseen')
            nextupdate = tag.get('nextupdate')
            nextcheckin = tag.get('nextcheckin')
            LQI = tag.get('LQI')
            RSSI = tag.get('RSSI')
            temperature = tag.get('temperature')
            batteryMv = tag.get('batteryMv')
            pending = tag.get('pending')
            hwType = tag.get('hwType')
            contentMode = tag.get('contentMode')
            alias = tag.get('alias')
            wakeupReason = tag.get('wakeupReason')
            capabilities = tag.get('capabilities')
            hashv = tag.get('hash')
            modecfgjson = tag.get('modecfgjson')
            isexternal = tag.get('isexternal')
            rotate = tag.get('rotate')
            lut = tag.get('lut')
            ch = tag.get('ch')
            ver = tag.get('ver')
            tagname = ""
            if alias:
                tagname = alias
            else:
                tagname = tagmac
            #required for automations
            if is_in_hw_map(hwType):
                width, height = get_hw_dimensions(hwType)
                self._hass.states.set(DOMAIN + "." + tagmac, hwType,{
                    "icon": "mdi:fullscreen",
                    "friendly_name": tagname,
                    "attr_unique_id": tagmac,
                    "unique_id": tagmac,
                    "device_class": "sensor",
                    "device_info": {
                        "identifiers": {(DOMAIN, tagmac)}
                    },
                    "should_poll": False,
                    "hwtype": hwType,
                    "hwstring": get_hw_string(hwType),
                    "width": width,
                    "height": height,
                })
            else:
                _LOGGER.warning(f"ID {hwType} not in hwmap, please open an issue on github about this.")

            self.data[tagmac] = dict()
            self.data[tagmac]["temperature"] = temperature
            self.data[tagmac]["rssi"] = RSSI
            self.data[tagmac]["battery"] = batteryMv
            self.data[tagmac]["lqi"] = LQI
            self.data[tagmac]["hwtype"] = hwType
            self.data[tagmac]["hwstring"] = get_hw_string(hwType)
            self.data[tagmac]["contentmode"] = contentMode
            self.data[tagmac]["lastseen"] = lastseen
            self.data[tagmac]["nextupdate"] = nextupdate
            self.data[tagmac]["nextcheckin"] = nextcheckin
            self.data[tagmac]["pending"] = pending
            self.data[tagmac]["wakeupReason"] = wakeupReason
            self.data[tagmac]["capabilities"] = capabilities
            self.data[tagmac]["external"] = isexternal
            self.data[tagmac]["alias"] = alias
            self.data[tagmac]["hashv"] = hashv
            self.data[tagmac]["modecfgjson"] = modecfgjson
            self.data[tagmac]["rotate"] = rotate
            self.data[tagmac]["lut"] = lut
            self.data[tagmac]["ch"] = ch
            self.data[tagmac]["ver"] = ver
            self.data[tagmac]["tagname"] = tagname
            #maintains a list of all tags, new entities should be generated here
            if tagmac not in self.esls:
                self.esls.append(tagmac)
                loop = self.eventloop
                asyncio.run_coroutine_threadsafe(self.reloadcfgett(),loop)
                #fire event with the wakeup reason
            lut = {0: "TIMED",1: "BOOT",2: "GPIO",3: "NFC",4: "BUTTON1",5: "BUTTON2",252: "FIRSTBOOT",253: "NETWORK_SCAN",254: "WDT_RESET"}
            event_data = {
                "device_id": tagmac,
                "type": lut[wakeupReason],
            }
            self._hass.bus.fire(DOMAIN + "_event", event_data)
        elif 'errMsg' in data:
            errmsg = data.get('errMsg')
        elif 'logMsg' in data:
            logmsg = data.get('logMsg')
        elif 'apitem' in data:
            self._hass.loop.call_soon_threadsafe(self.fetch_ap_config())
            logmsg = data.get('apitem')
        else:
            _LOGGER.debug("Unknown msg")
            _LOGGER.debug(data)
    #log websocket errors
    def on_error(self,ws, error) -> None:
        _LOGGER.debug("Websocket error, most likely on_message crashed")
        _LOGGER.debug(error)
    def on_close(self, ws, close_status_code, close_msg) -> None:
        _LOGGER.warning(
            f"Websocket connection lost to url={ws.url} "
            f"(close_status_code={close_status_code}, close_msg={close_msg}), "
            f"trying to reconnect every {_RECONNECT_SECONDS} seconds")
    #we could do something here
    def on_open(self,ws) -> None:
        _LOGGER.debug("WS started")

    #starts the websocket
    def connection_thread(self) -> None:
        while True:
            try:
                ws_url = "ws://" + self._host + "/ws"
                ws = websocket.WebSocketApp(
                    ws_url, on_message=self.on_message, on_error=self.on_error,
                    on_close=self.on_close, on_open=self.on_open)
                ws.run_forever(reconnect=_RECONNECT_SECONDS)
            except Exception as e:
                _LOGGER.exception(e)

            _LOGGER.error(f"open_epaper_link WebSocketApp crashed, reconnecting in {_RECONNECT_SECONDS} seconds")
            time.sleep(_RECONNECT_SECONDS)

    #we should do more here
    async def test_connection(self) -> bool:
        return True
    #reload is reqired to add new entities
    async def reloadcfgett(self) -> bool:
        await self._hass.config_entries.async_unload_platforms(self._cfgenty, ["sensor","camera","button"])
        await self._hass.config_entries.async_forward_entry_setups(self._cfgenty, ["sensor","camera","button"])
        return True

    async def fetch_ap_config(self):
        async with aiohttp.ClientSession() as session:
            async with async_timeout.timeout(10):
                response = await session.get(f"http://{self._host}/get_ap_config")
                if response.status == 200:
                    data = await response.json()
                    _LOGGER.info(f"AP config: {data}")
                    self.ap_config = data
                    self.ap_config_loaded.set()
                else:
                    _LOGGER.error(f"Failed to fetch AP config: {response.status}")
