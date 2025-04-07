"""Light platform for Moonraker integration."""

import logging
from dataclasses import dataclass

from homeassistant.components.light import (
    LightEntity,
    LightEntityDescription,
    ColorMode,
)
from homeassistant.core import callback
from homeassistant.util import color

from .const import DOMAIN, METHODS, OBJ
from .entity import BaseMoonrakerEntity


@dataclass
class MoonrakerLightSensorDescription(LightEntityDescription):
    """Class describing Mookraker light entities."""

    color_mode: ColorMode | None = None
    sensor_name: str | None = None
    icon: str | None = None
    subscriptions: list | None = None


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the light platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    await async_setup_light(coordinator, entry, async_add_devices)


async def async_setup_light(coordinator, entry, async_add_entities):
    """Set optional light platform."""

    object_list = await coordinator.async_fetch_data(METHODS.PRINTER_OBJECTS_LIST)

    query_obj = {OBJ: {"configfile": ["settings"]}}
    settings = await coordinator.async_fetch_data(
        METHODS.PRINTER_OBJECTS_QUERY, query_obj, quiet=True
    )

    lights = []
    for obj in object_list["objects"]:
        if (
            not obj.startswith("led ")
            and not obj.startswith("neopixel ")
            and not obj.startswith("dotstar ")
            and not obj.startswith("pca9533 ")
            and not obj.startswith("pca9632 ")
        ):
            continue

        led_type = obj.split()[0]
        color_mode = ColorMode.UNKNOWN
        conf = settings["status"]["configfile"]["settings"][obj.lower()]

        if led_type == "led":
            num_led_pins = 0
            for pin in ["red_pin", "green_pin", "blue_pin", "white_pin"]:
                if pin in conf:
                    num_led_pins += 1

            if num_led_pins == 0:
                continue
            elif num_led_pins == 1:
                color_mode = ColorMode.BRIGHTNESS
            elif num_led_pins == 4 or "white_pin" in conf:
                color_mode = ColorMode.RGBW
            elif "red_pin" in conf and "green_pin" in conf and "blue_pin" in conf:
                color_mode = ColorMode.RGB
        elif led_type == "neopixel" or led_type == "pca9632":
            if "color_order" in conf and "W" in conf["color_order"]:
                color_mode = ColorMode.RGBW
            else:
                color_mode = ColorMode.RGB
        elif led_type == "dotstar":
            color_mode = ColorMode.RGB
        elif led_type == "pca9533":
            color_mode = ColorMode.RGBW

        desc = MoonrakerLightSensorDescription(
            key=obj,
            sensor_name=obj,
            name=obj.replace("_", " ").title(),
            icon="mdi:led-variant-on",
            subscriptions=[(obj, "color_data")],
            color_mode=color_mode,
        )
        lights.append(desc)

    coordinator.load_sensor_data(lights)
    await coordinator.async_refresh()
    async_add_entities([MoonrakerLED(coordinator, entry, desc) for desc in lights])


_LOGGER = logging.getLogger(__name__)


class MoonrakerLED(BaseMoonrakerEntity, LightEntity):
    """Moonraker LED class."""

    def __init__(
        self,
        coordinator,
        entry,
        description,
    ) -> None:
        """Initialize the switch class."""
        super().__init__(coordinator, entry)
        self.led_name = " ".join(description.sensor_name.split()[1:])
        self.entity_description = description
        self.sensor_name = description.sensor_name
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_has_entity_name = True
        self._attr_icon = description.icon
        self._attr_color_mode = description.color_mode
        self._attr_supported_color_modes = {description.color_mode}
        self._set_attributes_from_coordinator()

    async def async_turn_on(
        self,
        brightness: int = None,
        color_temp: int = None,
        rgb_color=None,
        **kwargs,
    ) -> None:
        """Turn on the light."""
        if rgb_color:
            await self._set_rgbw(*rgb_color, 0)
        else:
            if brightness is None or not self._attr_is_on:
                brightness = 255
                self._attr_is_on = True
                await self._set_rgbw(brightness, brightness, brightness, brightness)
            elif self._attr_is_on:
                color_data = self.coordinator.data["status"][self.sensor_name][
                    "color_data"
                ][0]
                multiplier = brightness / (
                    max(color_data[0], color_data[1], color_data[2], color_data[3])
                    * 255
                )
                await self._set_rgbw(
                    (color_data[0] * 255 * multiplier),
                    (color_data[1] * 255 * multiplier),
                    (color_data[2] * 255 * multiplier),
                    (color_data[3] * 255 * multiplier),
                )

    async def async_turn_off(self, **kwargs) -> None:
        """Turn off the light."""
        self._attr_is_on = False
        await self._set_rgbw(0, 0, 0, 0)

    async def _set_rgbw(self, r: int, g: int, b: int, w: int) -> None:
        """Update HA attributes."""
        self._attr_rgb_color = (r, g, b)
        self._attr_rgbw_color = (r, g, b, w)
        self._attr_brightness = max(r, g, b, w)
        """Set native Value."""
        f_r = round(color.brightness_to_value((1, 100), r) / 100, 2)
        f_g = round(color.brightness_to_value((1, 100), g) / 100, 2)
        f_b = round(color.brightness_to_value((1, 100), b) / 100, 2)
        f_w = round(color.brightness_to_value((1, 100), w) / 100, 2)
        await self.coordinator.async_send_data(
            METHODS.PRINTER_GCODE_SCRIPT,
            {
                "script": f'SET_LED LED="{self.led_name}" RED={f_r} GREEN={f_g} BLUE={f_b} WHITE={f_w} SYNC=0 TRANSMIT=1'
            },
        )
        self._attr_rgbw_color = (r, g, b, w)
        self.async_write_ha_state()

    def _set_attributes_from_coordinator(self) -> None:
        color_data = self.coordinator.data["status"][self.sensor_name]["color_data"][0]
        if color_data[0] != 0:
            r = color.value_to_brightness((1, 100), color_data[0] * 100)
        else:
            r = 0
        if color_data[1] != 0:
            g = color.value_to_brightness((1, 100), color_data[1] * 100)
        else:
            g = 0
        if color_data[2] != 0:
            b = color.value_to_brightness((1, 100), color_data[2] * 100)
        else:
            b = 0
        if color_data[3] != 0:
            w = color.value_to_brightness((1, 100), color_data[3] * 100)
        else:
            w = 0
        self._set_attributes(r, g, b, w)

    def _set_attributes(self, r: int, g: int, b: int, w: int) -> None:
        self._attr_is_on = r > 0 or g > 0 or b > 0 or w > 0
        self._attr_brightness = max(r, g, b, w)
        self._attr_rgb_color = (r, g, b)
        self._attr_rgbw_color = (r, g, b, w)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._set_attributes_from_coordinator()
        self.async_write_ha_state()
