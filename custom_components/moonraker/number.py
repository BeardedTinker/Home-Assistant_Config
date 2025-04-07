"""Number platform for Moonraker integration."""

import logging
from dataclasses import dataclass

from homeassistant.components.number import (
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.core import callback
from homeassistant.const import UnitOfTemperature

from .const import DOMAIN, METHODS, OBJ
from .entity import BaseMoonrakerEntity


@dataclass
class MoonrakerNumberSensorDescription(NumberEntityDescription):
    """Class describing Mookraker number entities."""

    sensor_name: str | None = None
    icon: str | None = None
    subscriptions: list | None = None
    icon: str | None = None
    unit: str | None = None
    update_code: str | None = None
    max_value: int | None = None


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the number platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    await async_setup_output_pin(coordinator, entry, async_add_devices)
    await async_setup_temperature_target(coordinator, entry, async_add_devices)


async def async_setup_temperature_target(coordinator, entry, async_add_entities):
    """Set optional temp target."""

    sensors = []

    object_list = await coordinator.async_fetch_data(METHODS.PRINTER_OBJECTS_LIST)
    for obj in object_list["objects"]:
        if obj.startswith("heater_bed"):
            desc = MoonrakerNumberSensorDescription(
                key=f"{obj}_target",
                sensor_name=obj,
                name="Bed Target".title(),
                subscriptions=[(obj, "target")],
                icon="mdi:radiator",
                unit=UnitOfTemperature.CELSIUS,
                update_code="M140 S",
                max_value=130,
            )
            sensors.append(desc)

        elif obj.startswith("extruder"):
            extruder_val = "0" if obj == "extruder" else obj[-1]

            desc = MoonrakerNumberSensorDescription(
                key=f"{obj}_target",
                sensor_name=obj,
                name=f"{obj} Target".title(),
                subscriptions=[(obj, "target")],
                icon="mdi:printer-3d-nozzle-heat",
                unit=UnitOfTemperature.CELSIUS,
                update_code=f"M104 T{extruder_val} S",
                max_value=260,
            )
            sensors.append(desc)

    coordinator.load_sensor_data(sensors)
    await coordinator.async_refresh()
    async_add_entities(
        [MoonrakerTempTarget(coordinator, entry, desc) for desc in sensors]
    )


async def async_setup_output_pin(coordinator, entry, async_add_entities):
    """Set optional binary sensor platform."""

    object_list = await coordinator.async_fetch_data(METHODS.PRINTER_OBJECTS_LIST)

    query_obj = {OBJ: {"configfile": ["settings"]}}
    settings = await coordinator.async_fetch_data(
        METHODS.PRINTER_OBJECTS_QUERY, query_obj, quiet=True
    )

    numbers = []
    for obj in object_list["objects"]:
        if "output_pin" not in obj:
            continue

        if not settings["status"]["configfile"]["settings"][obj.lower()]["pwm"]:
            continue

        desc = MoonrakerNumberSensorDescription(
            key=obj,
            sensor_name=obj,
            name=obj.replace("_", " ").title(),
            icon="mdi:switch",
            subscriptions=[(obj, "value")],
        )
        numbers.append(desc)

    coordinator.load_sensor_data(numbers)
    await coordinator.async_refresh()
    async_add_entities(
        [MoonrakerPWMOutputPin(coordinator, entry, desc) for desc in numbers]
    )


_LOGGER = logging.getLogger(__name__)


class MoonrakerPWMOutputPin(BaseMoonrakerEntity, NumberEntity):
    """Moonraker PWM output pin class."""

    def __init__(
        self,
        coordinator,
        entry,
        description,
    ) -> None:
        """Initialize the switch class."""
        super().__init__(coordinator, entry)
        self.pin = description.sensor_name.replace("output_pin ", "")
        self._attr_mode = NumberMode.SLIDER
        self._attr_native_value = (
            coordinator.data["status"][description.sensor_name]["value"] * 100
        )
        self.entity_description = description
        self.sensor_name = description.sensor_name
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_has_entity_name = True
        self._attr_icon = description.icon

    async def async_set_native_value(self, value: float) -> None:
        """Set native Value."""
        await self.coordinator.async_send_data(
            METHODS.PRINTER_GCODE_SCRIPT,
            {"script": f"SET_PIN PIN={self.pin} VALUE={round(value / 100, 2)}"},
        )
        self._attr_native_value = value
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = (
            self.coordinator.data["status"][self.sensor_name]["value"] * 100
        )
        self.async_write_ha_state()


class MoonrakerTempTarget(BaseMoonrakerEntity, NumberEntity):
    """Moonraker temp target class."""

    def __init__(
        self,
        coordinator,
        entry,
        description,
    ) -> None:
        """Initialize the temp target class."""
        super().__init__(coordinator, entry)
        self._attr_mode = NumberMode.SLIDER
        self._attr_native_value = coordinator.data["status"][description.sensor_name][
            "target"
        ]
        self.entity_description = description
        self.sensor_name = description.sensor_name
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_native_max_value = description.max_value
        self._attr_has_entity_name = True
        self._attr_icon = description.icon
        self.update_string = description.update_code

    async def async_set_native_value(self, value: float) -> None:
        """Set native Value."""
        await self.coordinator.async_send_data(
            METHODS.PRINTER_GCODE_SCRIPT,
            {"script": f"{self.update_string}{value}"},
        )
        self._attr_native_value = value
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.coordinator.data["status"][self.sensor_name][
            "target"
        ]
        self.async_write_ha_state()
