from __future__ import annotations
from .const import DOMAIN
import requests
import logging
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_send
_LOGGER: Final = logging.getLogger(__name__)

def get_image_folder(hass):
    """Return the folder where images are stored."""
    return hass.config.path("www/open_epaper_link")

def get_image_path(hass, entity_id):
    """Return the path to the image for a specific tag."""
    return hass.config.path("www/open_epaper_link/open_epaper_link."+ str(entity_id).lower() + ".jpg")
async def send_tag_cmd(hass: HomeAssistant, entity_id: str, cmd: str) -> bool:
    """Send a command to an ESL Tag."""
    ip = hass.states.get(DOMAIN + ".ip").state
    mac = entity_id.split(".")[1].upper()
    url = f"http://{ip}/tag_cmd"

    data = {
        'mac': mac,
        'cmd': cmd
    }

    try:
        result = await hass.async_add_executor_job(lambda : requests.post(url, data=data))
        if result.status_code == 200:
            _LOGGER.info("Sent %s command to %s", cmd, entity_id)
        else:
            _LOGGER.error("Failed to send %s command to %s", cmd, entity_id)
    except Exception as e:
        _LOGGER.error("Failed to send %s command to %s: %s", cmd, entity_id, e)
        return False

async def reboot_ap(hass: HomeAssistant) -> bool:
    """Reboot the ESL Access Point."""
    ip = hass.states.get(DOMAIN + ".ip").state
    url = f"http://{ip}/reboot"

    try:
        result = await hass.async_add_executor_job(lambda : requests.post(url))
        if result.status_code == 200:
            hass
            _LOGGER.info("Rebooted ESL Access Point")
        else:
            _LOGGER.error("Failed to reboot ESL Access Point")
    except Exception as e:
        _LOGGER.error("Failed to reboot ESL Access Point: %s", e)
        return False

async def set_ap_config_item(hub, key: str, value: str|int) -> bool:
    """Set a configuration item on the Access Point."""
    if key in hub.ap_config and hub.ap_config[key] != value:
        data = {
            key: value
        }
        _LOGGER.debug(data)
        try:
            response = await hub._hass.async_add_executor_job(lambda: requests.post(f"http://{hub._host}/save_apcfg", data=data))
            if response.status_code == 200:
                hub.ap_config[key] = value
                async_dispatcher_send(hub._hass, f"{DOMAIN}_ap_config_update")
                return True
        except Exception as e:
            _LOGGER.error(f"Failed to set AP config {key}: {e}")
            return False