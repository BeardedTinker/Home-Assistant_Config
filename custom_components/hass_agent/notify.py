import json
import logging
from typing import Any
from contextlib import suppress

from http import HTTPStatus
import requests

import re

from homeassistant.components.notify import (
    ATTR_TITLE,
    ATTR_DATA,
    BaseNotificationService,
)

from homeassistant.components import media_source, mqtt

from homeassistant.helpers.network import NoURLAvailableError, get_url

from homeassistant.const import (
    CONF_ID,
    CONF_NAME,
    CONF_URL,
)

from .const import CONF_DEFAULT_NOTIFICATION_TITLE

_logger = logging.getLogger(__name__)

CAMERA_PROXY_REGEX = re.compile(r"\/api\/camera_proxy\/camera\.(.*)")


def get_service(hass, config, discovery_info=None):
    """Get the HASS Agent notification service."""

    entry_id = discovery_info.get(CONF_ID, None)

    return HassAgentNotificationService(hass, discovery_info[CONF_NAME], entry_id)


class HassAgentNotificationService(BaseNotificationService):
    """Implementation of the HASS Agent notification service"""

    def __init__(self, hass, name, entry_id):
        """Initialize the service."""
        self._service_name = name
        self._device_name = name
        self._entry_id = entry_id
        self._hass = hass

    async def async_send_message(self, message: str, **kwargs: Any):
        """Send the message to the provided resource."""
        _logger.debug("Preparing notification")

        entry = self.hass.config_entries.async_get_entry(self._entry_id)

        title = kwargs.get(ATTR_TITLE, entry.options[CONF_DEFAULT_NOTIFICATION_TITLE])

        data = kwargs.get(ATTR_DATA, None)

        if data is None:
            data = dict()

        image = data.get("image", None)

        if image is not None:
            new_url = None

            camera_proxy_match = CAMERA_PROXY_REGEX.match(image)

            if camera_proxy_match is not None:
                camera = self.hass.states.get(f"camera.{camera_proxy_match.group(1)}")

                if camera is not None:
                    external_url = None
                    with suppress(NoURLAvailableError):  # external_url not configured
                        external_url = get_url(self.hass, allow_internal=False)

                    if external_url is not None:
                        access_token = camera.attributes["access_token"]
                        new_url = f"{external_url}{image}?token={access_token}"

            elif media_source.is_media_source_id(image):
                sourced_media = await media_source.async_resolve_media(self.hass, image)
                sourced_media = media_source.async_process_play_media_url(
                    self.hass, sourced_media.url
                )
                new_url = sourced_media

            if new_url is not None:
                data.update({"image": new_url})

        payload = {"message": message, "title": title, "data": data}

        _logger.debug("Sending notification")

        url = entry.data.get(CONF_URL, None)

        if url is None:
            await mqtt.async_publish(
                self.hass,
                f"hass.agent/notifications/{self._device_name}",
                json.dumps(payload),
            )
        else:
            try:

                def send_request(url, data):
                    """Sends the json request"""
                    return requests.post(url, json=data, timeout=10)

                response = await self.hass.async_add_executor_job(
                    send_request, f"{entry.data[CONF_URL]}/notify", payload
                )

                _logger.debug("Checking result")

                if response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
                    _logger.error(
                        "Server error. Response %d: %s",
                        response.status_code,
                        response.reason,
                    )
                elif response.status_code == HTTPStatus.BAD_REQUEST:
                    _logger.error(
                        "Client error (bad request). Response %d: %s",
                        response.status_code,
                        response.reason,
                    )
                elif response.status_code == HTTPStatus.NOT_FOUND:
                    _logger.debug(
                        "Server error (not found). Response %d: %s",
                        response.status_code,
                        response.reason,
                    )
                elif response.status_code == HTTPStatus.METHOD_NOT_ALLOWED:
                    _logger.error(
                        "Server error (method not allowed). Response %d",
                        response.status_code,
                    )
                elif response.status_code == HTTPStatus.REQUEST_TIMEOUT:
                    _logger.debug(
                        "Server error (request timeout). Response %d: %s",
                        response.status_code,
                        response.reason,
                    )
                elif response.status_code == HTTPStatus.NOT_IMPLEMENTED:
                    _logger.error(
                        "Server error (not implemented). Response %d: %s",
                        response.status_code,
                        response.reason,
                    )
                elif response.status_code == HTTPStatus.SERVICE_UNAVAILABLE:
                    _logger.error(
                        "Server error (service unavailable). Response %d",
                        response.status_code,
                    )
                elif response.status_code == HTTPStatus.GATEWAY_TIMEOUT:
                    _logger.error(
                        "Network error (gateway timeout). Response %d: %s",
                        response.status_code,
                        response.reason,
                    )
                elif response.status_code == HTTPStatus.OK:
                    _logger.debug(
                        "Success. Response %d: %s",
                        response.status_code,
                        response.reason,
                    )
                else:
                    _logger.debug(
                        "Unknown response %d: %s", response.status_code, response.reason
                    )
            except Exception as ex:
                _logger.debug("Error sending message: %s", ex)
