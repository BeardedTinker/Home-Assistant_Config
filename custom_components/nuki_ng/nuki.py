from hashlib import sha256
from random import randint
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.network import get_url
from homeassistant.components import webhook

import requests
import logging
import json
import re
from datetime import timedelta, datetime, timezone
from urllib.parse import urlencode

from .constants import DOMAIN

_LOGGER = logging.getLogger(__name__)

BRIDGE_DISCOVERY_API = "https://api.nuki.io/discover/bridges"
BRIDGE_HOOK = "nuki_ng_bridge_hook"


class NukiInterface:
    def __init__(
        self, hass, *, bridge: str = None, token: str = None, web_token: str = None, use_hashed: bool = False
    ):
        self.hass = hass
        self.bridge = bridge
        self.token = token
        self.web_token = web_token
        self.use_hashed = False

    async def async_json(self, cb):
        response = await self.hass.async_add_executor_job(lambda: cb(requests))
        if response.status_code >= 300:
            raise ConnectionError(f"Http response: {response.status_code}")
        if response.status_code > 200:
            return dict()
        json_resp = response.json()
        return json_resp

    async def discover_bridge(self) -> str:
        try:
            response = await self.async_json(lambda r: r.get(BRIDGE_DISCOVERY_API))
            bridges = response.get("bridges", [])
            if len(bridges) > 0:
                return bridges[0]["ip"]
        except Exception as err:
            _LOGGER.exception(f"Failed to discover bridge:", err)
        return None

    def bridge_url(self, path: str, extra=None) -> str:
        extra_str = "&%s" % (urlencode(extra)) if extra else ""
        url = f"http://{self.bridge}:8080"
        if re.match(".+\\:\d+$", self.bridge):
            # Port inside
            url = f"http://{self.bridge}"
        if self.use_hashed:
            tz = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            rnr = randint(0, 65535)
            to_hash = "%s,%s,%s" % (tz, rnr, self.token)
            hashed = sha256(to_hash.encode("utf-8")).hexdigest()
            return f"{url}{path}?ts={tz}&rnr={rnr}&hash={hashed}{extra_str}"
        return f"{url}{path}?token={self.token}{extra_str}"

    async def bridge_list(self):
        return await self.async_json(lambda r: r.get(self.bridge_url("/list")))

    async def bridge_info(self):
        return await self.async_json(lambda r: r.get(self.bridge_url("/info")))

    async def bridge_reboot(self):
        return await self.async_json(lambda r: r.get(self.bridge_url("/reboot")))

    async def bridge_fwupdate(self):
        return await self.async_json(lambda r: r.get(self.bridge_url("/fwupdate")))

    async def bridge_lock_action(self, dev_id: str, action: str, device_type):
        actions_map = {
            "unlock": 1,
            "lock": 2,
            "open": 3,
            "lock_n_go": 4,
            "lock_n_go_open": 5,
            "activate_rto": 1,
            "deactivate_rto": 2,
            "electric_strike_actuation": 3,
            "activate_continuous_mode": 4,
            "deactivate_continuous_mode": 5,
        }
        return await self.async_json(
            lambda r: r.get(
                self.bridge_url(
                    "/lockAction",
                    dict(
                        action=actions_map[action],
                        nukiId=dev_id,
                        deviceType=device_type,
                    ),
                )
            )
        )

    async def web_lock_action(self, dev_id: str, action: str):
        actions_map = {
            "unlock": 1,
            "lock": 2,
            "open": 3,
            "lock_n_go": 4,
            "lock_n_go_open": 5,
            "activate_rto": 1,
            "deactivate_rto": 2,
            "electric_strike_actuation": 3,
            "activate_continuous_mode": 6,
            "deactivate_continuous_mode": 7,
        }
        await self.web_async_json(
            lambda r, h: r.post(
                self.web_url(f"/smartlock/{dev_id}/action"),
                headers=h,
                json=dict(action=actions_map.get(action)),
            )
        )

    async def bridge_remove_callback(self, callback: str):
        callbacks = await self.async_json(
            lambda r: r.get(self.bridge_url("/callback/list"))
        )
        _LOGGER.debug(f"bridge_remove_callback: {callbacks}, {callback}")
        callbacks_list = callbacks.get("callbacks", [])
        for item in callbacks_list:
            if item["url"] == callback:
                result = await self.async_json(
                    lambda r: r.get(
                        self.bridge_url("/callback/remove", {"id": item["id"]})
                    )
                )
                if not result.get("success", True):
                    raise ConnectionError(result.get("message"))
                return True
        return False

    async def bridge_check_callback(self, callback: str):
        callbacks = await self.async_json(
            lambda r: r.get(self.bridge_url("/callback/list"))
        )
        _LOGGER.debug(f"bridge_check_callback: {callbacks}, {callback}")
        result = dict()
        callbacks_list = callbacks.get("callbacks", [])
        if len(callbacks_list) and callbacks_list[0]["url"] == callback:
            _LOGGER.debug("Callback is set")
            return callbacks_list
        add_callbacks = [callback]
        for item in callbacks_list:
            if item["url"] != callback:
                add_callbacks.append(item["url"])
            await self.bridge_remove_callback(item["url"])
        for callback_url in add_callbacks[:3]:
            result = await self.async_json(
                lambda r: r.get(self.bridge_url("/callback/add", {"url": callback_url}))
            )
            if not result.get("success", True):
                raise ConnectionError(result.get("message"))
        _LOGGER.debug("Callback is set - re-added")
        callbacks = await self.async_json(
            lambda r: r.get(self.bridge_url("/callback/list"))
        )
        return callbacks.get("callbacks", [])

    def web_url(self, path):
        return f"https://api.nuki.io{path}"

    async def web_async_json(self, cb):
        return await self.async_json(
            lambda r: cb(r, {"authorization": f"Bearer {self.web_token}"})
        )

    def can_web(self):
        return True if self.web_token else False

    def can_bridge(self):
        return True if self.token and self.bridge else False

    async def web_list_all_auths(self, dev_id: str):
        result = {}
        response = await self.web_async_json(
            lambda r, h: r.get(self.web_url(f"/smartlock/{dev_id}/auth"), headers=h)
        )
        for item in response:
            result[item["id"]] = item
        return result

    async def web_list(self):
        door_state_map = {
            1: "deactivated",
            2: "door closed",
            3: "door opened",
            4: "door state unknown",
            5: "calibrating",
            16: "uncalibrated",
            240: "removed",
            255: "unknown",
        }
        device_state_map = {
            0: {
                0: "uncalibrated",
                1: "locked",
                2: "unlocking",
                3: "unlocked",
                4: "locking",
                5: "unlatched",
                6: "unlocked (lock 'n' go)",
                7: "unlatching",
                254: "motor blocked",
                255: "undefined",
            },
            2: {
                0: "untrained",
                1: "online",
                3: "ring to open active",
                5: "open",
                7: "opening",
                253: "boot run",
                255: "undefined",
            },
            4: {
                0: "uncalibrated",
                1: "locked",
                2: "unlocking",
                3: "unlocked",
                4: "locking",
                5: "unlatched",
                6: "unlocked (lock 'n' go)",
                7: "unlatching",
                254: "motor blocked",
                255: "undefined",
            },
        }
        resp = await self.web_async_json(
            lambda r, h: r.get(self.web_url(f"/smartlock"), headers=h)
        )
        result = []
        for item in resp:
            if item.get("type") not in (0, 2, 4):
                continue
            state = item.get("state", {})
            result.append(
                {
                    "deviceType": item.get("type"),
                    "nukiId": item.get("smartlockId"),
                    "name": item.get("name"),
                    "firmwareVersion": str(item.get("firmwareVersion")),
                    "lastKnownState": {
                        "mode": state.get("mode"),
                        "state": state.get("state"),
                        "stateName": device_state_map.get(item.get("type"), {}).get(
                            state.get("state")
                        ),
                        "batteryCritical": state.get("batteryCritical"),
                        "batteryCharging": state.get("batteryCharging"),
                        "batteryChargeState": state.get("batteryCharge"),
                        "keypadBatteryCritical": state.get("keypadBatteryCritical"),
                        "doorsensorState": state.get("doorState"),
                        "doorsensorStateName": door_state_map.get(
                            state.get("doorState")
                        ),
                        "timestamp": item.get("updateDate"),
                    },
                }
            )
        return result

    async def web_update_auth(self, dev_id: str, auth_id: str, changes: dict):
        await self.web_async_json(
            lambda r, h: r.post(
                self.web_url(f"/smartlock/{dev_id}/auth/{auth_id}"),
                headers=h,
                json=changes,
            )
        )


