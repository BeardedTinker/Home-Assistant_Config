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
from .const import DOMAIN

_LOGGER: Final = logging.getLogger(__name__)

# Time to wait before trying to reconnect on disconnections.
_RECONNECT_SECONDS : int = 30

#Hub class for handeling communication
class Hub:
    #the init function starts the thread for all other communication
    def __init__(self, hass: HomeAssistant, host: str,cfgenty: str) -> None:
        self._host = host
        self._cfgenty = cfgenty
        self._hass = hass
        self._name = host
        self._id = host.lower()
        self.esls = []
        self.data = dict()
        self.data["ap"] = dict()
        self.data["ap"]["ip"] =  self._host;
        self.data["ap"]["systime"] = None;
        self.data["ap"]["heap"] = None;
        self.data["ap"]["recordcount"] = None;
        self.data["ap"]["dbsize"] = None;
        self.data["ap"]["littlefsfree"] = None;
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
            self.data["ap"]["ip"] =  self._host;
            self.data["ap"]["systime"] = systime;
            self.data["ap"]["heap"] = heap;
            self.data["ap"]["recordcount"] = recordcount;
            self.data["ap"]["dbsize"] = dbsize;
            self.data["ap"]["littlefsfree"] = littlefsfree;
            self.data["ap"]["rssi"] = rssi;
            self.data["ap"]["apstate"] = apstate;
            self.data["ap"]["runstate"] = runstate;
            self.data["ap"]["temp"] = temp;
            self.data["ap"]["wifistatus"] = wifistatus;
            self.data["ap"]["wifissid"] = wifissid;
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
            hwmap = {
                0: ["M2 1.54\"", 152, 152],
                1: ["M2 2.9\"",  296, 128],
                2: ["M2 4.2\"",  400, 300],
                5: ["M2 7.4\"",  640, 384],
                17: ["M2 2.9\" (NFC)", 296, 128],
                18: ["M2 4.2\" (NFC)",  400, 300],
                26: ["M2 7.4\" (outdated)",  640, 384],
                33: ["M2 2.9\"", 296, 128],
                38: ["M2 7.4 BW\"",  640, 384],
                45: ["M3 12.2\"",  960, 768],
                46: ["M3 9.7\"",  960, 672],
                47: ["M3 4.3\"",  522, 152],
                48: ["M3 1.6\"",  200, 200],
                49: ["M3 2.2\"",  296, 160],
                50: ["M3 2.6\"",  360, 184],
                51: ["M3 2.9\"",  384, 168],
                52: ["M3 4.2\"",  400, 300],
                53: ["M3 6.0\"",  600, 448],
                54: ["M3 7.5\"",  800, 480],
                67: ["M3 1.3\" Peghook",  144, 200],
                69: ["M3 2.2\" Lite",  250, 128],
                70: ["M3 2.2\" BW",  296, 160],
                84: ["HS BW 2.13\"",  256, 128],
                85: ["HS BWR 2.13\"",  256, 128],
                86: ["HS BWR 2.66\"",  296, 152],
                96: ["HS BWY 3.5\"",  384, 184],
                97: ["HS BWR 3.5\"",  384, 184],
                98: ["HS BW 3.5\"",  384, 184],
                102: ["HS BWY 7.5\"",  800, 480],
                103: ["HS BWY 2.0\"",  152, 200],
                128: ["Chroma 7.4\"", 640, 384],
                130: ["Chroma29 2.9\"", 296, 128],
                131: ["Chroma42 4\"", 400, 300],
                176: ["Gicisky BLE EPD BW 2.1\"",  212, 104],
                177: ["Gicisky BLE EPD BWR 2.13\"",  250, 128],
                178: ["Gicisky BLE EPD BW 2.9\"",  296, 128],
                179: ["Gicisky BLE EPD BWR 2.9\"",  296, 128],
                181: ["Gicisky BLE EPD BWR 4.2\"",  400, 300],
                186: ["Gicisky BLE TFT 2.13\"",  250, 132],
                191: ["Gicisky BLE Unknown",  0, 0],
                190: ["ATC MiThermometer BLE",  6, 8],
                224: ["AP display",  320, 170],
                225: ["AP display",  160, 80],
                240: ["Segmented",  0, 0]
            }
            if hwType in hwmap:
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
                    "hwstring": hwmap[hwType][0],
                    "width": hwmap[hwType][1],
                    "height": hwmap[hwType][2],
                })
            else:
                _LOGGER.warning("Id not in hwmap, please open an issue on github about this." +str(hwType))
                
            self.data[tagmac] = dict()
            self.data[tagmac]["temperature"] = temperature
            self.data[tagmac]["rssi"] = RSSI
            self.data[tagmac]["battery"] = batteryMv
            self.data[tagmac]["lqi"] = LQI
            self.data[tagmac]["hwtype"] = hwType
            self.data[tagmac]["hwstring"] = hwmap[hwType][0]
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
            ermsg = data.get('errMsg');
        elif 'logMsg' in data:
            logmsg = data.get('logMsg');
        elif 'apitem' in data:
            logmsg = data.get('apitem');
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
        await self._hass.config_entries.async_unload_platforms(self._cfgenty, ["sensor","camera"])
        await self._hass.config_entries.async_forward_entry_setups(self._cfgenty, ["sensor","camera"])
        return True
