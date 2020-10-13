"""
Reolink Camera API
"""
import requests
import datetime
import json
import logging
import aiohttp

_LOGGER = logging.getLogger(__name__)

class ReolinkApi(object):
    def __init__(self, ip, channel):
        self._url = "http://" + ip + "/cgi-bin/api.cgi"
        self._ip = ip
        self._channel = channel
        self._token = None
        self._motion_state = False
        self._last_motion = 0
        self._device_info = None
        self._motion_state = None
        self._ftp_state = None
        self._email_state = None
        self._ir_state = None
        self._recording_state = None
        self._rtspport = None
        self._rtmpport = None
        self._ptzpresets = dict()
        self._motion_detection_state = None

    def session_active(self):
        return self._token is not None

    async def get_settings(self):
        if self._token is None:
            return

        param_channel = {"channel": self._channel}
        body = [{"cmd": "GetDevInfo", "action":1, "param": {"channel": self._channel}},
            {"cmd": "GetNetPort", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetFtp", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetEmail", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetIsp", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetRec", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetPtzPreset", "action": 1, "param": {"channel": self._channel}},
            {"cmd": "GetAlarm","action":1,"param":{"Alarm":{"channel": self._channel ,"type":"md"}}}]
            # the call must be like this:
            #[{"cmd":"GetAlarm","action":1,"param":{"Alarm":{"channel":0,"type":"md"}}}]
            #so we cannot use  param_channel

        param = {"token": self._token}
        response = await self.send(body, param)

        try:
            json_data = json.loads(response)
        except:
            _LOGGER.error(f"Error translating response to json")
            self._token = None
            return

        for data in json_data:
            try:
                if data["cmd"] == "GetDevInfo":
                    self._device_info = data

                elif data["cmd"] == "GetNetPort":
                    self._netport_settings = data
                    self._rtspport = data["value"]["NetPort"]["rtspPort"]
                    self._rtmpport = data["value"]["NetPort"]["rtmpPort"]

                elif data["cmd"] == "GetFtp":
                    self._ftp_settings = data
                    if (data["value"]["Ftp"]["schedule"]["enable"] == 1):
                        self._ftp_state = True
                    else:
                        self._ftp_state = False

                elif data["cmd"] == "GetEmail":
                    self._email_settings = data
                    if (data["value"]["Email"]["schedule"]["enable"] == 1):
                        self._email_state = True
                    else:
                        self._email_state = False

                elif data["cmd"] == "GetIsp":
                    self._ir_settings = data
                    if (data["value"]["Isp"]["dayNight"] == "Auto"):
                        self._ir_state = True
                    else:
                        self._ir_state = False

                elif data["cmd"] == "GetRec":
                    self._recording_settings = data
                    if (data["value"]["Rec"]["schedule"]["enable"] == 1):
                        self._recording_state = True
                    else:
                        self._recording_state = False

                elif data["cmd"] == "GetPtzPreset":
                    self._ptzpresets_settings = data
                    for preset in data["value"]["PtzPreset"]:
                        if int(preset["enable"]) == 1:
                            preset_name = preset["name"]
                            preset_id = int(preset["id"])
                            self._ptzpresets[preset_name] = preset_id
                            _LOGGER.debug(f"Got preset {preset_name} with ID {preset_id}")
                        else:
                            _LOGGER.debug(f"Preset is not enabled: {preset}")

                elif data["cmd"] == "GetAlarm":
                    self._motion_detection_settings = data
                    self._pippo = data
                    if (data["value"]["Alarm"]["enable"] == 1):
                        self._motion_detection_state = True
                    else:
                        self._motion_detection_state = False
            except:
                continue

    async def get_motion_state(self):
        body = [{"cmd": "GetMdState", "action": 0, "param":{"channel":self._channel}}]
        param = {"token": self._token}

        response = await self.send(body, param)

        try:
            json_data = json.loads(response)

            if json_data is None:
                _LOGGER.error(f"Unable to get Motion detection state at IP {self._ip}")
                self._motion_state = False
                return self._motion_state

            if json_data[0]["value"]["state"] == 1:
                self._motion_state = True
                self._last_motion = datetime.datetime.now()
            else:
                self._motion_state = False
        except:
            self._motion_state = False

        return self._motion_state

    @property
    async def still_image(self):
        response = await self.send(None, f"?cmd=Snap&channel={self._channel}&token={self._token}", stream=True)
        if response is None:
            return

        # response.raw.decode_content = True
        return response

    @property
    async def snapshot(self):
        response = await self.send(None, f"?cmd=Snap&channel={self._channel}&token={self._token}", stream=False)
        if response is None:
            return

        return response

    @property
    def motion_state(self):
        return self._motion_state

    @property
    def ftp_state(self):
        return self._ftp_state

    @property
    def email_state(self):
        return self._email_state

    @property
    def ir_state(self):
        return self._ir_state

    @property
    def recording_state(self):
        return self._recording_state

    @property
    def rtmpport(self):
        return self._rtmpport

    @property
    def rtspport(self):
        return self._rtspport

    @property
    def last_motion(self):
        return self._last_motion

    @property
    def ptzpresets(self):
        return self._ptzpresets

    @property
    def motion_detection_state(self):
        """Camera motion detection setting status."""
        return self._motion_detection_state

    async def login(self, username, password):
        body = [{"cmd": "Login", "action": 0, "param": {"User": {"userName": username, "password": password}}}]
        param = {"cmd": "Login", "token": "null"}

        response = await self.send(body, param)

        try:
            json_data = json.loads(response)
        except:
            _LOGGER.error(f"Error translating login response to json")
            return

        if json_data is not None:
            if json_data[0]["code"] == 0:
                self._token = json_data[0]["value"]["Token"]["name"]
                _LOGGER.info(f"Reolink camera logged in at IP {self._ip}")
            else:
                _LOGGER.error(f"Failed to login at IP {self._ip}. No token available")
        else:
            _LOGGER.error(f"Failed to login at IP {self._ip}. Connection error.")

    async def logout(self):
        body = [{"cmd":"Logout","action":0,"param":{}}]
        param = {"cmd": "Logout", "token": self._token}

        await self.send(body, param)

    async def set_ftp(self, enabled):
        await self.get_settings()

        if not self._ftp_settings:
            _LOGGER.error("Error while fetching current FTP settings")
            return

        if enabled == True:
            newValue = 1
        else:
            newValue = 0

        body = [{"cmd":"SetFtp","action":0,"param": self._ftp_settings["value"] }]
        body[0]["param"]["Ftp"]["schedule"]["enable"] = newValue

        response = await self.send(body, {"cmd": "SetFtp", "token": self._token} )
        try:
            json_data = json.loads(response)
            if json_data[0]["value"]["rspCode"] == 200:
                return True
            else:
                return False
        except:
            _LOGGER.error(f"Error translating FTP response to json")
            return False

    async def set_email(self, enabled):
        await self.get_settings()

        if not self._email_settings:
            _LOGGER.error("Error while fetching current email settings")
            return

        if enabled == True:
            newValue = 1
        else:
            newValue = 0

        body = [{"cmd":"SetEmail","action":0,"param": self._email_settings["value"] }]
        body[0]["param"]["Email"]["schedule"]["enable"] = newValue

        response = await self.send(body, {"cmd": "SetEmail", "token": self._token} )
        try:
            json_data = json.loads(response)
            if json_data[0]["value"]["rspCode"] == 200:
                return True
            else:
                return False
        except:
            _LOGGER.error(f"Error translating Email response to json")
            return False

    async def set_ir_lights(self, enabled):
        await self.get_settings()

        if not self._ir_settings:
            _LOGGER.error("Error while fetching current IR light settings")
            return

        if enabled == True:
            newValue = "Auto"
        else:
            newValue = "Color"

        body = [{"cmd":"SetIsp","action":0,"param": self._ir_settings["value"] }]
        body[0]["param"]["Isp"]["dayNight"] = newValue

        response = await self.send(body, {"cmd": "SetIrLights", "token": self._token} )
        try:
            json_data = json.loads(response)
            if json_data[0]["value"]["rspCode"] == 200:
                return True
            else:
                return False
        except requests.exceptions.RequestException:
            _LOGGER.error(f"Error translating IR Lights response to json")
            return False

    async def set_recording(self, enabled):
        await self.get_settings()

        if not self._recording_settings:
            _LOGGER.error("Error while fetching current recording settings")
            return

        if enabled == True:
            newValue = 1
        else:
            newValue = 0

        body = [{"cmd":"SetRec","action":0,"param": self._recording_settings["value"] }]
        body[0]["param"]["Rec"]["schedule"]["enable"] = newValue

        response = await self.send(body, {"cmd": "SetRec", "token": self._token} )
        try:
            json_data = json.loads(response)
            if json_data[0]["value"]["rspCode"] == 200:
                return True
            else:
                return False
        except:
            _LOGGER.error(f"Error translating Recording response to json")
            return False

    async def set_motion_detection(self, enabled):
        await self.get_settings()

        if not self._motion_detection_settings:
            _LOGGER.error("Error while fetching current motion detection settings")
            return

        if enabled == True:
            newValue = 1
        else:
            newValue = 0

        body = [{"cmd":"SetAlarm","action":0,"param": self._motion_detection_settings["value"] }]
        body[0]["param"]["Alarm"]["enable"] = newValue
        response = await self.send(body, {"cmd": "SetAlarm", "token": self._token} )
        try:
            json_data = json.loads(response)
            if json_data[0]["value"]["rspCode"] == 200:
                return True
            else:
                return False
        except:
            _LOGGER.error(f"Error translating Recording response to json")
            return False

    async def send(self, body, param, stream=False):
        if (self._token is None and
            (body is None or body[0]["cmd"] != "Login")):
            _LOGGER.info(f"Reolink camera at IP {self._ip} is not logged in")
            return

        timeout = aiohttp.ClientTimeout(total=10)

        if body is None:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url=self._url, params=param) as response:
                    return await response.read()
        else:
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(url=self._url, json=body, params=param) as response:
                    json_data = await response.text()
                    return json_data

    def clear_token(self):
        self._token = None
