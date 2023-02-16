"""This component provides support for Reolink motion events."""
import asyncio
import datetime
import logging
import traceback

from homeassistant.core import HomeAssistant, Event
from homeassistant.components.binary_sensor import BinarySensorEntity

from .entity import ReolinkEntity, CoordinatorEntity
from .const import BASE, DOMAIN, MOTION_UPDATE_COORDINATOR
from .base import ReolinkBase

_LOGGER = logging.getLogger(__name__)

DEFAULT_DEVICE_CLASS = "motion"


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_devices):
    """Set up the Reolink IP Camera switches."""

    base: ReolinkBase = hass.data[DOMAIN][config_entry.entry_id][BASE]

    base.sensor_motion_detection = MotionSensor(hass, config_entry)

    new_sensors = [base.sensor_motion_detection]

    if base.api.is_ia_enabled:
        _LOGGER.debug("Camera '{}' model '{}' is AI enabled so object detection sensors will be created".
                      format(base.name, base.api.model))
        base.sensor_person_detection = ObjectDetectedSensor(hass, config_entry, "person")
        base.sensor_vehicle_detection = ObjectDetectedSensor(hass, config_entry, "vehicle")
        base.sensor_pet_detection = ObjectDetectedSensor(hass, config_entry, "pet")

        new_sensors.append(base.sensor_person_detection)
        new_sensors.append(base.sensor_vehicle_detection)
        new_sensors.append(base.sensor_pet_detection)

    async_add_devices(new_sensors, update_before_add=False)


class MotionSensor(ReolinkEntity, BinarySensorEntity):
    """An implementation of a Reolink IP camera motion sensor."""

    def __init__(self, hass, config):
        """Initialize a the switch."""
        ReolinkEntity.__init__(self, hass, config)
        BinarySensorEntity.__init__(self)
        CoordinatorEntity.__init__(self, hass.data[DOMAIN][config.entry_id][MOTION_UPDATE_COORDINATOR])

        self._available = False
        self._event_state = False
        self._last_event_state = False
        self._last_motion = datetime.datetime.min

    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"reolink_motion_{self._base.unique_id}"

    @property
    def name(self):
        """Return the name of this camera."""
        return f"{self._base.name} motion"

    @property
    def is_on(self):
        """Return the state of the sensor."""
        if not self._base.motion_detection_state:
            self._state = False
            return self._state

        if self._event_state or self._base.motion_off_delay == 0:
            self._state = self._event_state
            return self._state

        if (
            datetime.datetime.now() - self._last_motion
        ).total_seconds() < self._base.motion_off_delay:
            self._state = True
        else:           
            self._state = False

        return self._state

    @property
    def available(self):
        # in case detection solely relies on callback, availability relies on active session state
        if self._base.motion_states_update_fallback_delay is None or self._base.motion_states_update_fallback_delay <= 0:
            return self._base.api.session_active
        return self._available

    @property
    def device_class(self):
        """Return the class of this device."""
        return DEFAULT_DEVICE_CLASS

    async def async_added_to_hass(self) -> None:
        """Entity created."""
        await super().async_added_to_hass()
        self.hass.bus.async_listen(self._base.event_id, self.handle_event)

    async def handle_event(self, event):
        """Handle incoming event for motion detection and availability."""

        try:
            self._available = event.data["available"]
        except KeyError:
            pass

        if not self._available:
            if self._base.sensor_person_detection is not None and self._base.sensor_person_detection.available:
                await self._base.sensor_person_detection.handle_event(
                    Event(self._base.event_id, {"available": False}))
            if self._base.sensor_vehicle_detection is not None and self._base.sensor_vehicle_detection.available:
                await self._base.sensor_vehicle_detection.handle_event(
                    Event(self._base.event_id, {"available": False}))
            if self._base.sensor_pet_detection is not None and self._base.sensor_pet_detection.available:
                await self._base.sensor_pet_detection.handle_event(
                    Event(self._base.event_id, {"available": False}))
            return

        try:
            self._last_event_state = bool(self._event_state)
            self._event_state = event.data["motion"]
        except KeyError:
            return

        try:
            await self._base.api.get_all_motion_states()
            self._event_state = self._base.api.motion_state
        except:
            _LOGGER.error("Motion states could not be queried from API")
            _LOGGER.error(traceback.format_exc())
            self._available = False
            if self._base.sensor_person_detection is not None:
                await self._base.sensor_person_detection.handle_event(
                    Event(self._base.event_id, {"available": False}))
            if self._base.sensor_vehicle_detection is not None:
                await self._base.sensor_vehicle_detection.handle_event(
                    Event(self._base.event_id, {"available": False}))
            if self._base.sensor_pet_detection is not None:
                await self._base.sensor_pet_detection.handle_event(
                    Event(self._base.event_id, {"available": False}))
            self.async_schedule_update_ha_state()
            return

        if not self._available:
            self._available = True
            self.async_schedule_update_ha_state()

        if self._event_state:
            self._last_motion = datetime.datetime.now()
        else:
            if self._base.motion_off_delay > 0:
                await asyncio.sleep(self._base.motion_off_delay)

        if self._base.api.ai_state:
            # send an event to AI based motion sensor entities
            if self._base.sensor_person_detection is not None:
                await self._base.sensor_person_detection.handle_event(
                    Event(self._base.event_id, {"ai_refreshed": True, "available": True}))
            if self._base.sensor_vehicle_detection is not None:
                await self._base.sensor_vehicle_detection.handle_event(
                    Event(self._base.event_id, {"ai_refreshed": True, "available": True}))
            if self._base.sensor_pet_detection is not None:
                await self._base.sensor_pet_detection.handle_event(
                    Event(self._base.event_id, {"ai_refreshed": True, "available": True}))

        if self.enabled:
            self.async_schedule_update_ha_state()

    @property
    def extra_state_attributes(self):
        """Return the state attributes."""
        attrs = super().extra_state_attributes

        if attrs is None:
            attrs = {}

        attrs["bus_event_id"] = self._base.event_id

        if self._base.api.ai_state:
            for key, value in self._base.api.ai_state.items():
                if key == "channel":
                    continue

                if self._state:
                    if isinstance(value, int):  # compatibility with firmware < 3.0.0-494
                        attrs[key] = value == 1
                    else:
                        # from firmware 3.0.0.0-494 there is a new json structure:
                        # [
                        #     {
                        #         "cmd" : "GetAiState",
                        #         "code" : 0,
                        #         "value" : {
                        #             "channel" : 0,
                        #             "face" : {
                        #                 "alarm_state" : 0,
                        #                 "support" : 0
                        #             },
                        #             "people" : {
                        #                 "alarm_state" : 0,
                        #                 "support" : 1
                        #             },
                        #             "vehicle" : {
                        #                 "alarm_state" : 0,
                        #                 "support" : 1
                        #             }
                        #         }
                        #     }
                        # ]
                        attrs[key] = value.get("alarm_state", 0) == 1
                else:
                    # Reset the AI values.
                    attrs[key] = False

        return attrs

    async def request_refresh(self):
        """Call the coordinator to update the API."""
        await self.coordinator.async_request_refresh()


