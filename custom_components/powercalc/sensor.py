"""Platform for sensor integration."""

from __future__ import annotations

import copy
import logging
import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, NamedTuple

import homeassistant.helpers.config_validation as cv
import homeassistant.helpers.device_registry as dr
import homeassistant.helpers.entity_registry as er
import voluptuous as vol
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.components.utility_meter import max_28_days
from homeassistant.components.utility_meter.const import METER_TYPES
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_DOMAIN,
    CONF_ENTITIES,
    CONF_ENTITY_ID,
    CONF_NAME,
    CONF_UNIQUE_ID,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_platform
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity_registry import RegistryEntryDisabler
from homeassistant.helpers.template import Template
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .common import (
    SourceEntity,
    create_source_entity,
    get_merged_sensor_configuration,
    validate_is_number,
    validate_name_pattern,
)
from .const import (
    CONF_AREA,
    CONF_CALCULATION_ENABLED_CONDITION,
    CONF_CALIBRATE,
    CONF_CREATE_ENERGY_SENSOR,
    CONF_CREATE_GROUP,
    CONF_CREATE_UTILITY_METERS,
    CONF_CUSTOM_MODEL_DIRECTORY,
    CONF_DAILY_FIXED_ENERGY,
    CONF_DELAY,
    CONF_DISABLE_STANDBY_POWER,
    CONF_ENERGY_INTEGRATION_METHOD,
    CONF_ENERGY_SENSOR_CATEGORY,
    CONF_ENERGY_SENSOR_ID,
    CONF_ENERGY_SENSOR_NAMING,
    CONF_ENERGY_SENSOR_UNIT_PREFIX,
    CONF_FILTER,
    CONF_FIXED,
    CONF_FORCE_ENERGY_SENSOR_CREATION,
    CONF_GROUP,
    CONF_HIDE_MEMBERS,
    CONF_IGNORE_UNAVAILABLE_STATE,
    CONF_INCLUDE,
    CONF_LINEAR,
    CONF_MANUFACTURER,
    CONF_MODE,
    CONF_MODEL,
    CONF_MULTIPLY_FACTOR,
    CONF_MULTIPLY_FACTOR_STANDBY,
    CONF_ON_TIME,
    CONF_POWER,
    CONF_POWER_SENSOR_CATEGORY,
    CONF_POWER_SENSOR_ID,
    CONF_POWER_SENSOR_NAMING,
    CONF_POWER_TEMPLATE,
    CONF_SENSOR_TYPE,
    CONF_SLEEP_POWER,
    CONF_STANDBY_POWER,
    CONF_STATES_POWER,
    CONF_TEMPLATE,
    CONF_UNAVAILABLE_POWER,
    CONF_UTILITY_METER_OFFSET,
    CONF_UTILITY_METER_TARIFFS,
    CONF_UTILITY_METER_TYPES,
    CONF_VALUE,
    CONF_VALUE_TEMPLATE,
    CONF_WLED,
    DATA_CONFIGURED_ENTITIES,
    DATA_DISCOVERED_ENTITIES,
    DATA_DOMAIN_ENTITIES,
    DATA_USED_UNIQUE_IDS,
    DISCOVERY_SOURCE_ENTITY,
    DISCOVERY_TYPE,
    DOMAIN,
    DOMAIN_CONFIG,
    DUMMY_ENTITY_ID,
    ENERGY_INTEGRATION_METHODS,
    ENTITY_CATEGORIES,
    ENTRY_DATA_ENERGY_ENTITY,
    ENTRY_DATA_POWER_ENTITY,
    SERVICE_CALIBRATE_ENERGY,
    SERVICE_CALIBRATE_UTILITY_METER,
    SERVICE_INCREASE_DAILY_ENERGY,
    SERVICE_RESET_ENERGY,
    CalculationStrategy,
    PowercalcDiscoveryType,
    SensorType,
    UnitPrefix,
)
from .discovery import autodiscover_model
from .errors import (
    ModelNotSupportedError,
    PowercalcSetupError,
    SensorAlreadyConfiguredError,
    SensorConfigurationError,
)
from .group_include.include import resolve_include_entities
from .power_profile.factory import get_power_profile
from .sensors.abstract import BaseEntity
from .sensors.daily_energy import (
    DAILY_FIXED_ENERGY_SCHEMA,
    create_daily_fixed_energy_power_sensor,
    create_daily_fixed_energy_sensor,
)
from .sensors.energy import EnergySensor, create_energy_sensor
from .sensors.group import (
    add_to_associated_group,
    create_domain_group_sensor,
    create_group_sensors,
    create_group_sensors_from_config_entry,
)
from .sensors.group_standby import create_general_standby_sensors
from .sensors.power import VirtualPowerSensor, create_power_sensor
from .sensors.utility_meter import create_utility_meters
from .strategy.fixed import CONFIG_SCHEMA as FIXED_SCHEMA
from .strategy.linear import CONFIG_SCHEMA as LINEAR_SCHEMA
from .strategy.wled import CONFIG_SCHEMA as WLED_SCHEMA

