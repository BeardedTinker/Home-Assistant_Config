import asyncio
from datetime import datetime
from typing import Optional, List, Tuple

from growcube_client import GrowcubeClient, GrowcubeReport, Channel, WateringMode
from growcube_client import (
    WaterStateGrowcubeReport,
    DeviceVersionGrowcubeReport,
    MoistureHumidityStateGrowcubeReport,
    PumpOpenGrowcubeReport,
    PumpCloseGrowcubeReport,
    CheckSensorGrowcubeReport,
    CheckOutletBlockedGrowcubeReport,
    CheckSensorNotConnectedGrowcubeReport,
    LockStateGrowcubeReport,
    CheckOutletLockedGrowcubeReport,
)
from growcube_client import WateringModeCommand, SyncTimeCommand, PlantEndCommand, ClosePumpCommand
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.const import (
    STATE_UNAVAILABLE,
    STATE_OK,
    STATE_PROBLEM,
    STATE_LOCKED,
    STATE_OPEN,
    STATE_CLOSED,
)
import logging

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, CHANNEL_NAME

_LOGGER = logging.getLogger(__name__)


class GrowcubeDataModel:
    def __init__(self, host: str):
        # Device
        self.host: str = host
        self.version: str = ""
        self.device_id: Optional[str] = None
        self.device_info: Optional[DeviceInfo] = None

        # Sensors
        self.temperature: Optional[int] = None
        self.humidity: Optional[int] = None
        self.moisture: List[Optional[int]] = [None, None, None, None]
        self.pump_open: List[bool] = [False, False, False, False]

        # Diagnostics
        self.device_locked: int = False
        self.water_warning: int = False
        self.sensor_abnormal: List[int] = [False, False, False, False]
        self.sensor_disconnected: List[int] = [False, False, False, False]
        self.outlet_blocked_state: List[int] = [False, False, False, False]
        self.outlet_locked_state: List[int] = [False, False, False, False]


