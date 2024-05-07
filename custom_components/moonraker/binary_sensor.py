"""Binary sensors platform for Moonraker integration."""
from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)

from .const import DOMAIN, METHODS
from .entity import BaseMoonrakerEntity


@dataclass
class MoonrakerBinarySensorDescription(BinarySensorEntityDescription):
    """Class describing Mookraker binary_sensor entities."""

    is_on_fn: Callable | None = None
    sensor_name: str | None = None
    subscriptions: list | None = None
    icon: str | None = None


async def async_setup_entry(hass, entry, async_add_devices):
    """Set up the binary_sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    await async_setup_optional_binary_sensors(coordinator, entry, async_add_devices)
    await async_setup_update_binary_sensors(coordinator, entry, async_add_devices)


async def async_setup_optional_binary_sensors(coordinator, entry, async_add_entities):
    """Set optional binary sensor platform."""

    sensors = []
    object_list = await coordinator.async_fetch_data(METHODS.PRINTER_OBJECTS_LIST)
    for obj in object_list["objects"]:
        split_obj = obj.split()

        if split_obj[0] in ["filament_switch_sensor", "filament_motion_sensor"]:
            desc = MoonrakerBinarySensorDescription(
                key=f"{split_obj[0]}_{split_obj[1]}",
                sensor_name=obj,
                is_on_fn=lambda sensor: sensor.coordinator.data["status"][
                    sensor.sensor_name
                ]["filament_detected"],
                name=split_obj[1].replace("_", " ").title(),
                subscriptions=[(obj, "filament_detected")],
                icon="mdi:printer-3d-nozzle-alert",
                device_class=BinarySensorDeviceClass.OCCUPANCY,
            )
            sensors.append(desc)

    coordinator.load_sensor_data(sensors)
    await coordinator.async_refresh()
    async_add_entities(
        [MoonrakerBinarySensor(coordinator, entry, desc) for desc in sensors]
    )


async def async_setup_update_binary_sensors(coordinator, entry, async_add_entities):
    """Set Machine Update binary sensor."""

    desc = MoonrakerBinarySensorDescription(
        key="update_available",
        sensor_name="update_available",
        is_on_fn=update_available_fn,
        name="Update Available",
        subscriptions=[("status", "update_available")],
        icon="mdi:update",
        device_class=BinarySensorDeviceClass.UPDATE,
        entity_registry_enabled_default=False,
    )

    coordinator.load_sensor_data([desc])
    await coordinator.async_refresh()
    async_add_entities([MoonrakerBinarySensor(coordinator, entry, desc)])


def update_available_fn(sensor):
    """Return if update is available."""
    if "machine_update" not in sensor.coordinator.data:
        return False

    for component in sensor.coordinator.data["machine_update"]["version_info"]:
        if component == "system":
            if (
                sensor.coordinator.data["machine_update"]["version_info"][component][
                    "package_count"
                ]
                > 0
            ):
                return True
            continue

        if (
            sensor.coordinator.data["machine_update"]["version_info"][component][
                "remote_version"
            ]
            != sensor.coordinator.data["machine_update"]["version_info"][component][
                "version"
            ]
        ):
            return True

    return False


class MoonrakerBinarySensor(BaseMoonrakerEntity, BinarySensorEntity):
    """Moonraker binary_sensor class."""

    def __init__(
        self,
        coordinator,
        entry,
        description,
    ) -> None:
        """Initialize the binary_sensor class."""
        super().__init__(coordinator, entry)
        self.entity_description = description
        self.is_on_fn = description.is_on_fn
        self.sensor_name = description.sensor_name
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_has_entity_name = True
        self._attr_native_value = description.is_on_fn(self)
        self._attr_icon = description.icon

    @property
    def is_on(self) -> bool:
        """Return state."""
        return self.is_on_fn(self)
