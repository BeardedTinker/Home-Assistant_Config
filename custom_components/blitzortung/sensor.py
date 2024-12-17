"""Blitzortung sensor platform."""

import logging
from dataclasses import dataclass

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
    DOMAIN as SENSOR_PLATFORM,
)
from homeassistant.const import (
    CONF_NAME,
    DEGREE,
    EntityCategory,
    UnitOfLength,
    UnitOfTime,
)
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.typing import UNDEFINED
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from . import BlitzortungConfigEntry
from .const import (
    ATTR_LAT,
    ATTR_LIGHTNING_AZIMUTH,
    ATTR_LIGHTNING_COUNTER,
    ATTR_LIGHTNING_DISTANCE,
    ATTR_LON,
    ATTRIBUTION,
    BLITZORTUNG_CONFIG,
    BLIZORTUNG_URL,
    DOMAIN,
    SERVER_STATS,
    SW_VERSION,
)

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, kw_only=True)
class BlitzortungSensorEntityDescription(SensorEntityDescription):
    """Blitzortun sensor entity description."""

    entity_class: type["BlitzortungSensor"]


class BlitzortungSensor(SensorEntity):
    """Define a Blitzortung sensor."""

    _attr_should_poll = False

    def __init__(self, coordinator, description, integration_name, unique_prefix):
        """Initialize."""
        self.coordinator = coordinator
        self._attr_unique_id = f"{unique_prefix}-{description.key}"
        if description.name is UNDEFINED:
            self._attr_name = f"Server {description.key.replace("_", " ").lower()}"
        self._attr_attribution = ATTRIBUTION
        self._attr_device_info = DeviceInfo(
            name=integration_name,
            identifiers={(DOMAIN, unique_prefix)},
            model="Blitzortung Lightning Detector",
            sw_version=SW_VERSION,
            entry_type=DeviceEntryType.SERVICE,
            configuration_url=BLIZORTUNG_URL.format(
                lat=coordinator.latitude, 
                lon=coordinator.longitude
            ),
        )
        self.entity_description = description

    @property
    def available(self):
        return self.coordinator.is_connected

    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        self.coordinator.register_sensor(self)

    async def async_update(self):
        await self.coordinator.async_request_refresh()

    def update_lightning(self, lightning):
        pass

    def on_message(self, message):
        pass

    def tick(self):
        pass


class LightningSensor(BlitzortungSensor):
    """Define a Blitzortung lightning sensor."""

    INITIAL_STATE: int | None = None

    def __init__(self, *args, **kwargs):
        """Initialize."""
        super().__init__(*args, **kwargs)
        self._attr_native_value = self.INITIAL_STATE

    def tick(self):
        if (
            self._attr_native_value != self.INITIAL_STATE
            and self.coordinator.is_inactive
        ):
            self._attr_native_value = self.INITIAL_STATE
            self.async_write_ha_state()


class DistanceSensor(LightningSensor):
    """Define a Blitzortung distance sensor."""

    def update_lightning(self, lightning):
        """Update the sensor data."""
        self._attr_native_value = lightning[ATTR_LIGHTNING_DISTANCE]
        self._attr_extra_state_attributes = {
            ATTR_LAT: lightning[ATTR_LAT],
            ATTR_LON: lightning[ATTR_LON],
        }
        self.async_write_ha_state()


class AzimuthSensor(LightningSensor):
    """Define a Blitzortung azimuth sensor."""

    def update_lightning(self, lightning):
        """Update the sensor data."""
        self._attr_native_value = lightning[ATTR_LIGHTNING_AZIMUTH]
        self._attr_extra_state_attributes = {
            ATTR_LAT: lightning[ATTR_LAT],
            ATTR_LON: lightning[ATTR_LON],
        }
        self.async_write_ha_state()


class CounterSensor(LightningSensor):
    """Define a Blitzortung counter sensor."""

    INITIAL_STATE = 0

    def update_lightning(self, lightning):
        self._attr_native_value = self._attr_native_value + 1
        self.async_write_ha_state()


class ServerStatSensor(BlitzortungSensor):
    """Define a Blitzortung server stats sensor."""

    def __init__(
        self, topic, coordinator, description, integration_name, unique_prefix
    ):
        """Initialize."""
        self._topic = topic

        topic_parts = topic.split("/")
        self.kind = "_".join(topic_parts)
        if self.kind.startswith("load"):
            self.data_type = float
        elif self.kind == "version":
            self.data_type = str
        else:
            self.data_type = int
        if self.data_type in (int, float):
            self._attr_state_class = SensorStateClass.MEASUREMENT

        super().__init__(coordinator, description, integration_name, unique_prefix)

    @property
    def native_unit_of_measurement(self):
        if self.kind == "uptime":
            return UnitOfTime.SECONDS
        if self.data_type in (int, float):
            return "clients" if self.kind == "clients_connected" else " "
        return None

    def on_message(self, topic, message):
        if topic == self._topic:
            payload = message.payload.decode("utf-8")
            if self.kind == "uptime":
                payload = payload.split(" ")[0]
            try:
                self._attr_native_value = self.data_type(payload)
            except ValueError:
                self._attr_native_value = str(payload)
            if self.hass:
                self.async_write_ha_state()