_LOGGER = logging.getLogger(__name__)

MAX_GROUP_NESTING_LEVEL = 5

SENSOR_CONFIG = {
    vol.Optional(CONF_NAME): cv.string,
    vol.Optional(CONF_ENTITY_ID): cv.entity_id,
    vol.Optional(CONF_UNIQUE_ID): cv.string,
    vol.Optional(CONF_MODEL): cv.string,
    vol.Optional(CONF_MANUFACTURER): cv.string,
    vol.Optional(CONF_MODE): vol.In([cls.value for cls in CalculationStrategy]),
    vol.Optional(CONF_STANDBY_POWER): vol.Coerce(float),
    vol.Optional(CONF_DISABLE_STANDBY_POWER): cv.boolean,
    vol.Optional(CONF_CUSTOM_MODEL_DIRECTORY): cv.string,
    vol.Optional(CONF_POWER_SENSOR_ID): cv.entity_id,
    vol.Optional(CONF_FORCE_ENERGY_SENSOR_CREATION): cv.boolean,
    vol.Optional(CONF_FIXED): FIXED_SCHEMA,
    vol.Optional(CONF_LINEAR): LINEAR_SCHEMA,
    vol.Optional(CONF_WLED): WLED_SCHEMA,
    vol.Optional(CONF_DAILY_FIXED_ENERGY): DAILY_FIXED_ENERGY_SCHEMA,
    vol.Optional(CONF_CREATE_ENERGY_SENSOR): cv.boolean,
    vol.Optional(CONF_CREATE_UTILITY_METERS): cv.boolean,
    vol.Optional(CONF_UTILITY_METER_TARIFFS): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_UTILITY_METER_TYPES): vol.All(
        cv.ensure_list,
        [vol.In(METER_TYPES)],
    ),
    vol.Optional(CONF_UTILITY_METER_OFFSET): vol.All(
        cv.time_period,
        cv.positive_timedelta,
        max_28_days,
    ),
    vol.Optional(CONF_MULTIPLY_FACTOR): vol.Coerce(float),
    vol.Optional(CONF_MULTIPLY_FACTOR_STANDBY): cv.boolean,
    vol.Optional(CONF_POWER_SENSOR_NAMING): validate_name_pattern,
    vol.Optional(CONF_POWER_SENSOR_CATEGORY): vol.In(ENTITY_CATEGORIES),
    vol.Optional(CONF_ENERGY_SENSOR_ID): cv.entity_id,
    vol.Optional(CONF_ENERGY_SENSOR_NAMING): validate_name_pattern,
    vol.Optional(CONF_ENERGY_SENSOR_CATEGORY): vol.In(ENTITY_CATEGORIES),
    vol.Optional(CONF_ENERGY_INTEGRATION_METHOD): vol.In(ENERGY_INTEGRATION_METHODS),
    vol.Optional(CONF_ENERGY_SENSOR_UNIT_PREFIX): vol.In(
        [cls.value for cls in UnitPrefix],
    ),
    vol.Optional(CONF_CREATE_GROUP): cv.string,
    vol.Optional(CONF_HIDE_MEMBERS): cv.boolean,
    vol.Optional(CONF_INCLUDE): vol.Schema(
        {
            vol.Optional(CONF_AREA): cv.string,
            vol.Optional(CONF_GROUP): cv.entity_id,
            vol.Optional(CONF_TEMPLATE): cv.template,
            vol.Optional(CONF_DOMAIN): cv.string,
            vol.Optional(CONF_FILTER): vol.Schema(
                {
                    vol.Required(CONF_DOMAIN): vol.Any(cv.string, [cv.string]),
                },
            ),
        },
    ),
    vol.Optional(CONF_IGNORE_UNAVAILABLE_STATE): cv.boolean,
    vol.Optional(CONF_CALCULATION_ENABLED_CONDITION): cv.template,
    vol.Optional(CONF_SLEEP_POWER): vol.Schema(
        {
            vol.Required(CONF_POWER): vol.Coerce(float),
            vol.Required(CONF_DELAY): cv.positive_int,
        },
    ),
    vol.Optional(CONF_UNAVAILABLE_POWER): vol.Coerce(float),
}


