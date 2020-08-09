import logging

from homeassistant.const import ATTR_ATTRIBUTION, CONF_NAME, LENGTH_KILOMETERS
from homeassistant.helpers.entity import Entity

from .const import (
    ATTR_LAT,
    ATTR_LIGHTNING_AZIMUTH,
    ATTR_LIGHTNING_COUNTER,
    ATTR_LIGHTNING_DISTANCE,
    ATTR_LON,
    ATTRIBUTION,
    DOMAIN,
    SERVER_STATS,
)

ATTR_ICON = "icon"
ATTR_LABEL = "label"
ATTR_UNIT = "unit"
ATTR_LIGHTNING_PROPERTY = "lightning_prop"

DEGREE = "°"

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    integration_name = config_entry.data[CONF_NAME]

    coordinator = hass.data[DOMAIN][config_entry.entry_id]

    unique_prefix = config_entry.unique_id

    sensors = [
        klass(coordinator, integration_name, unique_prefix)
        for klass in (DistanceSensor, AzimuthSensor, CounterSensor)
    ]

    async_add_entities(sensors, False)

    config = hass.data[DOMAIN].get("config") or {}
    if config.get(SERVER_STATS):
        server_stat_sensors = {}

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
                sensor = ServerStatSensor(
                    topic, coordinator, integration_name, unique_prefix
                )
                server_stat_sensors[topic] = sensor
                async_add_entities([sensor], False)
            sensor.on_message(topic, message)

        coordinator.register_message_receiver(on_message)


class BlitzortungSensor(Entity):
    """Define a Blitzortung sensor."""

    def __init__(self, coordinator, integration_name, unique_prefix):
        """Initialize."""
        self.coordinator = coordinator
        self._integration_name = integration_name
        self.entity_id = f"sensor.{integration_name}-{self.name}"
        self._unique_id = f"{unique_prefix}-{self.kind}"
        self._device_class = None
        self._state = None
        self._unit_of_measurement = None
        self._attrs = {ATTR_ATTRIBUTION: ATTRIBUTION}

    should_poll = False
    icon = "mdi:flash"
    device_class = None

    @property
    def available(self):
        return self.coordinator.is_connected

    @property
    def label(self):
        return self.kind.capitalize()

    @property
    def name(self):
        """Return the name."""
        return f"Lightning {self.label}"

    @property
    def state(self):
        """Return the state."""
        return self._state

    @property
    def device_state_attributes(self):
        """Return the state attributes."""
        return self._attrs

    @property
    def unique_id(self):
        """Return a unique_id for this entity."""
        return self._unique_id

    async def async_added_to_hass(self):
        """Connect to dispatcher listening for entity data notifications."""
        # self.async_on_remove(self.coordinator.async_add_listener(self._update_sensor))
        self.coordinator.register_sensor(self)

    async def async_update(self):
        await self.coordinator.async_request_refresh()

    @property
    def device_info(self):
        return {
            "name": f"{self._integration_name} Lightning Detector",
            "identifiers": {(DOMAIN, self._integration_name)},
            "model": "Lightning Detector",
            "sw_version": "0.0.1",
            "entry_type": "service",
        }

    def update_lightning(self, lightning):
        pass

    def on_message(self, message):
        pass

    def tick(self):
        pass


class LightningSensor(BlitzortungSensor):
    INITIAL_STATE = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._state = self.INITIAL_STATE

    def tick(self):
        if self._state != self.INITIAL_STATE and self.coordinator.is_inactive:
            self._state = self.INITIAL_STATE
            self.async_write_ha_state()


class DistanceSensor(LightningSensor):
    kind = ATTR_LIGHTNING_DISTANCE
    unit_of_measurement = LENGTH_KILOMETERS

    def update_lightning(self, lightning):
        self._state = lightning["distance"]
        self._attrs[ATTR_LAT] = lightning[ATTR_LAT]
        self._attrs[ATTR_LON] = lightning[ATTR_LON]
        self.async_write_ha_state()


class AzimuthSensor(LightningSensor):
    kind = ATTR_LIGHTNING_AZIMUTH
    unit_of_measurement = DEGREE

    def update_lightning(self, lightning):
        self._state = lightning["azimuth"]
        self._attrs[ATTR_LAT] = lightning[ATTR_LAT]
        self._attrs[ATTR_LON] = lightning[ATTR_LON]
        self.async_write_ha_state()


class CounterSensor(LightningSensor):
    kind = ATTR_LIGHTNING_COUNTER
    unit_of_measurement = "↯"
    INITIAL_STATE = 0

    def update_lightning(self, lightning):
        self._state = self._state + 1
        self.async_write_ha_state()


class ServerStatSensor(BlitzortungSensor):
    def __init__(self, topic, coordinator, integration_name, unique_prefix):
        self._topic = topic

        topic_parts = topic.replace("$SYS/broker/", "").split("/")
        self.kind = "_".join(topic_parts)
        if self.kind.startswith("load"):
            self.data_type = float
        elif self.kind in ("uptime", "version"):
            self.data_type = str
        else:
            self.data_type = int

        if self.kind == "clients_connected":
            self.kind = "server_stats"

        self._name = " ".join(part.capitalize() for part in topic_parts)

        super().__init__(coordinator, integration_name, unique_prefix)

    @property
    def unit_of_measurement(self):
        if self.data_type in (int, float):
            return "." if self.kind == "server_stats" else " "
        else:
            return None

    @classmethod
    def for_topic(cls, topic, coordinator, integration_name, unique_prefix):
        return cls(topic, coordinator, integration_name, unique_prefix)

    def on_message(self, topic, message):
        if topic == self._topic:
            payload = message.payload.decode("utf-8")
            try:
                self._state = self.data_type(payload)
            except ValueError:
                self._state = str(payload)
            if self.hass:
                self.async_write_ha_state()

    @property
    def label(self):
        return self._name

    @property
    def name(self):
        return self._name
