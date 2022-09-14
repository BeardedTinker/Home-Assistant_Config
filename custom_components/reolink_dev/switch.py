"""This component provides support many for Reolink IP cameras switches."""
import asyncio
import logging

from homeassistant.core import HomeAssistant
from homeassistant.components.switch import DEVICE_CLASS_SWITCH
from homeassistant.helpers.entity import ToggleEntity, EntityCategory

from .const import BASE, DOMAIN
from .entity import ReolinkEntity

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, config_entry, async_add_devices):
    """Set up the Reolink IP Camera switches."""
    devices = []
    base = hass.data[DOMAIN][config_entry.entry_id][BASE]

    for capability in await base.api.get_switch_capabilities():
        if capability == "ftp":
            devices.append(FTPSwitch(hass, config_entry))
        elif capability == "email":
            devices.append(EmailSwitch(hass, config_entry))
        elif capability == "audio":
            devices.append(AudioSwitch(hass, config_entry))
        elif capability == "irLights":
            devices.append(IRLightsSwitch(hass, config_entry))
        elif capability == "spotlight":
            devices.append(SpotLightSwitch(hass, config_entry))
        elif capability == "siren":
            devices.append(SirenSwitch(hass, config_entry))
        elif capability == "push":
            devices.append(PushSwitch(hass, config_entry))
        elif capability == "recording":
            devices.append(RecordingSwitch(hass, config_entry))
        else:
            continue

    async_add_devices(devices, update_before_add=False)


class FTPSwitch(ReolinkEntity, ToggleEntity):
    """An implementation of a Reolink IP camera FTP switch."""

    def __init__(self, hass, config):
        """Initialize a Reolink camera."""
        ReolinkEntity.__init__(self, hass, config)
        ToggleEntity.__init__(self)

    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"reolink_ftpSwitch_{self._base.unique_id}"

    @property
    def name(self):
        """Return the name of this camera."""
        return f"{self._base.name} FTP"

    @property
    def is_on(self):
        """Camera Motion FTP upload Status."""
        return self._base.api.ftp_state

    @property
    def device_class(self):
        """Device class of the switch."""
        return DEVICE_CLASS_SWITCH

    @property
    def icon(self):
        """Icon of the switch."""
        if self.is_on:
            return "mdi:folder-upload"

        return "mdi:folder-remove"

    async def async_turn_on(self, **kwargs):
        """Enable motion ftp recording."""
        await self._base.api.set_ftp(True)
        await self.request_refresh()

    async def async_turn_off(self, **kwargs):
        """Disable motion ftp recording."""
        await self._base.api.set_ftp(False)
        await self.request_refresh()


class EmailSwitch(ReolinkEntity, ToggleEntity):
    """An implementation of a Reolink IP camera email switch."""

    def __init__(self, hass, config):
        """Initialize a Reolink camera."""
        ReolinkEntity.__init__(self, hass, config)
        ToggleEntity.__init__(self)

    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"reolink_emailSwitch_{self._base.unique_id}"

    @property
    def name(self):
        """Return the name of this camera."""
        return f"{self._base.name} email"

    @property
    def is_on(self):
        """Camera Motion email upload Status."""
        return self._base.api.email_state

    @property
    def device_class(self):
        """Device class of the switch."""
        return DEVICE_CLASS_SWITCH

    @property
    def icon(self):
        """Icon of the switch."""
        if self.is_on:
            return "mdi:email"

        return "mdi:email-outline"

    async def async_turn_on(self, **kwargs):
        """Enable motion email notification."""
        await self._base.api.set_email(True)
        await self.request_refresh()

    async def async_turn_off(self, **kwargs):
        """Disable motion email notification."""
        await self._base.api.set_email(False)
        await self.request_refresh()