def build_nested_configuration_schema(schema: dict, iteration: int = 0) -> dict:
    if iteration == MAX_GROUP_NESTING_LEVEL:
        return schema
    iteration += 1
    schema.update(
        {
            vol.Optional(CONF_ENTITIES): vol.All(
                cv.ensure_list,
                [build_nested_configuration_schema(schema.copy(), iteration)],
            ),
        },
    )
    return schema


SENSOR_CONFIG = build_nested_configuration_schema(SENSOR_CONFIG)

PLATFORM_SCHEMA = vol.All(
    cv.has_at_least_one_key(
        CONF_ENTITY_ID,
        CONF_POWER_SENSOR_ID,
        CONF_ENTITIES,
        CONF_INCLUDE,
        CONF_DAILY_FIXED_ENERGY,
    ),
    PLATFORM_SCHEMA.extend(SENSOR_CONFIG),
)

ENTITY_ID_FORMAT = SENSOR_DOMAIN + ".{}"


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Setup sensors from YAML config sensor entries."""
    await _async_setup_entities(
        hass,
        config,
        async_add_entities,
        discovery_info=discovery_info,
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Setup sensors from config entry (GUI config flow)."""
    sensor_config = convert_config_entry_to_sensor_config(entry)
    sensor_type = entry.data.get(CONF_SENSOR_TYPE)
    if sensor_type == SensorType.GROUP:
        global_config: dict = hass.data[DOMAIN][DOMAIN_CONFIG]
        merged_sensor_config = get_merged_sensor_configuration(
            global_config,
            sensor_config,
        )
        entities = await create_group_sensors_from_config_entry(
            hass=hass,
            entry=entry,
            sensor_config=merged_sensor_config,
        )
        async_add_entities(entities)
        return

    if CONF_UNIQUE_ID not in sensor_config:
        sensor_config[CONF_UNIQUE_ID] = entry.unique_id

    await _async_setup_entities(
        hass,
        sensor_config,
        async_add_entities,
        config_entry=entry,
    )

    # Add entry to an existing group
    await add_to_associated_group(hass, entry)