class GrowcubeDataCoordinator(DataUpdateCoordinator):
    def __init__(self, host: str, hass: HomeAssistant):
        self.client = GrowcubeClient(
            host, self.handle_report, self.on_connected, self.on_disconnected
        )
        super().__init__(hass, _LOGGER, name=DOMAIN)
        self.entities = []
        self.device_id = None
        self.data: GrowcubeDataModel = GrowcubeDataModel(host)
        self.shutting_down = False

    def set_device_id(self, device_id: str) -> None:
        self.device_id = hex(int(device_id))[2:]
        self.data.device_id = f"growcube_{self.device_id}"
        self.data.device_info = {
            "name": "GrowCube " + self.device_id,
            "identifiers": {(DOMAIN, self.data.device_id)},
            "manufacturer": "Elecrow",
            "model": "Growcube",
            "sw_version": self.data.version,
        }

    async def _async_update_data(self):
        return self.data

    async def connect(self) -> Tuple[bool, str]:
        result, error = await self.client.connect()
        if not result:
            return False, error

        self.shutting_down = False
        # Wait for the device to send back the DeviceVersionGrowcubeReport
        while not self.data.device_id:
            await asyncio.sleep(0.1)
        _LOGGER.debug(
            "Growcube device id: %s",
            self.data.device_id
        )

        time_command = SyncTimeCommand(datetime.now())
        _LOGGER.debug(
            "%s: Sending SyncTimeCommand",
            self.data.device_id
        )
        self.client.send_command(time_command)
        return True, ""

    async def reconnect(self) -> None:
        if self.client.connected:
            await self.client.disconnect()

        if not self.shutting_down:
            while True:
                # Set flag to avoid handling in on_disconnected
                self.shutting_down = True
                result, error = await self.client.connect()
                if result:
                    _LOGGER.debug(
                        "Reconnect to %s succeeded",
                        self.data.host
                    )
                    self.shutting_down = False
                    await asyncio.sleep(10)
                    return

                _LOGGER.debug(
                    "Reconnect failed for %s with error '%s', retrying in 10 seconds",
                    self.data.host,
                    error)
                await asyncio.sleep(10)

    @staticmethod
    async def get_device_id(host: str) -> tuple[bool, str]:
        """This is used in the config flow to check for a valid device"""
        device_id = ""

        def _handle_device_id_report(report: GrowcubeReport):
            if isinstance(report, DeviceVersionGrowcubeReport):
                nonlocal device_id
                device_id = report.device_id

        async def _check_device_id_assigned():
            nonlocal device_id
            while not device_id:
                await asyncio.sleep(0.1)

        client = GrowcubeClient(host, _handle_device_id_report)
        result, error = await client.connect()
        if not result:
            return False, error

        try:
            await asyncio.wait_for(_check_device_id_assigned(), timeout = 5)
            client.disconnect()
        except asyncio.TimeoutError:
            client.disconnect()
            return False, "Timed out waiting for device ID"

        return True, device_id

    def on_connected(self, host: str) -> None:
        _LOGGER.debug(
            "Connection to %s established",
            host
        )

    async def on_disconnected(self, host: str) -> None:
        _LOGGER.debug("Connection to %s lost", host)
        if self.data.device_id is not None:
            self.hass.states.async_set(
                DOMAIN + "." + self.data.device_id, STATE_UNAVAILABLE
            )
            self.reset_sensor_data()
        if not self.shutting_down:
            _LOGGER.debug(
                "Device host %s went offline, will try to reconnect",
                host
            )
            loop = asyncio.get_event_loop()
            loop.call_later(10, lambda: loop.create_task(self.reconnect()))

    def disconnect(self) -> None:
        self.shutting_down = True
        self.client.disconnect()

    def reset_sensor_data(self) -> None:
        self.data.temperature = None
        self.data.humidity = None
        self.data.moisture = [None, None, None, None]
        self.data.pump_open = [False, False, False, False]
        self.data.device_locked = False
        self.data.water_warning = False
        self.data.sensor_abnormal = [False, False, False, False]
        self.data.sensor_disconnected = [False, False, False, False]
        self.data.outlet_blocked_state = [False, False, False, False]
        self.data.outlet_locked_state = [False, False, False, False]

    def handle_report(self, report: GrowcubeReport):
        """Handle a report from the Growcube."""
        # 24 - RepDeviceVersion
        if isinstance(report, DeviceVersionGrowcubeReport):
            _LOGGER.debug(
                "Device device_id: %s, version %s",
                report.device_id,
                report.version
            )
            self.reset_sensor_data()
            self.data.version = report.version
            self.set_device_id(report.device_id)

        # 20 - RepWaterState
        elif isinstance(report, WaterStateGrowcubeReport):
            _LOGGER.debug(
                "%s: Water state %s",
                self.data.device_id,
                report.water_warning
            )
            self.data.water_warning = report.water_warning

        # 21 - RepSTHSate
        elif isinstance(report, MoistureHumidityStateGrowcubeReport):
            _LOGGER.debug(
                "%s: Sensor reading, channel %s, humidity %s, temperature %s, moisture %s",
                self.data.device_id,
                report.channel,
                report.humidity,
                report.temperature,
                report.moisture,
            )
            self.data.humidity = report.humidity
            self.data.temperature = report.temperature
            self.data.moisture[report.channel.value] = report.moisture

        # 26 - RepPumpOpen
        elif isinstance(report, PumpOpenGrowcubeReport):
            _LOGGER.debug(
                "%s: Pump open, channel %s",
                self.data.device_id,
                report.channel
            )
            self.data.pump_open[report.channel.value] = True

        # 27 - RepPumpClose
        elif isinstance(report, PumpCloseGrowcubeReport):
            _LOGGER.debug(
                "%s: Pump closed, channel %s",
                self.data.device_id,
                report.channel
            )
            self.data.pump_open[report.channel.value] = False

        # 28 - RepCheckSenSorNotConnected
        elif isinstance(report, CheckSensorGrowcubeReport):
            _LOGGER.debug(
                "%s: Sensor abnormal, channel %s",
                self.data.device_id,
                report.channel
            )
            self.data.sensor_abnormal[report.channel.value] = True

        # 29 - Pump channel blocked
        elif isinstance(report, CheckOutletBlockedGrowcubeReport):
            _LOGGER.debug(
                "%s: Outlet blocked, channel %s",
                self.data.device_id,
                report.channel
            )
            self.data.outlet_blocked_state[report.channel.value] = True

        # 30 - RepCheckSenSorNotConnect
        elif isinstance(report, CheckSensorNotConnectedGrowcubeReport):
            _LOGGER.debug(
                "%s: Check sensor, channel %s",
                self.data.device_id,
                report.channel
            )
            self.data.sensor_disconnected[report.channel.value] = True

        # 33 - RepLockstate
        elif isinstance(report, LockStateGrowcubeReport):
            _LOGGER.debug(
                f"%s: Lock state, %s",
                self.data.device_id,
                report.lock_state
            )
            # Handle case where the button on the device was pressed, this should do a reconnect
            # to read any problems still present
            if not report.lock_state and self.data.device_locked:
                self.reset_sensor_data()
                self.reconnect()
            self.data.device_locked = report.lock_state

        # 34 - ReqCheckSenSorLock
        elif isinstance(report, CheckOutletLockedGrowcubeReport):
            _LOGGER.debug(
                "%s Check outlet, channel %s",
                self.data.device_id,
                report.channel
            )
            self.data.outlet_locked_state[report.channel.value] = True

    async def water_plant(self, channel: int) -> None:
        await self.client.water_plant(Channel(channel), 5)

    async def handle_water_plant(self, channel: Channel, duration: int) -> None:
        _LOGGER.debug(
            "%s: Service water_plant called, %s, %s",
            self.data.device_id,
            channel,
            duration
        )
        await self.client.water_plant(channel, duration)

    async def handle_set_smart_watering(self, channel: Channel,
                                        all_day: bool,
                                        min_moisture: int,
                                        max_moisture: int) -> None:

        _LOGGER.debug(
            "%s: Service set_smart_watering called, %s, %s, %s, %s",
            self.data.device_id,
            channel,
            all_day,
            min_moisture,
            max_moisture,
        )

        watering_mode = WateringMode.Smart if all_day else WateringMode.SmartOutside
        command = WateringModeCommand(channel, watering_mode, min_moisture, max_moisture)
        self.client.send_command(command)

    async def handle_set_manual_watering(self, channel: Channel, duration: int, interval: int) -> None:

        _LOGGER.debug(
            "%s: Service set_manual_watering called, %s, %s, %s",
            self.data.device_id,
            channel,
            duration,
            interval,
        )

        command = WateringModeCommand(channel, WateringMode.Manual, interval, duration)
        self.client.send_command(command)

    async def handle_delete_watering(self, channel: Channel) -> None:

        _LOGGER.debug(
            "%s: Service delete_watering called, %s,",
            self.data.device_id,
            channel
        )
        command = PlantEndCommand(channel)
        self.client.send_command(command)
        command = ClosePumpCommand(channel)
        self.client.send_command(command)