SENSORS: tuple[BlitzortungSensorEntityDescription, ...] = (
    BlitzortungSensorEntityDescription(
        key=ATTR_LIGHTNING_AZIMUTH,
        name="Lightning azimuth",
        translation_key=ATTR_LIGHTNING_AZIMUTH,
        has_entity_name=True,
        native_unit_of_measurement=DEGREE,
        entity_class=AzimuthSensor,
    ),
    BlitzortungSensorEntityDescription(
        key=ATTR_LIGHTNING_COUNTER,
        name="Lightning counter",
        translation_key=ATTR_LIGHTNING_COUNTER,
        has_entity_name=True,
        native_unit_of_measurement="↯",
        state_class=SensorStateClass.MEASUREMENT,
        entity_class=CounterSensor,
    ),
    BlitzortungSensorEntityDescription(
        key=ATTR_LIGHTNING_DISTANCE,
        name="Lightning distance",
        translation_key=ATTR_LIGHTNING_DISTANCE,
        has_entity_name=True,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        entity_class=DistanceSensor,
    ),
)


async def async_setup_entry(
    hass, config_entry: BlitzortungConfigEntry, async_add_entities
):
    """Add Blitzortung sensor entity from a config_entry."""
    integration_name = config_entry.data[CONF_NAME]

    coordinator = config_entry.runtime_data

    unique_prefix = config_entry.entry_id

    # Migrate old service identifiers to new identifiers
    device_registry = dr.async_get(hass)
    old_ids = (DOMAIN, config_entry.title)
    if device_entry := device_registry.async_get_device(identifiers={old_ids}):
        new_ids = (DOMAIN, unique_prefix)
        _LOGGER.debug(
            "Migrating service %s from old IDs '%s' to new IDs '%s'",
            device_entry.name,
            old_ids,
            new_ids,
        )
        device_registry.async_update_device(device_entry.id, new_identifiers={new_ids})

    # Migrate old unique IDs to new unique IDs
    entity_registry = er.async_get(hass)
    old_unique_id = f"{config_entry.title}-server_stats"
    if entity_id := entity_registry.async_get_entity_id(
        SENSOR_PLATFORM, DOMAIN, old_unique_id
    ):
        new_unique_id = f"{unique_prefix}-clients_connected"
        _LOGGER.debug(
            "Migrating entity %s from old unique ID '%s' to new unique ID '%s'",
            entity_id,
            old_unique_id,
            new_unique_id,
        )
        entity_registry.async_update_entity(entity_id, new_unique_id=new_unique_id)

    for sensor_type in (
        ATTR_LIGHTNING_AZIMUTH,
        ATTR_LIGHTNING_COUNTER,
        ATTR_LIGHTNING_DISTANCE,
        "bytes_received",
        "bytes_sent",
        "clients_connected",
        "heap_current",
        "load_bytes_received_1min",
        "load_bytes_sent_1min",
        "load_connections_1min",
        "load_messages_received_1min",
        "load_messages_sent_1min",
        "load_publish_received_1min",
        "load_publish_sent_1min",
        "load_sockets_1min",
        "messages_received",
        "messages_sent",
        "messages_stored",
        "publish_bytes_received",
        "publish_bytes_sent",
        "publish_messages_received",
        "publish_messages_sent",
        "publish_messages_sent",
        "retained messages_count",
        "store_messages_bytes",
        "store_messages_count",
        "subscriptions_count",
        "uptime",
        "version",
    ):
        old_unique_id = f"{config_entry.title}-{sensor_type}"
        if entity_id := entity_registry.async_get_entity_id(
            SENSOR_PLATFORM, DOMAIN, old_unique_id
        ):
            new_unique_id = f"{unique_prefix}-{sensor_type}"
            _LOGGER.debug(
                "Migrating entity %s from old unique ID '%s' to new unique ID '%s'",
                entity_id,
                old_unique_id,
                new_unique_id,
            )
            entity_registry.async_update_entity(entity_id, new_unique_id=new_unique_id)

    sensors = [
        description.entity_class(
            coordinator, description, integration_name, unique_prefix
        )
        for description in SENSORS
    ]

    async_add_entities(sensors, False)

    config = hass.data[BLITZORTUNG_CONFIG]
    if config.get(SERVER_STATS):
        server_stat_sensors: dict[str, ServerStatSensor] = {}

        def on_message(message):
            if not message.topic.startswith("$SYS/broker/"):
                return
            topic = message.topic.replace("$SYS/broker/", "")
            if topic.startswith("load") and not topic.endswith("/1min"):
                return
            if topic.startswith("clients") and topic != "clients/connected":
                return
            sensor = server_stat_sensors.get(topic)
            if not sensor:
                description = BlitzortungSensorEntityDescription(
                    key=topic.replace("/", "_"),
                    translation_key="server_stats",
                    has_entity_name=False,
                    entity_category=EntityCategory.DIAGNOSTIC,
                    entity_class=ServerStatSensor,
                )
                sensor = description.entity_class(
                    topic, coordinator, description, integration_name, unique_prefix
                )
                server_stat_sensors[topic] = sensor
                async_add_entities([sensor], False)
            sensor.on_message(topic, message)

        coordinator.register_message_receiver(on_message)