async def _async_setup_entities(
    hass: HomeAssistant,
    config: dict[str, Any],
    async_add_entities: AddEntitiesCallback,
    config_entry: ConfigEntry | None = None,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Main routine to setup power/energy sensors from provided configuration."""
    register_entity_services()

    try:
        entities = await create_sensors(hass, config, discovery_info, config_entry)
        if not entities:
            return

        if config_entry:
            save_entity_ids_on_config_entry(hass, config_entry, entities)
    except SensorConfigurationError as err:
        _LOGGER.error(err)
        return

    entities_to_add = [
        entity for entity in entities.new if isinstance(entity, SensorEntity)
    ]

    # See: https://github.com/bramstroker/homeassistant-powercalc/issues/1454
    # Remove entities which are disabled because of a disabled device from the list of entities to add
    # When we add nevertheless the entity_platform code will set device_id to None and abort entity addition.
    # `async_added_to_hass` hook will not be called, which powercalc uses to bind the entity to device again
    # This causes the powercalc entity to never be bound to the device again and be disabled forever.
    entity_reg = er.async_get(hass)
    for entity in entities_to_add:
        existing_entry = entity_reg.async_get(entity.entity_id)
        if (
            existing_entry
            and existing_entry.disabled_by == RegistryEntryDisabler.DEVICE
        ):
            entities_to_add.remove(entity)

    async_add_entities(entities_to_add)


@callback
def save_entity_ids_on_config_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    entities: EntitiesBucket,
) -> None:
    """Save the power and energy sensor entity_id's on the config entry
    We need this in group sensor logic to differentiate between energy sensor and utility meters.
    """
    power_entities = [
        e.entity_id for e in entities.all() if isinstance(e, VirtualPowerSensor)
    ]
    new_data = config_entry.data.copy()
    if power_entities:
        new_data.update({ENTRY_DATA_POWER_ENTITY: power_entities[0]})

    if CONF_CREATE_ENERGY_SENSOR not in config_entry.data or config_entry.data.get(
        CONF_CREATE_ENERGY_SENSOR,
    ):
        energy_entities = [
            e.entity_id for e in entities.all() if isinstance(e, EnergySensor)
        ]
        if not energy_entities:
            raise SensorConfigurationError(
                f"No energy sensor created for config_entry {config_entry.entry_id}",
            )
        new_data.update({ENTRY_DATA_ENERGY_ENTITY: energy_entities[0]})

    hass.config_entries.async_update_entry(
        config_entry,
        data=new_data,
    )


@callback
def register_entity_services() -> None:
    """Register the different entity services."""
    platform = entity_platform.async_get_current_platform()
    platform.async_register_entity_service(
        SERVICE_RESET_ENERGY,
        {},
        "async_reset",
    )

    platform.async_register_entity_service(
        SERVICE_CALIBRATE_UTILITY_METER,
        {vol.Required(CONF_VALUE): validate_is_number},  # type: ignore
        "async_calibrate",
    )

    platform.async_register_entity_service(
        SERVICE_CALIBRATE_ENERGY,
        {vol.Required(CONF_VALUE): validate_is_number},  # type: ignore
        "async_calibrate",
    )

    platform.async_register_entity_service(
        SERVICE_INCREASE_DAILY_ENERGY,
        {vol.Required(CONF_VALUE): validate_is_number},  # type: ignore
        "async_increase",
    )


def convert_config_entry_to_sensor_config(config_entry: ConfigEntry) -> ConfigType:
    """Convert the config entry structure to the sensor config which we use to create the entities."""
    sensor_config = dict(config_entry.data.copy())

    if sensor_config.get(CONF_SENSOR_TYPE) == SensorType.GROUP:
        sensor_config[CONF_CREATE_GROUP] = sensor_config.get(CONF_NAME)

    if CONF_DAILY_FIXED_ENERGY in sensor_config:
        daily_fixed_config: dict[str, Any] = copy.copy(sensor_config.get(CONF_DAILY_FIXED_ENERGY))  # type: ignore
        if CONF_VALUE_TEMPLATE in daily_fixed_config:
            daily_fixed_config[CONF_VALUE] = Template(
                daily_fixed_config[CONF_VALUE_TEMPLATE],
            )
            del daily_fixed_config[CONF_VALUE_TEMPLATE]
        if CONF_ON_TIME in daily_fixed_config:
            on_time = daily_fixed_config[CONF_ON_TIME]
            daily_fixed_config[CONF_ON_TIME] = timedelta(
                hours=on_time["hours"],
                minutes=on_time["minutes"],
                seconds=on_time["seconds"],
            )
        else:
            daily_fixed_config[CONF_ON_TIME] = timedelta(days=1)
        sensor_config[CONF_DAILY_FIXED_ENERGY] = daily_fixed_config

    if CONF_FIXED in sensor_config:
        fixed_config: dict[str, Any] = copy.copy(sensor_config.get(CONF_FIXED))  # type: ignore
        if CONF_POWER_TEMPLATE in fixed_config:
            fixed_config[CONF_POWER] = Template(fixed_config[CONF_POWER_TEMPLATE])
            del fixed_config[CONF_POWER_TEMPLATE]
        if CONF_STATES_POWER in fixed_config:
            new_states_power = {}
            for key, value in fixed_config[CONF_STATES_POWER].items():
                if isinstance(value, str) and "{{" in value:
                    value = Template(value)
                new_states_power[key] = value
            fixed_config[CONF_STATES_POWER] = new_states_power
        sensor_config[CONF_FIXED] = fixed_config

    if CONF_LINEAR in sensor_config:
        linear_config: dict[str, Any] = copy.copy(sensor_config.get(CONF_LINEAR))  # type: ignore
        if CONF_CALIBRATE in linear_config:
            calibrate_dict: dict[str, float] = linear_config.get(CONF_CALIBRATE)  # type: ignore
            new_calibrate_list: list[str] = []
            for item in calibrate_dict.items():
                new_calibrate_list.append(f"{item[0]} -> {item[1]}")
            linear_config[CONF_CALIBRATE] = new_calibrate_list

        sensor_config[CONF_LINEAR] = linear_config

    if CONF_CALCULATION_ENABLED_CONDITION in sensor_config:
        sensor_config[CONF_CALCULATION_ENABLED_CONDITION] = Template(
            sensor_config[CONF_CALCULATION_ENABLED_CONDITION],
        )

    return sensor_config


async def create_sensors(
    hass: HomeAssistant,
    config: ConfigType,
    discovery_info: DiscoveryInfoType | None = None,
    config_entry: ConfigEntry | None = None,
    context: CreationContext | None = None,
) -> EntitiesBucket:
    """Main routine to create all sensors (power, energy, utility, group) for a given entity."""
    if context is None:
        context = CreationContext(
            group=CONF_CREATE_GROUP in config,
            entity_config=config,
        )

    global_config = hass.data[DOMAIN][DOMAIN_CONFIG]

    # Handle setup of domain groups and general standby power group
    if discovery_info:
        if discovery_info[DISCOVERY_TYPE] == PowercalcDiscoveryType.DOMAIN_GROUP:
            return EntitiesBucket(
                new=await create_domain_group_sensor(
                    hass,
                    discovery_info,
                    global_config,
                ),
            )
        if discovery_info[DISCOVERY_TYPE] == PowercalcDiscoveryType.STANDBY_GROUP:
            return EntitiesBucket(
                new=await create_general_standby_sensors(hass, global_config),
            )

    # Setup a power sensor for one single appliance. Either by manual configuration or discovery
    if CONF_ENTITIES not in config and CONF_INCLUDE not in config:
        if discovery_info:
            config[CONF_ENTITY_ID] = discovery_info[CONF_ENTITY_ID]
        merged_sensor_config = get_merged_sensor_configuration(global_config, config)
        return await create_individual_sensors(
            hass,
            merged_sensor_config,
            context,
            config_entry,
            discovery_info,
        )

    # Setup power sensors for multiple appliances in one config entry
    sensor_configs = {}
    entities_to_add = EntitiesBucket()
    for entity_config in config.get(CONF_ENTITIES) or []:
        # When there are nested entities, combine these with the current entities, recursively
        if CONF_ENTITIES in entity_config or CONF_CREATE_GROUP in entity_config:
            child_entities = await create_sensors(hass, entity_config, context=context)
            entities_to_add.extend_items(child_entities)
            continue

        entity_id = entity_config.get(CONF_ENTITY_ID) or str(uuid.uuid4())
        sensor_configs.update({entity_id: entity_config})

    # Automatically add a bunch of entities by area or evaluating template
    if CONF_INCLUDE in config:
        entities = resolve_include_entities(hass, config.get(CONF_INCLUDE))  # type: ignore
        _LOGGER.debug("Found include entities: %s", entities)
        sensor_configs = {
            entity.entity_id: {CONF_ENTITY_ID: entity.entity_id}
            for entity in entities
            if await is_auto_configurable(hass, entity)
        } | sensor_configs

    # Create sensors for each entity
    for sensor_config in sensor_configs.values():
        try:
            merged_sensor_config = get_merged_sensor_configuration(
                global_config,
                config,
                sensor_config,
            )
            entities_to_add.extend_items(
                await create_individual_sensors(
                    hass,
                    merged_sensor_config,
                    config_entry=config_entry,
                    context=CreationContext(
                        group=context.group,
                        entity_config=sensor_config,
                    ),
                ),
            )
        except SensorConfigurationError as error:
            _LOGGER.error(error)

    if not entities_to_add.has_entities():
        exception_message = "Could not resolve any entities"
        if CONF_CREATE_GROUP in config:
            exception_message += f" in group '{config.get(CONF_CREATE_GROUP)}'"
        raise SensorConfigurationError(exception_message)

    # Create group sensors (power, energy, utility)
    if CONF_CREATE_GROUP in config:
        entities_to_add.new.extend(
            await create_group_sensors(
                str(config.get(CONF_CREATE_GROUP)),
                get_merged_sensor_configuration(global_config, config, validate=False),
                entities_to_add.all(),
                hass=hass,
            ),
        )

    return entities_to_add


async def create_individual_sensors(
    hass: HomeAssistant,
    sensor_config: dict,
    context: CreationContext,
    config_entry: ConfigEntry | None = None,
    discovery_info: DiscoveryInfoType | None = None,
) -> EntitiesBucket:
    """Create entities (power, energy, utility_meters) which track the appliance."""
    if discovery_info:
        source_entity: SourceEntity = discovery_info.get(DISCOVERY_SOURCE_ENTITY)  # type: ignore
    else:
        source_entity = await create_source_entity(sensor_config[CONF_ENTITY_ID], hass)

    if (used_unique_ids := hass.data[DOMAIN].get(DATA_USED_UNIQUE_IDS)) is None:
        used_unique_ids = hass.data[DOMAIN][DATA_USED_UNIQUE_IDS] = []
    try:
        await check_entity_not_already_configured(
            sensor_config,
            source_entity,
            hass,
            used_unique_ids,
            discovery_info is not None,
        )
    except SensorAlreadyConfiguredError as error:
        # Include previously discovered/configured entities in group when no specific configuration
        if context.group and list(context.entity_config.keys()) == [CONF_ENTITY_ID]:
            return EntitiesBucket([], error.existing_entities)
        if discovery_info:
            return EntitiesBucket()
        raise error

    entities_to_add: list[Entity] = []
    energy_sensor: EnergySensor | None = None
    if CONF_DAILY_FIXED_ENERGY in sensor_config:
        energy_sensor = await create_daily_fixed_energy_sensor(
            hass,
            sensor_config,
            source_entity,
        )
        entities_to_add.append(energy_sensor)

        if source_entity:
            daily_fixed_power_sensor = await create_daily_fixed_energy_power_sensor(
                hass,
                sensor_config,
                source_entity,
            )
            if daily_fixed_power_sensor:
                entities_to_add.append(daily_fixed_power_sensor)
    else:
        try:
            power_sensor = await create_power_sensor(
                hass,
                sensor_config,
                source_entity,
                discovery_info,
            )

            entities_to_add.append(power_sensor)
        except PowercalcSetupError:
            return EntitiesBucket()

        # Create energy sensor which integrates the power sensor
        if sensor_config.get(CONF_CREATE_ENERGY_SENSOR):
            energy_sensor = await create_energy_sensor(
                hass,
                sensor_config,
                power_sensor,
                source_entity,
            )
            entities_to_add.append(energy_sensor)
            if isinstance(power_sensor, VirtualPowerSensor):
                power_sensor.set_energy_sensor_attribute(energy_sensor.entity_id)

    if energy_sensor:
        entities_to_add.extend(
            await create_utility_meters(hass, energy_sensor, sensor_config),
        )

    await attach_entities_to_source_device(
        config_entry,
        entities_to_add,
        hass,
        source_entity,
    )

    # Update several registries
    hass.data[DOMAIN][
        DATA_DISCOVERED_ENTITIES if discovery_info else DATA_CONFIGURED_ENTITIES
    ].update(
        {source_entity.entity_id: entities_to_add},
    )

    if source_entity.domain not in hass.data[DOMAIN][DATA_DOMAIN_ENTITIES]:
        hass.data[DOMAIN][DATA_DOMAIN_ENTITIES][source_entity.domain] = []

    hass.data[DOMAIN][DATA_DOMAIN_ENTITIES][source_entity.domain].extend(
        entities_to_add,
    )

    # Keep track for which unique_id's we generated sensors already
    unique_id = sensor_config.get(CONF_UNIQUE_ID) or source_entity.unique_id
    if unique_id:
        used_unique_ids.append(unique_id)

    return EntitiesBucket(new=entities_to_add, existing=[])


async def attach_entities_to_source_device(
    config_entry: ConfigEntry | None,
    entities_to_add: list[Entity],
    hass: HomeAssistant,
    source_entity: SourceEntity,
) -> None:
    """Set the entity to same device as the source entity, if any available."""
    if source_entity.entity_entry and source_entity.device_entry:
        device_id = source_entity.device_entry.id
        device_registry = dr.async_get(hass)
        for entity in entities_to_add:
            if not isinstance(entity, BaseEntity):
                continue
            try:
                entity.source_device_id = source_entity.device_entry.id  # type: ignore
            except AttributeError:
                _LOGGER.error(f"{entity.entity_id}: Cannot set device id on entity")
        if (
            config_entry
            and config_entry.entry_id not in source_entity.device_entry.config_entries
        ):
            device_registry.async_update_device(
                device_id,
                add_config_entry_id=config_entry.entry_id,
            )


async def check_entity_not_already_configured(
    sensor_config: dict,
    source_entity: SourceEntity,
    hass: HomeAssistant,
    used_unique_ids: list[str],
    is_discovered: bool = True,
) -> None:
    if source_entity.entity_id == DUMMY_ENTITY_ID:
        return

    configured_entities: dict[str, list[SensorEntity]] = hass.data[DOMAIN][
        DATA_CONFIGURED_ENTITIES
    ]
    discovered_entities: dict[str, list[SensorEntity]] = hass.data[DOMAIN][
        DATA_DISCOVERED_ENTITIES
    ]

    # Prefer configured entity over discovered entity
    if not is_discovered and source_entity.entity_id in discovered_entities:
        entity_reg = er.async_get(hass)
        for entity in discovered_entities.get(source_entity.entity_id) or []:
            if entity_reg.async_get(entity.entity_id):
                entity_reg.async_remove(entity.entity_id)
            hass.states.async_remove(entity.entity_id)
        discovered_entities[source_entity.entity_id] = []
        return

    existing_entities = (
        configured_entities.get(source_entity.entity_id)
        or discovered_entities.get(source_entity.entity_id)
        or []
    )

    unique_id = sensor_config.get(CONF_UNIQUE_ID) or source_entity.unique_id
    if unique_id in used_unique_ids:
        raise SensorAlreadyConfiguredError(source_entity.entity_id, existing_entities)

    entity_id = source_entity.entity_id
    if unique_id is None and (
        entity_id in discovered_entities or entity_id in configured_entities
    ):
        raise SensorAlreadyConfiguredError(source_entity.entity_id, existing_entities)


async def is_auto_configurable(
    hass: HomeAssistant,
    entity_entry: er.RegistryEntry,
    sensor_config: ConfigType | None = None,
) -> bool:
    try:
        model_info = await autodiscover_model(hass, entity_entry)
        if not model_info:
            return False
        power_profile = await get_power_profile(
            hass,
            sensor_config or {},
            model_info=model_info,
        )
        if not power_profile:
            return False
        source_entity = await create_source_entity(entity_entry.entity_id, hass)
        if not power_profile.is_entity_domain_supported(source_entity):
            return False
        if power_profile.has_sub_profiles and power_profile.sub_profile:
            return True
        return not power_profile.is_additional_configuration_required
    except ModelNotSupportedError:
        return False


@dataclass
class EntitiesBucket:
    new: list[Entity] = field(default_factory=list)
    existing: list[Entity] = field(default_factory=list)

    def extend_items(self, bucket: EntitiesBucket) -> None:
        """Append current entity bucket with new one"""
        self.new.extend(bucket.new)
        self.existing.extend(bucket.existing)

    def all(self) -> list[Entity]:  # noqa: A003
        """Return all entities both new and existing"""
        return self.new + self.existing

    def has_entities(self) -> bool:
        """Check whether the entity bucket is not empty"""
        return bool(self.new) or bool(self.existing)


class CreationContext(NamedTuple):
    group: bool = False
    entity_config: ConfigType = {}