class ObjectDetectedSensor(ReolinkEntity, BinarySensorEntity):
    """An implementation of a Reolink IP camera object motion sensor."""

    def __init__(self, hass, config, object_type: str):
        """Initialize a the switch."""
        ReolinkEntity.__init__(self, hass, config)
        BinarySensorEntity.__init__(self)

        self._available = False
        self._event_state = False
        self._last_event_state = False
        self._last_motion = datetime.datetime.min
        self._object_type = object_type

    @property
    def icon(self):
        """Icon of the sensor."""

        if self._object_type == "pet":
            if self._state:
                return "mdi:dog-side"
            else:
                return "mdi:dog-side-off"
        if self._object_type == "vehicle":
            if self._state:
                return "mdi:car"
            else:
                return "mdi:car-off"

        if self._state:
            return "mdi:motion-sensor"
        return "mdi:motion-sensor-off"

    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"reolink_object_{self._object_type}_detected_{self._base.unique_id}"

    @property
    def name(self):
        """Return the name of this sensor."""
        return f"{self._base.name} {self._object_type} detected"

    @property
    def is_on(self):
        """Return the state of the sensor."""
        self._state = self._event_state
        return self._state

    @property
    def available(self):
        """Return True if entity is available."""
        if self._base.motion_states_update_fallback_delay is None or self._base.motion_states_update_fallback_delay <= 0:
            return self._base.api.ai_state and self._base.api.session_active
        return self._available

    @property
    def device_class(self):
        """Return the class of this device."""
        return DEFAULT_DEVICE_CLASS

    async def async_added_to_hass(self) -> None:
        """Entity created."""
        await super().async_added_to_hass()
        self.hass.bus.async_listen(self._base.event_id, self.handle_event)

    async def handle_event(self, event):
        """Handle incoming event for motion detection and availability."""

        new_availability = self._available

        try:
            new_availability = event.data["available"]
            if not new_availability:
                if new_availability != self._available:
                    self._available = new_availability
                    self.async_schedule_update_ha_state()
                return
        except KeyError:
            pass

        if event.data.get("smtp") is self._object_type:
            self._event_state = True
            if self.enabled:
                self.async_schedule_update_ha_state()

        if event.data.get("ai_refreshed") is not True:
            return

        self._last_event_state = bool(self._event_state)
        self._event_state = False

        if self._base.api.ai_state:
            object_found = False
            for key, value in self._base.api.ai_state.items():
                if key == "channel":
                    continue

                if key == self._object_type or (self._object_type == 'person' and key == 'people'):
                    if isinstance(value, int):  # compatibility with firmware < 3.0.0-494
                        self._event_state = value == 1
                    else:
                        self._event_state = value.get('alarm_state', 0) == 1
                        self._available = value.get('support', 0) == 1

                    if self.enabled:
                        self.async_schedule_update_ha_state()
                    object_found = True
                    break

            if not object_found:
                new_availability = False

        if new_availability != self._available:
            self._available = new_availability
            self.async_schedule_update_ha_state()










