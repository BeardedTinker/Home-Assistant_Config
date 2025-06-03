"""Sensor platform for Moonraker integration."""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    PERCENTAGE,
    UnitOfLength,
    UnitOfPressure,
    UnitOfTemperature,
    UnitOfTime,
    REVOLUTIONS_PER_MINUTE,
)
from homeassistant.core import callback

from .const import OBJ, DOMAIN, METHODS, PRINTERSTATES, PRINTSTATES
from .entity import BaseMoonrakerEntity

_LOGGER = logging.getLogger(__name__)


@dataclass
class MoonrakerSensorDescription(SensorEntityDescription):
    """Class describing Mookraker sensor entities."""

    value_fn: Callable | None = None
    sensor_name: str | None = None
    status_key: str | None = None
    icon: str | None = None
    unit: str | None = None
    device_class: str | None = None
    subscriptions: list | None = None


SENSORS: tuple[MoonrakerSensorDescription, ...] = [
    MoonrakerSensorDescription(
        key="state",
        name="Printer State",
        value_fn=lambda sensor: sensor.coordinator.data["printer.info"]["state"],
        device_class=SensorDeviceClass.ENUM,
        options=PRINTERSTATES.list(),
        subscriptions=[],
    ),
    MoonrakerSensorDescription(
        key="message",
        name="Printer Message",
        value_fn=lambda sensor: sensor.coordinator.data["printer.info"][
            "state_message"
        ],
        subscriptions=[],
    ),
    MoonrakerSensorDescription(
        key="print_state",
        name="Current Print State",
        value_fn=lambda sensor: sensor.coordinator.data["status"]["print_stats"][
            "state"
        ],
        device_class=SensorDeviceClass.ENUM,
        options=PRINTSTATES.list(),
        subscriptions=[("print_stats", "state")],
    ),
    MoonrakerSensorDescription(
        key="print_message",
        name="Current Print Message",
        value_fn=lambda sensor: sensor.coordinator.data["status"]["print_stats"][
            "message"
        ],
        subscriptions=[("print_stats", "message")],
    ),
    MoonrakerSensorDescription(
        key="display_message",
        name="Current Display Message",
        value_fn=lambda sensor: sensor.coordinator.data["status"]["display_status"][
            "message"
        ]
        if sensor.coordinator.data["status"]["display_status"]["message"] is not None
        else "",
        subscriptions=[("display_status", "message")],
    ),
    MoonrakerSensorDescription(
        key="filename",
        name="Filename",
        value_fn=lambda sensor: sensor.empty_result_when_not_printing(
            sensor.coordinator.data["status"]["print_stats"]["filename"]
        ),
        subscriptions=[("print_stats", "filename")],
    ),
    MoonrakerSensorDescription(
        key="print_projected_total_duration",
        name="Print Projected Total Duration",
        value_fn=lambda sensor: sensor.empty_result_when_not_printing(
            round(
                sensor.coordinator.data["status"]["print_stats"]["print_duration"]
                / calculate_pct_job(sensor.coordinator.data)
                if calculate_pct_job(sensor.coordinator.data) != 0
                else 0,
                2,
            )
            / 3600
        ),
        subscriptions=[
            ("print_stats", "total_duration"),
            ("display_status", "progress"),
        ],
        icon="mdi:timer",
        unit=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
    ),
    MoonrakerSensorDescription(
        key="print_time_left",
        name="Print Time Left",
        value_fn=lambda sensor: sensor.empty_result_when_not_printing(
            round(
                (
                    sensor.coordinator.data["status"]["print_stats"]["print_duration"]
                    / calculate_pct_job(sensor.coordinator.data)
                    if calculate_pct_job(sensor.coordinator.data) != 0
                    else 0
                )
                - sensor.coordinator.data["status"]["print_stats"]["print_duration"],
                2,
            )
            / 3600
        ),
        subscriptions=[
            ("print_stats", "print_duration"),
            ("display_status", "progress"),
        ],
        icon="mdi:timer",
        unit=UnitOfTime.HOURS,
        device_class=SensorDeviceClass.DURATION,
    ),
    MoonrakerSensorDescription(
        key="print_eta",
        name="Print ETA",
        value_fn=lambda sensor: calculate_eta(sensor.coordinator.data),
        subscriptions=[
            ("print_stats", "print_duration"),
            ("display_status", "progress"),
        ],
        icon="mdi:timer",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    MoonrakerSensorDescription(
        key="slicer_print_duration_estimate",
        name="Slicer Print Duration Estimate",
        value_fn=lambda sensor: sensor.empty_result_when_not_printing(
            round(
                sensor.coordinator.data["estimated_time"] / 3600,
                2,
            ) if sensor.coordinator.data["estimated_time"] > 0 else 0
        ),
        subscriptions=[],
        icon="mdi:timer",
        device_class=SensorDeviceClass.DURATION,
        unit=UnitOfTime.HOURS,
    ),
    MoonrakerSensorDescription(
        key="slicer_print_time_left_estimate",
        name="Slicer Print Time Left Estimate",
        value_fn=lambda sensor: sensor.empty_result_when_not_printing(
            round(
                (
                    sensor.coordinator.data["estimated_time"]
                    - sensor.coordinator.data["status"]["print_stats"]["print_duration"]
                )
                / 3600,
                2,
            ) if sensor.coordinator.data["estimated_time"] > 0 else 0
        ),
        subscriptions=[("print_stats", "print_duration")],
        icon="mdi:timer",
        device_class=SensorDeviceClass.DURATION,
        unit=UnitOfTime.HOURS,
    ),
    MoonrakerSensorDescription(
        key="print_duration",
        name="Print Duration",
        value_fn=lambda sensor: sensor.empty_result_when_not_printing(
            round(
                sensor.coordinator.data["status"]["print_stats"]["print_duration"] / 60,
                2,
            )
        ),
        subscriptions=[("print_stats", "print_duration")],
        icon="mdi:timer",
        unit=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
    ),
    MoonrakerSensorDescription(
        key="filament_used",
        name="Filament Used",
        value_fn=lambda sensor: sensor.empty_result_when_not_printing(
            round(
                int(sensor.coordinator.data["status"]["print_stats"]["filament_used"])
                * 1.0
                / 1000,
                2,
            )
        ),
        subscriptions=[("print_stats", "filament_used")],
        icon="mdi:tape-measure",
        unit=UnitOfLength.METERS,
    ),
    MoonrakerSensorDescription(
        key="progress",
        name="Progress",
        value_fn=lambda sensor: sensor.empty_result_when_not_printing(
            int(sensor.coordinator.data["status"]["display_status"]["progress"] * 100)
        ),
        subscriptions=[("display_status", "progress")],
        icon="mdi:percent",
        unit=PERCENTAGE,
    ),
    MoonrakerSensorDescription(
        key="total_layer",
        name="Total Layer",
        value_fn=lambda sensor: sensor.empty_result_when_not_printing(
            sensor.coordinator.data["status"]["print_stats"]["info"]["total_layer"]
            if sensor.coordinator.data["status"]["print_stats"]["info"] is not None
            and "total_layer"
            in sensor.coordinator.data["status"]["print_stats"]["info"]
            and sensor.coordinator.data["status"]["print_stats"]["info"]["total_layer"]
            is not None
            and sensor.coordinator.data["status"]["print_stats"]["info"]["total_layer"]
            > 0
            else sensor.coordinator.data["layer_count"]
        ),
        subscriptions=[("print_stats", "info", "total_layer")],
        icon="mdi:layers-triple",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MoonrakerSensorDescription(
        key="current_layer",
        name="Current Layer",
        value_fn=lambda sensor: calculate_current_layer(sensor.coordinator.data),
        subscriptions=[("print_stats", "info", "current_layer")],
        icon="mdi:layers-edit",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MoonrakerSensorDescription(
        key="toolhead_position_x",
        name="Toolhead position X",
        value_fn=lambda sensor: round(
            sensor.coordinator.data["status"]["toolhead"]["position"][0], 2
        ),
        subscriptions=[("toolhead", "position")],
        icon="mdi:axis-x-arrow",
        unit=UnitOfLength.MILLIMETERS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MoonrakerSensorDescription(
        key="toolhead_position_y",
        name="Toolhead position Y",
        value_fn=lambda sensor: round(
            sensor.coordinator.data["status"]["toolhead"]["position"][1], 2
        ),
        subscriptions=[("toolhead", "position")],
        icon="mdi:axis-y-arrow",
        unit=UnitOfLength.MILLIMETERS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MoonrakerSensorDescription(
        key="toolhead_position_z",
        name="Toolhead position Z",
        value_fn=lambda sensor: round(
            sensor.coordinator.data["status"]["toolhead"]["position"][2], 2
        ),
        subscriptions=[("toolhead", "position")],
        icon="mdi:axis-z-arrow",
        unit=UnitOfLength.MILLIMETERS,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MoonrakerSensorDescription(
        key="object_height",
        name="Object Height",
        value_fn=lambda sensor: sensor.empty_result_when_not_printing(
            sensor.coordinator.data["object_height"]
        ),
        subscriptions=[],
        icon="mdi:axis-z-arrow",
        device_class=SensorDeviceClass.DISTANCE,
        unit=UnitOfLength.MILLIMETERS,
    ),
    MoonrakerSensorDescription(
        key="sysload",
        name="System Load",
        value_fn=lambda sensor: round(
            sensor.coordinator.data["status"]["system_stats"]["sysload"], 2
        ),
        subscriptions=[("system_stats", "sysload")],
        icon="mdi:cpu-64-bit",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    MoonrakerSensorDescription(
        key="memused",
        name="Memory Used",
        value_fn=lambda sensor: calculate_memory_used(sensor.coordinator.data) or 0.0,
        subscriptions=[("system_stats", "memavail")],
        icon="mdi:memory",
        state_class=SensorStateClass.MEASUREMENT,
        unit=PERCENTAGE,
    ),
]


async def async_setup_entry(hass, entry, async_add_entities):
    """Set sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    await async_setup_basic_sensor(coordinator, entry, async_add_entities)
    await async_setup_optional_sensors(coordinator, entry, async_add_entities)
    await async_setup_history_sensors(coordinator, entry, async_add_entities)
    await async_setup_machine_update_sensors(coordinator, entry, async_add_entities)
    await async_setup_queue_sensors(coordinator, entry, async_add_entities)


async def _machine_system_info_updater(coordinator):
    return {
        "system_info": (
            await coordinator.async_fetch_data(METHODS.MACHINE_SYSTEM_INFO)
        )["system_info"]
    }


async def async_setup_basic_sensor(coordinator, entry, async_add_entities):
    """Set basic sensor platform."""
    coordinator.add_data_updater(_machine_system_info_updater)
    coordinator.load_sensor_data(SENSORS)
    async_add_entities([MoonrakerSensor(coordinator, entry, desc) for desc in SENSORS])


async def async_setup_optional_sensors(coordinator, entry, async_add_entities):
    """Set optional sensor platform."""

    temperature_keys = [
        "temperature_sensor",
        "temperature_fan",
        "temperature_probe",
        "tmc2240",
        "bme280",
        "htu21d",
        "lm75",
    ]

    fan_keys = ["heater_fan", "controller_fan", "fan_generic"]

    sensors = []
    object_list = await coordinator.async_fetch_data(METHODS.PRINTER_OBJECTS_LIST)
    for obj in object_list["objects"]:
        split_obj = obj.split()

        if split_obj[0] in temperature_keys:
            desc = MoonrakerSensorDescription(
                key=f"{split_obj[0]}_{split_obj[1]}",
                status_key=obj,
                name=split_obj[1].removesuffix("_temp").replace("_", " ").title()
                + " Temp",
                value_fn=lambda sensor: (
                    round(
                        sensor.coordinator.data["status"][sensor.status_key][
                            "temperature"
                        ],
                        2,
                    )
                    if sensor.coordinator.data["status"][sensor.status_key][
                        "temperature"
                    ]
                    is not None
                    else None
                ),
                subscriptions=[(obj, "temperature")],
                icon="mdi:thermometer",
                unit=UnitOfTemperature.CELSIUS,
                state_class=SensorStateClass.MEASUREMENT,
            )
            sensors.append(desc)

            if split_obj[0] == "bme280":
                query_obj = {OBJ: {obj: None}}
                result = await coordinator.async_fetch_data(
                    METHODS.PRINTER_OBJECTS_QUERY, query_obj, quiet=True
                )

                if "pressure" in result["status"][obj]:
                    desc = MoonrakerSensorDescription(
                        key=f"{split_obj[0]}_{split_obj[1]}_pressure",
                        status_key=obj,
                        name=split_obj[1].replace("_", " ").title() + " Pressure",
                        value_fn=lambda sensor: sensor.coordinator.data["status"][
                            sensor.status_key
                        ]["pressure"],
                        subscriptions=[(obj, "pressure")],
                        icon="mdi:gauge",
                        unit=UnitOfPressure.HPA,
                        state_class=SensorStateClass.MEASUREMENT,
                    )
                    sensors.append(desc)

                if "humidity" in result["status"][obj]:
                    desc = MoonrakerSensorDescription(
                        key=f"{split_obj[0]}_{split_obj[1]}_humidity",
                        status_key=obj,
                        name=split_obj[1].replace("_", " ").title() + " Humidity",
                        value_fn=lambda sensor: sensor.coordinator.data["status"][
                            sensor.status_key
                        ]["humidity"],
                        subscriptions=[(obj, "humidity")],
                        icon="mdi:water-percent",
                        unit=PERCENTAGE,
                        state_class=SensorStateClass.MEASUREMENT,
                    )
                    sensors.append(desc)

                if "gas" in result["status"][obj]:
                    desc = MoonrakerSensorDescription(
                        key=f"{split_obj[0]}_{split_obj[1]}_gas",
                        status_key=obj,
                        name=split_obj[1].replace("_", " ").title() + " Gas",
                        value_fn=lambda sensor: sensor.coordinator.data["status"][
                            sensor.status_key
                        ]["gas"],
                        subscriptions=[(obj, "gas")],
                        icon="mdi:eye",
                        unit=None,
                        state_class=SensorStateClass.MEASUREMENT,
                    )
                    sensors.append(desc)
        elif split_obj[0] == "mcu":
            if len(split_obj) > 1:
                key = f"{split_obj[0]}_{split_obj[1]}"
                name = obj.replace("_", " ").title()
            else:
                key = split_obj[0]
                name = split_obj[0].title()
            desc = MoonrakerSensorDescription(
                key=f"{key}_load",
                status_key=obj,
                name=f"{name} Load",
                value_fn=lambda sensor: (
                    (
                        sensor.coordinator.data["status"][sensor.status_key][
                            "last_stats"
                        ]["mcu_task_avg"]
                        + 3
                        * sensor.coordinator.data["status"][sensor.status_key][
                            "last_stats"
                        ]["mcu_task_stddev"]
                    )
                    / 0.0025
                    * 100
                )
                if sensor.coordinator.data["status"][sensor.status_key]["last_stats"]
                is not None
                else 0,
                subscriptions=[(obj, "last_stats")],
                icon="mdi:cpu-64-bit",
                state_class=SensorStateClass.MEASUREMENT,
                unit=PERCENTAGE,
            )
            sensors.append(desc)
            desc = MoonrakerSensorDescription(
                key=f"{key}_awake",
                status_key=obj,
                name=f"{name} Awake",
                value_fn=lambda sensor: (
                    sensor.coordinator.data["status"][sensor.status_key]["last_stats"][
                        "mcu_awake"
                    ]
                    / 5
                    * 100
                )
                if sensor.coordinator.data["status"][sensor.status_key]["last_stats"]
                is not None
                else 0,
                icon="mdi:cpu-64-bit",
                subscriptions=[(obj, "last_stats")],
                state_class=SensorStateClass.MEASUREMENT,
                unit=PERCENTAGE,
            )
            sensors.append(desc)
        elif split_obj[0] in fan_keys:
            desc = MoonrakerSensorDescription(
                key=f"{split_obj[0]}_{split_obj[1]}",
                status_key=obj,
                name=split_obj[1].replace("_", " ").title(),
                value_fn=lambda sensor: sensor.coordinator.data["status"][
                    sensor.status_key
                ]["speed"]
                * 100,
                subscriptions=[(obj, "speed")],
                icon="mdi:fan",
                unit=PERCENTAGE,
                state_class=SensorStateClass.MEASUREMENT,
            )
            sensors.append(desc)

            query_obj = {OBJ: {obj: ["rpm"]}}
            fan_data = await coordinator.async_fetch_data(
                METHODS.PRINTER_OBJECTS_QUERY, query_obj, quiet=True
            )

            if fan_data["status"][obj]["rpm"]:
                desc = MoonrakerSensorDescription(
                    key=f"{split_obj[0]}_{split_obj[1]}_rpm",
                    status_key=obj,
                    name=f"{split_obj[1].replace('_', ' ').title()} RPM",
                    value_fn=lambda sensor: int(
                        sensor.coordinator.data["status"][sensor.status_key]["rpm"]
                    )
                    if sensor.coordinator.data["status"][sensor.status_key]["rpm"]
                    is not None
                    else None,
                    subscriptions=[(obj, "rpm")],
                    icon="mdi:fan",
                    unit=REVOLUTIONS_PER_MINUTE,
                    state_class=SensorStateClass.MEASUREMENT,
                )
                sensors.append(desc)
        elif obj == "fan":
            query_obj = {OBJ: {"fan": ["rpm"]}}
            fan_data = await coordinator.async_fetch_data(
                METHODS.PRINTER_OBJECTS_QUERY, query_obj, quiet=True
            )

            if fan_data["status"]["fan"]["rpm"]:
                desc = MoonrakerSensorDescription(
                    key="fan_rpm",
                    name="Fan RPM",
                    value_fn=lambda sensor: int(
                        sensor.coordinator.data["status"]["fan"]["rpm"]
                    )
                    if sensor.coordinator.data["status"]["fan"]["rpm"] is not None
                    else None,
                    subscriptions=[("fan", "rpm")],
                    icon="mdi:fan",
                    unit=REVOLUTIONS_PER_MINUTE,
                    state_class=SensorStateClass.MEASUREMENT,
                )
                sensors.append(desc)
        elif split_obj[0] == "heater_generic":
            desc = MoonrakerSensorDescription(
                key=f"{split_obj[0]}_{split_obj[1]}_power",
                status_key=obj,
                name=f"{split_obj[1].replace('_', ' ')} Power".title(),
                value_fn=lambda sensor: int(
                    (
                        sensor.coordinator.data["status"][sensor.status_key]["power"]
                        or 0.0
                    )
                    * 100
                ),
                subscriptions=[(obj, "power")],
                icon="mdi:flash",
                unit=PERCENTAGE,
                state_class=SensorStateClass.MEASUREMENT,
            )
            sensors.append(desc)

            desc = MoonrakerSensorDescription(
                key=f"{split_obj[0]}_{split_obj[1]}_temperature",
                status_key=obj,
                name=f"{split_obj[1].replace('_', ' ')} Temperature".title(),
                value_fn=lambda sensor: (
                    round(
                        sensor.coordinator.data["status"][sensor.status_key][
                            "temperature"
                        ],
                        2,
                    )
                    if sensor.coordinator.data["status"][sensor.status_key][
                        "temperature"
                    ]
                    is not None
                    else None
                ),
                subscriptions=[(obj, "temperature")],
                icon="mdi:thermometer",
                unit=UnitOfTemperature.CELSIUS,
                state_class=SensorStateClass.MEASUREMENT,
            )
            sensors.append(desc)

            desc = MoonrakerSensorDescription(
                key=f"{split_obj[0]}_{split_obj[1]}_target",
                status_key=obj,
                name=f"{split_obj[1].replace('_', ' ')} Target".title(),
                value_fn=lambda sensor: sensor.coordinator.data["status"][
                    sensor.status_key
                ]["target"],
                subscriptions=[(obj, "target")],
                icon="mdi:radiator",
                unit=UnitOfTemperature.CELSIUS,
                state_class=SensorStateClass.MEASUREMENT,
            )
            sensors.append(desc)
        elif obj.startswith("extruder") or obj.startswith("heater_bed"):
            if obj.startswith("extruder"):
                icon = "mdi:printer-3d-nozzle-heat"
                base_name = obj
            else:
                icon = "mdi:radiator"
                base_name = "Bed"

            desc = MoonrakerSensorDescription(
                key=f"{obj}_temp",
                status_key=obj,
                name=f"{base_name} Temperature".title(),
                value_fn=lambda sensor: (
                    round(
                        sensor.coordinator.data["status"][sensor.status_key][
                            "temperature"
                        ],
                        2,
                    )
                    if sensor.coordinator.data["status"][sensor.status_key][
                        "temperature"
                    ]
                    is not None
                    else None
                ),
                subscriptions=[(obj, "temperature")],
                icon=icon,
                unit=UnitOfTemperature.CELSIUS,
                state_class=SensorStateClass.MEASUREMENT,
            )
            sensors.append(desc)

            desc = MoonrakerSensorDescription(
                key=f"{obj}_power",
                status_key=obj,
                name=f"{base_name} Power".title(),
                value_fn=lambda sensor: int(
                    (
                        sensor.coordinator.data["status"][sensor.status_key]["power"]
                        or 0.0
                    )
                    * 100
                ),
                subscriptions=[(obj, "power")],
                icon="mdi:flash",
                unit=PERCENTAGE,
                state_class=SensorStateClass.MEASUREMENT,
            )
            sensors.append(desc)

    coordinator.load_sensor_data(sensors)
    await coordinator.async_refresh()
    async_add_entities([MoonrakerSensor(coordinator, entry, desc) for desc in sensors])


async def _history_updater(coordinator):
    return {
        "history": await coordinator.async_fetch_data(METHODS.SERVER_HISTORY_TOTALS)
    }


async def async_setup_history_sensors(coordinator, entry, async_add_entities):
    """Set history sensors."""
    history = await coordinator.async_fetch_data(METHODS.SERVER_HISTORY_TOTALS)
    if history.get("error"):
        return

    coordinator.add_data_updater(_history_updater)

    sensors = [
        MoonrakerSensorDescription(
            key="total_jobs",
            name="Totals jobs",
            value_fn=lambda sensor: sensor.coordinator.data["history"]["job_totals"][
                "total_jobs"
            ],
            subscriptions=[],
            icon="mdi:numeric",
            unit="Jobs",
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        MoonrakerSensorDescription(
            key="total_print_time",
            name="Totals Print Time",
            value_fn=lambda sensor: convert_time(
                sensor.coordinator.data["history"]["job_totals"]["total_print_time"]
            ),
            subscriptions=[],
            icon="mdi:clock-outline",
        ),
        MoonrakerSensorDescription(
            key="total_filament_used",
            name="Totals Filament Used",
            value_fn=lambda sensor: round(
                sensor.coordinator.data["history"]["job_totals"]["total_filament_used"]
                / 1000,
                2,
            ),
            subscriptions=[],
            icon="mdi:clock-outline",
            unit=UnitOfLength.METERS,
            state_class=SensorStateClass.TOTAL_INCREASING,
        ),
        MoonrakerSensorDescription(
            key="longest_print",
            name="Longest Print",
            value_fn=lambda sensor: convert_time(
                sensor.coordinator.data["history"]["job_totals"]["longest_print"]
            ),
            subscriptions=[],
            icon="mdi:clock-outline",
        ),
    ]

    coordinator.load_sensor_data(sensors)
    await coordinator.async_refresh()
    async_add_entities([MoonrakerSensor(coordinator, entry, desc) for desc in sensors])


async def _queue_updater(coordinator):
    return {
        "queue": await coordinator.async_fetch_data(METHODS.SERVER_JOB_QUEUE_STATUS)
    }


async def async_setup_queue_sensors(coordinator, entry, async_add_entities):
    """Job queue sensors."""
    queue = await coordinator.async_fetch_data(METHODS.SERVER_JOB_QUEUE_STATUS)
    if queue.get("queue_state") is None or queue.get("queued_jobs") is None:
        return

    coordinator.add_data_updater(_queue_updater)

    sensors = [
        MoonrakerSensorDescription(
            key="queue_state",
            name="Queue State",
            value_fn=lambda sensor: sensor.coordinator.data["queue"]["queue_state"],
            subscriptions=[("queue_state")],
        ),
        MoonrakerSensorDescription(
            key="queue_count",
            name="Jobs in queue",
            value_fn=lambda sensor: len(
                sensor.coordinator.data["queue"]["queued_jobs"]
            ),
            subscriptions=[("queued_jobs")],
            icon="mdi:numeric",
            unit="Jobs",
            state_class=SensorStateClass.MEASUREMENT,
        ),
    ]

    coordinator.load_sensor_data(sensors)
    await coordinator.async_refresh()
    async_add_entities([MoonrakerSensor(coordinator, entry, desc) for desc in sensors])


async def _machine_update_updater(coordinator):
    return {
        "machine_update": await coordinator.async_fetch_data(
            METHODS.MACHINE_UPDATE_STATUS
        )
    }


async def async_setup_machine_update_sensors(coordinator, entry, async_add_entities):
    """Test update available."""
    machine_status = await coordinator.async_fetch_data(METHODS.MACHINE_UPDATE_STATUS)
    if machine_status.get("error"):
        return
    coordinator.add_data_updater(_machine_update_updater)
    sensors = []

    for version_info in machine_status["version_info"]:
        if version_info == "system":
            sensors.append(
                MoonrakerSensorDescription(
                    key="machine_update_system",
                    name="Machine Update System",
                    value_fn=lambda sensor: f"{sensor.coordinator.data['machine_update']['version_info']['system']['package_count']} packages can be upgraded",
                    subscriptions=[],
                    icon="mdi:update",
                    entity_registry_enabled_default=False,
                )
            )
        elif (
            "version" in machine_status["version_info"][version_info]
            and "remote_version" in machine_status["version_info"][version_info]
        ):
            sensors.append(
                MoonrakerSensorDescription(
                    key=f"machine_update_{version_info}",
                    name=f"Version {version_info.title()}",
                    status_key=version_info,
                    value_fn=lambda sensor: (
                        lambda v, rv: f"{v} > {rv}" if v != rv else v
                    )(
                        sensor.coordinator.data["machine_update"]["version_info"][
                            sensor.status_key
                        ]["version"],
                        sensor.coordinator.data["machine_update"]["version_info"][
                            sensor.status_key
                        ]["remote_version"],
                    ),
                    subscriptions=[],
                    icon="mdi:update",
                    entity_registry_enabled_default=False,
                )
            )
    if len(sensors) > 0:
        coordinator.load_sensor_data(sensors)
        await coordinator.async_refresh()
        async_add_entities(
            [MoonrakerSensor(coordinator, entry, desc) for desc in sensors]
        )


class MoonrakerSensor(BaseMoonrakerEntity, SensorEntity):
    """MoonrakerSensor Sensor class."""

    def __init__(self, coordinator, entry, description):
        """Init."""
        super().__init__(coordinator, entry)
        self.coordinator = coordinator
        self.status_key = description.status_key
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_has_entity_name = True
        self.entity_description = description
        self._attr_native_value = description.value_fn(self)
        self._attr_icon = description.icon
        self._attr_native_unit_of_measurement = description.unit

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self.entity_description.value_fn(self)
        self.async_write_ha_state()

    def empty_result_when_not_printing(self, value=""):
        """Return empty string when not printing."""
        if (
            self.coordinator.data["status"]["print_stats"]["state"]
            != PRINTSTATES.PRINTING.value
        ):
            return "" if isinstance(value, str) else 0.0
        return value


def calculate_pct_job(data) -> float:
    """Get a pct estimate of the job based on a mix of progress value and fillament used.

    This strategy is inline with Mainsail estimate.
    """
    print_expected_duration = data["estimated_time"]
    filament_used = data["status"]["print_stats"]["filament_used"]
    expected_filament = data["filament_total"]
    divider = 0
    time_pct = 0
    filament_pct = 0

    if print_expected_duration != 0:
        time_pct = data["status"]["display_status"]["progress"]
        divider += 1

    if expected_filament != 0:
        filament_pct = 1.0 * filament_used / expected_filament
        divider += 1

    if divider == 0:
        return data["status"]["display_status"]["progress"]

    return (time_pct + filament_pct) / divider


def calculate_eta(data):
    """Calculate ETA of current print."""
    percent_job = calculate_pct_job(data)
    if (
        data["status"]["print_stats"]["state"] != PRINTSTATES.PRINTING.value
        or data["status"]["print_stats"]["print_duration"] <= 0
        or percent_job <= 0
        or percent_job >= 1
    ):
        return None

    time_left = round(
        (data["status"]["print_stats"]["print_duration"] / percent_job)
        - data["status"]["print_stats"]["print_duration"],
        2,
    )

    return datetime.now(timezone.utc) + timedelta(0, time_left)


def calculate_current_layer(data):
    """Calculate current layer."""

    if (
        data["status"]["print_stats"]["state"] != PRINTSTATES.PRINTING.value
        or data["status"]["print_stats"]["filename"] == ""
    ):
        return 0

    if (
        "info" in data["status"]["print_stats"]
        and data["status"]["print_stats"]["info"] is not None
        and "current_layer" in data["status"]["print_stats"]["info"]
        and data["status"]["print_stats"]["info"]["current_layer"] is not None
    ):
        return data["status"]["print_stats"]["info"]["current_layer"]

    if "layer_height" not in data or data["layer_height"] <= 0:
        return 0

    # layer = (current_z - first_layer_height) / layer_height + 1
    return (
        int(
            round(
                (data["status"]["toolhead"]["position"][2] - data["first_layer_height"])
                / data["layer_height"],
                0,
            )
        )
        + 1
    )


def convert_time(time_s):
    """Convert time in seconds to a human readable string."""
    return (
        f"{round(time_s // 3600)}h {round(time_s % 3600 // 60)}m {round(time_s % 60)}s"
    )


def calculate_memory_used(data):
    """Calculate memory used."""

    if "system_info" not in data:
        return None

    total_memory = data["system_info"]["cpu_info"]["total_memory"]
    memory_used = total_memory - data["status"]["system_stats"]["memavail"]
    percent_mem_used = memory_used / total_memory * 100
    return round(percent_mem_used, 2)