class NukiCoordinator(DataUpdateCoordinator):
    def __init__(self, hass, entry, config: dict):
        self.entry = entry
        self.api = NukiInterface(
            hass,
            bridge=config.get("address"),
            token=config.get("token"),
            web_token=config.get("web_token"),
            use_hashed=config.get("use_hashed", False),
        )
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_method=self._make_update_method(),
            update_interval=timedelta(seconds=config.get("update_seconds", 30)),
        )

        hook_id = "%s_%s" % (BRIDGE_HOOK, entry.entry_id)

        url = config.get("hass_url", get_url(hass))
        self.bridge_hook = "{}{}".format(url, webhook.async_generate_path(hook_id))
        webhook.async_unregister(hass, hook_id)
        webhook.async_register(
            hass,
            DOMAIN,
            "bridge",
            hook_id,
            handler=self._make_bridge_hook_handler(),
            local_only=True,
        )

    def _add_update(self, dev_id: str, update):
        data = self.data
        if not data:
            return None
        previous = data.get("devices", {}).get(dev_id)
        if not previous:
            return None
        last_state = previous.get("lastKnownState", {})
        for key in last_state:
            if key in update:
                last_state[key] = update[key]
        previous["lastKnownState"] = last_state
        self.async_set_updated_data(data)

    async def _update(self):
        try:
            callbacks_list = None
            bridge_info = None
            info_mapping = dict()
            device_list = None
            if self.api.can_bridge():
                try:
                    callbacks_list = await self.api.bridge_check_callback(
                        self.bridge_hook
                    )
                except Exception:
                    _LOGGER.exception(f"Failed to update callback {self.bridge_hook}")
                bridge_info = await self.api.bridge_info()
                for item in bridge_info.get("scanResults", []):
                    info_mapping[item.get("nukiId")] = item
                bridge_info["callbacks_list"] = callbacks_list
                device_list = await self.api.bridge_list()
            if self.api.can_web() and not device_list:
                device_list = await self.api.web_list()
            result = dict(devices={}, bridge_info=bridge_info)
            for item in device_list:
                dev_id = item["nukiId"]
                if self.api.can_web():
                    try:
                        item["web_auth"] = await self.api.web_list_all_auths(dev_id)
                    except ConnectionError:
                        _LOGGER.exception("Error while fetching auth:")
                result["devices"][dev_id] = item
                result["devices"][dev_id]["bridge_info"] = info_mapping.get(dev_id)
            _LOGGER.debug(f"_update: {json.dumps(result)}")
            return result
        except Exception as err:
            _LOGGER.exception(f"Failed to get latest data: {err}")
            raise UpdateFailed from err

    def _make_update_method(self):
        async def _update_data():
            return await self._update()

        return _update_data

    def _make_bridge_hook_handler(self):
        async def _hook_handler(hass, hook_id, request):
            body = await request.json()
            _LOGGER.debug(f"_hook_handler: {body}")
            self._add_update(body.get("nukiId"), body)

        return _hook_handler

    async def unload(self):
        try:
            if self.api.can_bridge():
                result = await self.api.bridge_remove_callback(self.bridge_hook)
                _LOGGER.debug(f"unload: {result} {self.bridge_hook}")
        except Exception:
            _LOGGER.exception(f"Failed to remove callback")

    async def action(self, dev_id: str, action: str):
        if self.api.can_bridge():
            device_type = self.device_data(dev_id).get("deviceType")
            result = await self.api.bridge_lock_action(dev_id, action, device_type)
            if result.get("success"):
                await self.async_request_refresh()
            _LOGGER.debug(f"bridge action result: {result}, {action}")
        elif self.api.can_web():
            await self.api.web_lock_action(dev_id, action)
            await self.async_request_refresh()
            _LOGGER.debug(f"web action result: {action}")

    async def do_reboot(self):
        if self.api.can_bridge():
            await self.api.bridge_reboot()
        else:
            raise ConnectionError("Not supported")

    async def do_fwupdate(self):
        if self.api.can_bridge():
            await self.api.bridge_fwupdate()
        else:
            raise ConnectionError("Not supported")

    async def do_delete_callback(self, callback):
        if self.api.can_bridge():
            await self.api.bridge_remove_callback(callback)
        else:
            raise ConnectionError("Not supported")

    def device_data(self, dev_id: str):
        return self.data.get("devices", {}).get(dev_id, {})

    def info_data(self):
        return self.data.get("info", {})

    def is_lock(self, dev_id: str) -> bool:
        return self.device_data(dev_id).get("deviceType") in (0, 4)

    def is_opener(self, dev_id: str) -> bool:
        return self.device_data(dev_id).get("deviceType") == 2

    def device_supports(self, dev_id: str, feature: str) -> bool:
        return self.device_data(dev_id).get("lastKnownState", {}).get(feature) != None

    async def update_web_auth(self, dev_id: str, auth: dict, changes: dict):
        if "id" not in auth:
            raise UpdateFailed("Invalid auth entry")
        await self.api.web_update_auth(dev_id, auth["id"], changes)
        data = self.data
        for key in changes:
            data.get(dev_id, {}).get("web_auth", {}).get(auth["id"], {})[key] = changes[
                key
            ]
        self.async_set_updated_data(data)
