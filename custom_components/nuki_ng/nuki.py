from hashlib import sha256
from random import randint
from socket import timeout
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.network import get_url
from homeassistant.components import webhook
from homeassistant.exceptions import HomeAssistantError

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
BRIDGE_TIMEOUT = 10

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
        if not response.ok:
            raise HomeAssistantError(f"Http response for {response.request.url}: {response.status_code} {response.reason}")
        if response.status_code > 200:
            _LOGGER.debug(f"async_json: http status: {response.status_code} - {response.text}")
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
        return ""

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
        data = await self.async_json(lambda r: r.get(self.bridge_url("/list"), timeout=BRIDGE_TIMEOUT))
        result = dict()
        for item in data:
            result[item.get("nukiId")] = item
        return result

    async def bridge_info(self):
        return await self.async_json(lambda r: r.get(self.bridge_url("/info"), timeout=BRIDGE_TIMEOUT))

    async def bridge_reboot(self):
        return await self.async_json(lambda r: r.get(self.bridge_url("/reboot"), timeout=BRIDGE_TIMEOUT))

    async def bridge_fwupdate(self):
        return await self.async_json(lambda r: r.get(self.bridge_url("/fwupdate"), timeout=BRIDGE_TIMEOUT))

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
                ),
                timeout=BRIDGE_TIMEOUT
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
            lambda r: r.get(self.bridge_url("/callback/list"), timeout=BRIDGE_TIMEOUT)
        )
        _LOGGER.debug(f"bridge_remove_callback: {callbacks}, {callback}")
        callbacks_list = callbacks.get("callbacks", [])
        for item in callbacks_list:
            if item["url"] == callback:
                result = await self.async_json(
                    lambda r: r.get(
                        self.bridge_url("/callback/remove", {"id": item["id"]}),
                        timeout=BRIDGE_TIMEOUT
                    )
                )
                if not result.get("success", True):
                    raise HomeAssistantError(result.get("message"))
                return True
        return False

    async def bridge_check_callback(self, callback: str):
        callbacks = await self.async_json(
            lambda r: r.get(self.bridge_url("/callback/list"), timeout=BRIDGE_TIMEOUT)
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
                lambda r: r.get(self.bridge_url("/callback/add", {"url": callback_url}), timeout=BRIDGE_TIMEOUT)
            )
            if not result.get("success", True):
                raise HomeAssistantError(result.get("message"))
        _LOGGER.debug("Callback is set - re-added")
        callbacks = await self.async_json(
            lambda r: r.get(self.bridge_url("/callback/list"), timeout=BRIDGE_TIMEOUT)
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

    async def web_get_last_log(self, dev_id: str):
        lock_actions_map = {
            1: "unlock",
            2: "lock",
            3: "unlatch",
            4: "lock_n_go",
            5: "lock_n_go_unlatch",
        }
        device_actions_map = {
            0: lock_actions_map,
            2: {
                1: "activate_rto",
                2: "deactivate_rto",
                3: "electric_strike_actuation",
                6: "activate_continuous_mode",
                7: "deactivate_continuous_mode",
            },
            3: lock_actions_map,
            4: lock_actions_map,
        }
        device_actions_map[4] = device_actions_map[0]
        response = await self.web_async_json(
            lambda r, h: r.get(self.web_url(f"/smartlock/{dev_id}/log"), headers=h)
        )
        _LOGGER.debug(f"web_get_last_log ({dev_id}): {response}")
        for item in response:
            actions_map = device_actions_map.get(item.get("deviceType"), 0)
            if item.get("action") in actions_map.keys():
                return {
                    "name": item.get("name"),
                    "action": actions_map[item["action"]],
                    "timestamp": item["date"].replace("Z", "+00:00"),
                }
        return dict()

    async def web_get_last_unlock_log(self, dev_id: str):
        actions_map = {
            1: "unlock",
            3: "unlatch",
            5: "lock_n_go_unlatch",
        }
        response = await self.web_async_json(
            lambda r, h: r.get(self.web_url(f"/smartlock/{dev_id}/log"), headers=h)
        )
        _LOGGER.debug(f"web_get_last_unlock_log ({dev_id}): {response}")
        for item in response:
            if item.get("action") in actions_map.keys():
                # unlock, unlatch, lock'n'go with unlatch
                return {
                    "name": item.get("name"),
                    "action": actions_map[item["action"]],
                    "timestamp": item["date"].replace("Z", "+00:00"),
                }
        return dict()

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
        lock_state_map = {
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
        }
        device_state_map = {
            0: lock_state_map,
            2: {
                0: "untrained",
                1: "online",
                3: "ring to open active",
                5: "open",
                7: "opening",
                253: "boot run",
                255: "undefined",
            },
            3: lock_state_map,
            4: lock_state_map,
        }
        resp = await self.web_async_json(
            lambda r, h: r.get(self.web_url(f"/smartlock"), headers=h)
        )
        result = dict()
        for item in resp:
            if item.get("type") not in (0, 2, 4):
                continue
            state = item.get("state", {})
            result[item.get("smartlockId")] = {
                "deviceType": item.get("type"),
                "nukiId": item.get("smartlockId"),
                "web": True,
                "name": item.get("name"),
                "firmwareVersion": str(item.get("firmwareVersion")),
                "config": item.get("config"),
                "advancedConfig": item.get("advancedConfig"),
                "openerAdvancedConfig": item.get("openerAdvancedConfig"),
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
        return result

    async def web_update_auth(self, dev_id: str, auth_id: str, changes: dict):
        await self.web_async_json(
            lambda r, h: r.post(
                self.web_url(f"/smartlock/{dev_id}/auth/{auth_id}"),
                headers=h,
                json=changes,
            )
        )

    async def web_update_config(self, dev_id: str, name: str, changes: dict):
        mapping = {"config": "/config", "advancedConfig": "/advanced/config", "openerAdvancedConfig": "/advanced/openerconfig"}
        await self.web_async_json(
            lambda r, h: r.post(
                self.web_url(f"/smartlock/{dev_id}" + mapping[name]),
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

        """Turn off ring_action binary sensor after 5 seconds"""
        if update.get("ringactionState", False) == True:
            async def _schedule_callback(_now):
                last_state["ringactionState"] = False
                self.async_set_updated_data(data)
            async_call_later(self.hass, 5, _schedule_callback)    

    async def _update(self):
        try:
            callbacks_list = None
            bridge_info = None
            info_mapping = dict()
            device_list = None
            web_list = None
            def web_id_for_item(item):
                if item.get("web"):
                    return item["nukiId"] # Already in web mode
                as_hex = "{0:x}".format(item["nukiId"])
                deviceType = item.get("deviceType", 0)
                if deviceType == 2:
                    as_hex = f"2{as_hex}"
                elif deviceType == 3:
                    as_hex = f"3{as_hex}"
                elif deviceType == 4:
                    as_hex = f"4{as_hex}"
                return int(as_hex, 16)
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
            if self.api.can_web():
                try:
                    web_list = await self.api.web_list()
                except HomeAssistantError:
                    _LOGGER.warning("Despite being configured, Web API request has failed")
                    _LOGGER.exception("Error while fetching list of devices via web API:")
                if not device_list:
                    device_list = web_list
            result = dict(devices={}, bridge_info=bridge_info)
            if not device_list:
                raise HomeAssistantError("No available device data")
            for key, item in device_list.items():
                dev_id = item["nukiId"]
                if self.api.can_web():
                    web_id = web_id_for_item(item)
                    item["webId"] = web_id
                    try:
                        item["web_auth"] = await self.api.web_list_all_auths(web_id)
                    except HomeAssistantError as err:
                        _LOGGER.warning("Despite being configured, Web API request has failed")
                        _LOGGER.exception(f"Error while fetching auth: {err}")
                        item["web_auth"] = self.device_data(dev_id).get("web_auth", {})
                    try:
                        item["last_unlock_log"] = await self.api.web_get_last_unlock_log(web_id)
                    except HomeAssistantError as err:
                        _LOGGER.warning("Despite being configured, Web API request has failed")
                        _LOGGER.exception(f"Error while fetching last unlock log entry: {err}")
                        item["last_unlock_log"] = self.device_data(dev_id).get("last_unlock_log", {})
                    try:
                        item["last_log"] = await self.api.web_get_last_log(web_id)
                    except HomeAssistantError as err:
                        _LOGGER.warning("Despite being configured, Web API request has failed")
                        _LOGGER.exception(f"Error while fetching last log entry: {err}")
                        item["last_log"] = self.device_data(dev_id).get("last_log", {})
                if web_list:
                    item["config"] = web_list.get(web_id, {}).get("config")
                    item["advancedConfig"] = web_list.get(web_id, {}).get("advancedConfig")
                    item["openerAdvancedConfig"] = web_list.get(web_id, {}).get("openerAdvancedConfig")
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
            await self.api.web_lock_action(self.web_id(dev_id), action)
            await self.async_request_refresh()
            _LOGGER.debug(f"web action result: {action}")

    async def do_reboot(self):
        if self.api.can_bridge():
            await self.api.bridge_reboot()
        else:
            raise HomeAssistantError("Not supported")

    async def do_fwupdate(self):
        if self.api.can_bridge():
            await self.api.bridge_fwupdate()
        else:
            raise HomeAssistantError("Not supported")

    async def do_delete_callback(self, callback):
        if self.api.can_bridge():
            await self.api.bridge_remove_callback(callback)
        else:
            raise HomeAssistantError("Not supported")

    def device_data(self, dev_id: str):
        return self.data.get("devices", {}).get(dev_id, {})

    def web_id(self, dev_id: str):
        return self.device_data(dev_id).get("webId", dev_id)

    def info_data(self):
        return self.data.get("info", {})

    def is_lock(self, dev_id: str) -> bool:
        return self.device_data(dev_id).get("deviceType") in (0, 3, 4)

    def is_opener(self, dev_id: str) -> bool:
        return self.device_data(dev_id).get("deviceType") == 2

    def device_supports(self, dev_id: str, feature: str) -> bool:
        return self.device_data(dev_id).get("lastKnownState", {}).get(feature) != None

    def info_field(self, dev_id: str, default, *args):
        data = self.device_data(dev_id)
        for field in args:
            data = data.get(field)
            if data == None:
                return default
        return default if data == None else data

    async def update_web_auth(self, dev_id: str, auth: dict, changes: dict):
        if "id" not in auth:
            raise UpdateFailed("Invalid auth entry")
        await self.api.web_update_auth(self.web_id(dev_id), auth["id"], changes)
        data = self.data
        for key in changes:
            data.get(dev_id, {}).get("web_auth", {}).get(auth["id"], {})[key] = changes[
                key
            ]
        self.async_set_updated_data(data)
    
    async def update_config(self, dev_id: str, name: str, changes: dict):
        data = self.data
        obj = data["devices"].get(dev_id, {}).get(name)
        for key in changes:
            obj[key] = changes[key]
        _LOGGER.debug(f"Updating config: {name}: {changes} = {obj}")
        await self.api.web_update_config(self.web_id(dev_id), name, obj)
        self.async_set_updated_data(data)