class IRLightsSwitch(ReolinkEntity, ToggleEntity):
    """An implementation of a Reolink IP camera ir lights switch."""

    def __init__(self, hass, config):
        """Initialize a Reolink camera."""
        ReolinkEntity.__init__(self, hass, config)
        ToggleEntity.__init__(self)
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"reolink_irLightsSwitch_{self._base.unique_id}"

    @property
    def name(self):
        """Return the name of this camera."""
        return f"{self._base.name} IR lights"

    @property
    def is_on(self):
        """Camera Motion ir lights Status."""
        return self._base.api.ir_state

    @property
    def device_class(self):
        """Device class of the switch."""
        return DEVICE_CLASS_SWITCH

    @property
    def icon(self):
        """Icon of the switch."""
        if self.is_on:
            return "mdi:flashlight"

        return "mdi:flashlight-off"

    async def async_turn_on(self, **kwargs):
        """Enable motion ir lights."""
        await self._base.api.set_ir_lights(True)
        await self.request_refresh()

    async def async_turn_off(self, **kwargs):
        """Disable motion ir lights."""
        await self._base.api.set_ir_lights(False)
        await self.request_refresh()


class SpotLightSwitch(ReolinkEntity, ToggleEntity):
    """An implementation of a Reolink IP camera spotlight (WhiteLed) switch"""

    

    def __init__(self, hass, config):
        """Initialize a Reolink camera."""
        ReolinkEntity.__init__(self, hass, config)
        ToggleEntity.__init__(self)
        self._slstatus = False
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"reolink_SpotlightSwitch_{self._base.unique_id}"

    @property
    def name(self):
        """Return the name of this camera."""
        return f"{self._base.name} Spotlight"

    @property
    def is_on(self):
        """Camera Motion Spotlight Status."""
        # return self._base.api.whiteled_state
        return self._slstatus

    @property
    def device_class(self):
        """Device class of the switch."""
        return DEVICE_CLASS_SWITCH

    @property
    def icon(self):
        """Icon of the switch."""
        if self.is_on:
            return "mdi:lightbulb-spot"
        else: 
            return "mdi:lightbulb-spot-off"

    async def async_turn_on(self, **kwargs):
        """Enable spotlight."""
        # uses call to simple turn on routine
        # which sets night mode on, auto, 100% bright
        
        await self._base.api.set_spotlight(True)
        self._slstatus = True
        await self.request_refresh()

    async def async_turn_off(self, **kwargs):
        """Disable spotlight."""
        await self._base.api.set_spotlight(False)
        self._slstatus = False
        await self.request_refresh()    

    async def set_schedule(self,**kwargs):
        # to set the schedule for when night mode on and auto off
        # requires a start and end time in hours and minutes
        # if not provided will default to start 18:00, end 06:00
        #
        # if being set will cause night mode and non-auto to be set
        #
        _starthour = 18
        _startmin = 0
        _endhour = 6
        _endmin = 0

        for key, value in kwargs.items():
            if key == "starthour":
                _starthour = value
            elif key == "startmin":
                _startmin = value
            elif key == "endhour":
                _endhour = value
            elif key == "endmin":
                _endmin = value

        await self._base.api.set_spotlight_lighting_schedule(_endhour, _endmin, _starthour, _startmin )
        await self.request_refresh()


class SirenSwitch(ReolinkEntity, ToggleEntity):
    """An implementation of a Reolink IP camera spotlight (WhiteLed) switch"""

    def __init__(self, hass, config):
        """Initialize a Reolink camera."""
        ReolinkEntity.__init__(self, hass, config)
        ToggleEntity.__init__(self)
        self._sistatus = False
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"reolink_SirenSwitch_{self._base.unique_id}"

    @property
    def name(self):
        """Return the name of this camera."""
        return f"{self._base.name} Siren"

    @property
    def is_on(self):
        """Camera Motion Siren Status."""
        # return self._base.api.audio_alarm_state
        return self._sistatus

    @property
    def device_class(self):
        """Device class of the switch."""
        return DEVICE_CLASS_SWITCH

    @property
    def icon(self):
        """Icon of the switch."""
        if self.is_on:
            return "mdi:alarm"
        else: 
            return "mdi:alarm-off"

    async def async_turn_on(self, **kwargs):
        """Turn On Siren."""
        # uses call to simple turn on routine
        # which sets night mode on, auto, 100% bright
        
        await self._base.api.set_siren(True)
        self._sistatus = True
        await self.request_refresh()

    async def async_turn_off(self, **kwargs):
        """Turn Off Siren."""
        await self._base.api.set_siren(False)
        self._sistatus = False
        await self.request_refresh()


