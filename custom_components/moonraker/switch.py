"""Switch platform for Moonraker integration."""
from dataclasses import dataclass

from homeassistant.components.switch import (SwitchEntity,
                                             SwitchEntityDescription)

from .const import DOMAIN, METHODS, OBJ
from .entity import BaseMoonrakerEntity


@dataclass
class MoonrakerSwitchSensorDescription(SwitchEntityDescription):
    """Class describing Mookraker binary_sensor entities."""

    sensor_name: str | None = None
    icon: str | None = None
    subscriptions: list | None = None


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the switch platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    await async_setup_power_device(coordinator, entry, async_add_devices)
    await async_setup_output_pin(coordinator, entry, async_add_devices)


async def _power_device_updater(coordinator):
    return {
        "power_devices": await coordinator.async_fetch_data(
            METHODS.MACHINE_DEVICE_POWER_DEVICES
        )
    }


async def async_setup_output_pin(coordinator, entry, async_add_entities):
    """Set optional binary sensor platform."""

    object_list = await coordinator.async_fetch_data(METHODS.PRINTER_OBJECTS_LIST)

    query_obj = {OBJ: {"configfile": ["settings"]}}
    settings = await coordinator.async_fetch_data(
        METHODS.PRINTER_OBJECTS_QUERY, query_obj, quiet=True
    )

    switches = []
    for obj in object_list["objects"]:
        if "output_pin" not in obj:
            continue

        if settings["status"]["configfile"]["settings"][obj.lower()]["pwm"]:
            continue

        desc = MoonrakerSwitchSensorDescription(
            key=obj,
            sensor_name=obj,
            name=obj.replace("_", " ").title(),
            icon="mdi:switch",
            subscriptions=[(obj, "value")],
        )
        switches.append(desc)

    coordinator.load_sensor_data(switches)
    await coordinator.async_refresh()
    async_add_entities(
        [MoonrakerDigitalOutputPin(coordinator, entry, desc) for desc in switches]
    )


async def async_setup_power_device(coordinator, entry, async_add_entities):
    """Set optional binary sensor platform."""

    power_devices = await coordinator.async_fetch_data(
        METHODS.MACHINE_DEVICE_POWER_DEVICES
    )
    if power_devices.get("error"):
        return

    coordinator.add_data_updater(_power_device_updater)

    sensors = []
    for device in power_devices["devices"]:
        desc = MoonrakerSwitchSensorDescription(
            key=device["device"],
            sensor_name=device["device"],
            name=device["device"].replace("_", " ").title(),
            icon="mdi:power",
            subscriptions=[],
        )
        sensors.append(desc)

    coordinator.load_sensor_data(sensors)
    await coordinator.async_refresh()
    async_add_entities(
        [MoonrakerPowerDeviceSwitchSensor(coordinator, entry, desc) for desc in sensors]
    )


class MoonrakerSwitchSensor(BaseMoonrakerEntity, SwitchEntity):
    """Moonraker switch class."""

    def __init__(
        self,
        coordinator,
        entry,
        description,
    ) -> None:
        """Initialize the switch class."""
        super().__init__(coordinator, entry)
        self.entity_description = description
        self.sensor_name = description.sensor_name
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_has_entity_name = True
        self._attr_icon = description.icon


class MoonrakerPowerDeviceSwitchSensor(MoonrakerSwitchSensor):
    """Moonraker power device switch class."""

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        for device in self.coordinator.data["power_devices"]["devices"]:
            if device["device"] == self.sensor_name:
                return device["status"] == "on"

    async def async_turn_on(self, **_: any) -> None:
        """Turn on the switch."""
        await self.coordinator.async_send_data(
            METHODS.MACHINE_DEVICE_POWER_POST_DEVICE,
            {"device": self.sensor_name, "action": "on"},
        )
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **_: any) -> None:
        """Turn off the switch."""
        await self.coordinator.async_send_data(
            METHODS.MACHINE_DEVICE_POWER_POST_DEVICE,
            {"device": self.sensor_name, "action": "off"},
        )
        await self.coordinator.async_refresh()


class MoonrakerDigitalOutputPin(MoonrakerSwitchSensor):
    """Moonraker power device switch class."""

    def __init__(self, coordinator, entry, description) -> None:
        """Init."""
        super().__init__(coordinator, entry, description)
        self.pin = description.sensor_name.replace("output_pin ", "")

    @property
    def is_on(self) -> bool:
        """Return true if the switch is on."""
        return self.coordinator.data["status"][self.sensor_name]["value"] == 1

    async def async_turn_on(self, **_: any) -> None:
        """Turn on the switch."""
        await self.coordinator.async_send_data(
            METHODS.PRINTER_GCODE_SCRIPT,
            {"script": f"SET_PIN PIN={self.pin} VALUE=1"},
        )
        await self.coordinator.async_refresh()

    async def async_turn_off(self, **_: any) -> None:
        """Turn off the switch."""
        await self.coordinator.async_send_data(
            METHODS.PRINTER_GCODE_SCRIPT,
            {"script": f"SET_PIN PIN={self.pin} VALUE=0"},
        )
        await self.coordinator.async_refresh()
