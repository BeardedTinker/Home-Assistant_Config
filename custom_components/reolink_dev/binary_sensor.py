"""This component provides support for Reolink motion events."""
import asyncio
import datetime

from homeassistant.components.binary_sensor import BinarySensorEntity

from .entity import ReolinkEntity

DEFAULT_DEVICE_CLASS = "motion"


async def async_setup_entry(hass, config_entry, async_add_devices):
    """Set up the Reolink IP Camera switches."""
    sensor = MotionSensor(hass, config_entry)
    async_add_devices([sensor], update_before_add=False)


class MotionSensor(ReolinkEntity, BinarySensorEntity):
    """An implementation of a Reolink IP camera motion sensor."""

    def __init__(self, hass, config):
        """Initialize a the switch."""
        ReolinkEntity.__init__(self, hass, config)
        BinarySensorEntity.__init__(self)

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
        """Return True if entity is available."""
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
            return
        except KeyError:
            pass

        if not self._available:
            return

        try:
            self._last_event_state = bool(self._event_state)
            self._event_state = event.data["motion"]
        except KeyError:
            return

        if self._base.api.channels > 1:
            # Pull the motion state for the NVR channel, it has only 1 event
            self._event_state = await self._base.api.get_motion_state()

        if self._event_state:
            self._last_motion = datetime.datetime.now()

            if self._base.api.ai_state:
                # Pull the AI state only at motion detection
                await self._base.api.get_ai_state()
        else:
            if self._base.motion_off_delay > 0:
                await asyncio.sleep(self._base.motion_off_delay)

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
                    attrs[key] = value == 1
                else:
                    # Reset the AI values.
                    attrs[key] = False
		
        return attrs