class PushSwitch(ReolinkEntity, ToggleEntity):
    """An implementation of a Reolink IP camera push switch."""

    def __init__(self, hass, config):
        """Initialize a Reolink camera."""
        ReolinkEntity.__init__(self, hass, config)
        ToggleEntity.__init__(self)
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"reolink_pushSwitch_{self._base.unique_id}"

    @property
    def name(self):
        """Return the name of this camera."""
        return f"{self._base.name} push notifications"

    @property
    def is_on(self):
        """Camera push notification Status."""
        return self._base.api.push_state

    @property
    def device_class(self):
        """Device class of the switch."""
        return DEVICE_CLASS_SWITCH

    @property
    def icon(self):
        """Icon of the switch."""
        if self.is_on:
            return "mdi:message"

        return "mdi:message-off"

    async def async_turn_on(self, **kwargs):
        """Enable push notifications."""
        await self._base.api.set_push(True)
        await self.request_refresh()

    async def async_turn_off(self, **kwargs):
        """Disable push notifications."""
        await self._base.api.set_push(False)
        await self.request_refresh()

class RecordingSwitch(ReolinkEntity, ToggleEntity):
    """An implementation of a Reolink IP camera recording switch."""

    def __init__(self, hass, config):
        """Initialize a Reolink camera."""
        ReolinkEntity.__init__(self, hass, config)
        ToggleEntity.__init__(self)
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"reolink_recordingSwitch_{self._base.unique_id}"

    @property
    def name(self):
        """Return the name of this camera."""
        return f"{self._base.name} recording"

    @property
    def is_on(self):
        """Camera recording upload Status."""
        return self._base.api.recording_state

    @property
    def device_class(self):
        """Device class of the switch."""
        return DEVICE_CLASS_SWITCH

    @property
    def icon(self):
        """Icon of the switch."""
        if self.is_on:
            return "mdi:filmstrip"

        return "mdi:filmstrip-off"

    async def async_turn_on(self, **kwargs):
        """Enable recording."""
        await self._base.api.set_recording(True)
        await self.request_refresh()

    async def async_turn_off(self, **kwargs):
        """Disable recording."""
        await self._base.api.set_recording(False)
        await self.request_refresh()


class AudioSwitch(ReolinkEntity, ToggleEntity):
    """An implementation of a Reolink IP camera audio switch."""

    def __init__(self, hass, config):
        """Initialize a Reolink camera."""
        ReolinkEntity.__init__(self, hass, config)
        ToggleEntity.__init__(self)
        self._attr_entity_category = EntityCategory.CONFIG

    @property
    def unique_id(self):
        """Return Unique ID string."""
        return f"reolink_audioSwitch_{self._base.unique_id}"

    @property
    def name(self):
        """Return the name of this camera."""
        return f"{self._base.name} record audio"

    @property
    def is_on(self):
        """Camera audio switch Status."""
        return self._base.api.audio_state

    @property
    def device_class(self):
        """Device class of the switch."""
        return DEVICE_CLASS_SWITCH

    @property
    def icon(self):
        """Icon of the switch."""
        if self.is_on:
            return "mdi:volume-high"

        return "mdi:volume-off"

    async def async_turn_on(self, **kwargs):
        """Enable audio recording."""
        await self._base.api.set_audio(True)
        await self.request_refresh()

    async def async_turn_off(self, **kwargs):
        """Disable audio recording."""
        await self._base.api.set_audio(False)
        await self.request_refresh()
