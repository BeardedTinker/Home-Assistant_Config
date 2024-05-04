from __future__ import annotations
from .imagegen import *
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from . import hub
from .const import DOMAIN
from datetime import datetime
import logging
import pprint
import time

_LOGGER = logging.getLogger(__name__)

def rgb_to_rgb332(rgb):
    # Ensure that RGB values are in the range [0, 255]
    r, g, b = [max(0, min(255, x)) for x in rgb]
    
    # Convert RGB values to RGB332 format
    r = (r // 32) & 0b111  # 3 bits for red
    g = (g // 32) & 0b111  # 3 bits for green
    b = (b // 64) & 0b11   # 2 bits for blue

    # Combine the RGB332 components and convert to hex
    rgb332 = (r << 5) | (g << 2) | b

    return str(hex(rgb332)[2:].zfill(2))

def setup(hass, config):
    # callback for the draw custom service
    async def drawcustomservice(service: ServiceCall) -> None:
        ip = hass.states.get(DOMAIN + ".ip").state 
        entity_ids = service.data.get("entity_id")
        #sometimes you get a string, that's not nice to iterate over for ids....
        if isinstance(entity_ids, str):
            entity_ids=[entity_ids]

        dither = service.data.get("dither", False)
        ttl = service.data.get("ttl", 60)
        preloadtype = service.data.get("preloadtype", 0)
        preloadlut = service.data.get("preloadlut", 0)
        dry_run = service.data.get("dry-run", False)
        for entity_id in entity_ids:
            _LOGGER.info("Called entity_id: %s" % (entity_id))
            imgbuff = await hass.async_add_executor_job(customimage,entity_id, service, hass)
            id = entity_id.split(".")
            if (dry_run is False):
                result = await hass.async_add_executor_job(uploadimg, imgbuff, id[1], ip, dither,ttl,preloadtype,preloadlut,hass)
            else:
                _LOGGER.info("Running dry-run - no upload to AP!")
                result = True
                
    # callback for the image downlaod service
    async def dlimg(service: ServiceCall) -> None:
        ip = hass.states.get(DOMAIN + ".ip").state 
        entity_ids = service.data.get("entity_id")
        dither = service.data.get("dither", False)
        for entity_id in entity_ids:
            _LOGGER.info("Called entity_id: %s" % (entity_id))
            id = entity_id.split(".")
            imgbuff = await hass.async_add_executor_job(downloadimg, entity_id, service, hass)
            result = await hass.async_add_executor_job(uploadimg, imgbuff, id[1], ip, dither,300,0,0,hass)

    # callback for the 5 line service(depricated)
    async def lines5service(service: ServiceCall) -> None:
        ip = hass.states.get(DOMAIN + ".ip").state
        entity_ids = service.data.get("entity_id")
        for entity_id in entity_ids:
            _LOGGER.info("Called entity_id: %s" % (entity_id))
            imgbuff = gen5line(entity_id, service, hass)
            id = entity_id.split(".")
            result = await hass.async_add_executor_job(uploadimg, imgbuff, id[1], ip,False,300,0,0,hass)

    # callback for the 4 line service(depricated)
    async def lines4service(service: ServiceCall) -> None:
        ip = hass.states.get(DOMAIN + ".ip").state
        entity_ids = service.data.get("entity_id")
        for entity_id in entity_ids:
            _LOGGER.info("Called entity_id: %s" % (entity_id))
            imgbuff = gen4line(entity_id, service, hass)
            id = entity_id.split(".")
            result = await hass.async_add_executor_job(uploadimg, imgbuff, id[1], ip,False,300,0,0,hass)
            
    # callback for the setled service
    async def setled(service: ServiceCall) -> None:
        ip = hass.states.get(DOMAIN + ".ip").state
        entity_ids = service.data.get("entity_id")
        for entity_id in entity_ids:
            _LOGGER.info("Called entity_id: %s" % (entity_id))
            mac = entity_id.split(".")[1].upper()
            mode = service.data.get("mode", "")
            modebyte = "0"
            if(mode == "off"): modebyte = "0"
            if(mode == "flash"): modebyte = "1"
            modebyte = hex(int((int(service.data.get("brightness", 2) - 1) << 4)) + int(modebyte))[2:]
            repeats = int_to_hex_string(service.data.get("repeats", 2) - 1)
            color1 = rgb_to_rgb332(service.data.get("color1", ""))
            color2 = rgb_to_rgb332(service.data.get("color2", ""))
            color3 = rgb_to_rgb332(service.data.get("color3", ""))
            flashSpeed1 = hex(int(service.data.get("flashSpeed1", 2) * 10))[2:]
            flashSpeed2 = hex(int(service.data.get("flashSpeed2", 2) * 10))[2:]
            flashSpeed3 = hex(int(service.data.get("flashSpeed3", 2) * 10))[2:]
            flashCount1 = hex(int(service.data.get("flashCount1", 2)))[2:]
            flashCount2 = hex(int(service.data.get("flashCount2", 2)))[2:]
            flashCount3 = hex(int(service.data.get("flashCount3", 2)))[2:]
            delay1 = int_to_hex_string(int(service.data.get("delay1", 2) * 10))
            delay2 = int_to_hex_string(int(service.data.get("delay2", 2) * 10))
            delay3 = int_to_hex_string(int(service.data.get("delay3", 2) * 10))
            url = "http://" + ip + "/led_flash?mac=" + mac + "&pattern=" + modebyte + color1 + flashSpeed1 + flashCount1 + delay1 + color2 + flashSpeed2 + flashCount2 + delay2 + color3 + flashSpeed3 + flashCount3 + delay3 + repeats + "00";
            result = await hass.async_add_executor_job(requests.get, url)
            if result.status_code != 200:
               _LOGGER.warning(result.status_code)

    # register the services
    hass.services.register(DOMAIN, "dlimg", dlimg)
    hass.services.register(DOMAIN, "lines5", lines5service)
    hass.services.register(DOMAIN, "lines4", lines4service)
    hass.services.register(DOMAIN, "drawcustom", drawcustomservice)
    hass.services.register(DOMAIN, "setled", setled)
    # error haneling needs to be improved
    return True

def int_to_hex_string(number):
    hex_string = hex(number)[2:]
    if len(hex_string) == 1:
         hex_string = '0' + hex_string
    return hex_string
    
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub.Hub(hass, entry.data["host"], entry)
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, ["sensor"])
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

