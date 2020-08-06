"""The blitzortung integration."""
import asyncio
import json
import logging
import math
import time

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import const
from .const import (
    CONF_RADIUS,
    DOMAIN,
    PLATFORMS,
    DEFAULT_RADIUS,
    CONF_IDLE_RESET_TIMEOUT,
    DEFAULT_IDLE_RESET_TIMEOUT,
    DEFAULT_UPDATE_INTERVAL,
)
from .geohash_utils import geohash_overlap
from .mqtt import MQTT, MQTT_CONNECTED, MQTT_DISCONNECTED
from .version import __version__

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.Schema({vol.Optional(const.SERVER_STATS, default=False): bool})},
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: dict):
    """Initialize basic config of blitzortung component."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN]["config"] = config.get(DOMAIN) or {}
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Set up blitzortung from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    config = hass.data[DOMAIN].get("config") or {}

    latitude = config_entry.options.get(CONF_LATITUDE, hass.config.latitude)
    longitude = config_entry.options.get(CONF_LONGITUDE, hass.config.longitude)
    radius = config_entry.options.get(CONF_RADIUS, DEFAULT_RADIUS)
    idle_reset_seconds = config_entry.options.get(
        CONF_IDLE_RESET_TIMEOUT, DEFAULT_IDLE_RESET_TIMEOUT
    ) * 60

    coordinator = BlitzortungDataUpdateCoordinator(
        hass,
        latitude,
        longitude,
        radius,
        idle_reset_seconds,
        DEFAULT_UPDATE_INTERVAL,
        server_stats=config.get(const.SERVER_STATS),
    )

    hass.data[DOMAIN][config_entry.entry_id] = coordinator

    async def start_platforms():
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_setup(config_entry, component)
                for component in PLATFORMS
            ]
        )
        await coordinator.connect()

    hass.async_create_task(start_platforms())

    if not config_entry.update_listeners:
        config_entry.add_update_listener(async_update_options)

    return True


async def async_update_options(hass, config_entry):
    """Update options."""
    _LOGGER.info("async_update_options")
    await hass.config_entries.async_reload(config_entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry):
    """Unload a config entry."""
    coordinator = hass.data[DOMAIN].pop(config_entry.entry_id)
    await coordinator.disconnect()
    _LOGGER.info("disconnected")

    # cleanup platforms
    unload_ok = all(
        await asyncio.gather(
            *[
                hass.config_entries.async_forward_entry_unload(config_entry, component)
                for component in PLATFORMS
            ]
        )
    )
    return unload_ok


async def async_migrate_entry(hass, entry):
    _LOGGER.debug("Migrating Blitzortung entry from Version %s", entry.version)
    if entry.version == 1:
        latitude = entry.data[CONF_LATITUDE]
        longitude = entry.data[CONF_LONGITUDE]
        radius = entry.data[CONF_RADIUS]
        name = entry.data[CONF_NAME]

        entry.unique_id = f"{latitude}-{longitude}-{name}-lightning"
        entry.data = {CONF_NAME: name}
        entry.options = {
            CONF_LATITUDE: latitude,
            CONF_LONGITUDE: longitude,
            CONF_RADIUS: radius,
        }
        entry.version = 2
    if entry.version == 2:
        entry.options = dict(entry.options)
        entry.options[CONF_IDLE_RESET_TIMEOUT] = DEFAULT_IDLE_RESET_TIMEOUT
        entry.version = 3
    return True


class BlitzortungDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(
        self,
        hass,
        latitude,
        longitude,
        radius,
        idle_reset_seconds,
        update_interval,
        server_stats=False,
    ):
        """Initialize."""
        self.hass = hass
        self.latitude = latitude
        self.longitude = longitude
        self.radius = radius
        self.idle_reset_seconds = idle_reset_seconds
        self.server_stats = server_stats
        self.last_time = 0
        self.sensors = []
        self.callbacks = []
        self.geohash_overlap = geohash_overlap(
            self.latitude, self.longitude, self.radius
        )
        self._disconnect_callbacks = []
        self.unloading = False

        _LOGGER.info(
            "lat: %s, lon: %s, radius: %skm, geohashes: %s",
            self.latitude,
            self.longitude,
            self.radius,
            self.geohash_overlap,
        )

        self.mqtt_client = MQTT(hass, "blitzortung.ha.sed.pl", 1883,)

        self._disconnect_callbacks.append(
            async_dispatcher_connect(
                self.hass, MQTT_CONNECTED, self._on_connection_change
            )
        )
        self._disconnect_callbacks.append(
            async_dispatcher_connect(
                self.hass, MQTT_DISCONNECTED, self._on_connection_change
            )
        )

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
            update_method=self._do_update,
        )

    def _on_connection_change(self, *args, **kwargs):
        if self.unloading:
            return
        for sensor in self.sensors:
            sensor.async_write_ha_state()

    def compute_polar_coords(self, lightning):
        dy = (lightning["lat"] - self.latitude) * math.pi / 180
        dx = (
            (lightning["lon"] - self.longitude)
            * math.pi
            / 180
            * math.cos(self.latitude * math.pi / 180)
        )
        distance = round(math.sqrt(dx * dx + dy * dy) * 6371, 1)
        azimuth = round(math.atan2(dx, dy) * 180 / math.pi)

        lightning[const.ATTR_LIGHTNING_DISTANCE] = distance
        lightning[const.ATTR_LIGHTNING_AZIMUTH] = azimuth

    async def connect(self):
        await self.mqtt_client.async_connect()
        _LOGGER.info("Connected to Blitzortung proxy mqtt server")
        for geohash_code in self.geohash_overlap:
            geohash_part = "/".join(geohash_code)
            await self.mqtt_client.async_subscribe(
                "blitzortung/1.1/{}/#".format(geohash_part), self.on_mqtt_message, qos=0
            )
        if self.server_stats:
            await self.mqtt_client.async_subscribe(
                "$SYS/broker/#", self.on_mqtt_message, qos=0
            )
        await self.mqtt_client.async_subscribe(
            "component/hello", self.on_hello_message, qos=0
        )
        self._disconnect_callbacks.append(self.async_add_listener(lambda: None))

    async def disconnect(self):
        self.unloading = True
        await self.mqtt_client.async_disconnect()
        for cb in self._disconnect_callbacks:
            cb()

    def on_hello_message(self, message, *args):
        def parse_version(version_str):
            return tuple(map(int, version_str.split(".")))

        data = json.loads(message.payload)
        latest_version_str = data.get("latest_version")
        if latest_version_str:
            default_message = (
                f"New version {latest_version_str} is available. "
                f"[Check it out](https://github.com/mrk-its/homeassistant-blitzortung)"
            )
            latest_version_message = data.get("latest_version_message", default_message)
            latest_version_title = data.get("latest_version_title", "Blitzortung")
            latest_version = parse_version(latest_version_str)
            current_version = parse_version(__version__)
            if latest_version > current_version:
                _LOGGER.info("new version is available: %s", latest_version_str)
                self.hass.components.persistent_notification.async_create(
                    title=latest_version_title,
                    message=latest_version_message,
                    notification_id="blitzortung_new_version_available",
                )

    def on_mqtt_message(self, message, *args):
        for callback in self.callbacks:
            callback(message)
        if message.topic.startswith("blitzortung/1.1"):
            lightning = json.loads(message.payload)
            self.compute_polar_coords(lightning)
            if lightning[const.ATTR_LIGHTNING_DISTANCE] < self.radius:
                _LOGGER.debug("ligntning data: %s", lightning)
                self.last_time = time.time()
                for sensor in self.sensors:
                    sensor.update_lightning(lightning)

    def register_sensor(self, sensor):
        self.sensors.append(sensor)

    def register_message_receiver(self, message_cb):
        self.callbacks.append(message_cb)

    @property
    def is_inactive(self):
        return bool(
            self.idle_reset_seconds
            and (time.time() - self.last_time) >= self.idle_reset_seconds
        )

    @property
    def is_connected(self):
        return self.mqtt_client.connected

    async def _do_update(self):
        for sensor in self.sensors:
            sensor.tick()
