from __future__ import annotations

import inspect
import logging
from typing import cast

from homeassistant.components.select import DOMAIN as SELECT_DOMAIN
from homeassistant.components.sensor import SensorEntity
from homeassistant.components.utility_meter.const import (
    DATA_TARIFF_SENSORS,
    DATA_UTILITY,
)
from homeassistant.components.utility_meter.const import DOMAIN as UTILITY_DOMAIN
from homeassistant.components.utility_meter.select import TariffSelect
from homeassistant.components.utility_meter.sensor import UtilityMeterSensor
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_component import EntityComponent

from ..const import (
    CONF_CREATE_UTILITY_METERS,
    CONF_ENERGY_SENSOR_PRECISION,
    CONF_UTILITY_METER_OFFSET,
    CONF_UTILITY_METER_TARIFFS,
    CONF_UTILITY_METER_TYPES,
    DEFAULT_ENERGY_SENSOR_PRECISION,
)
from ..errors import SensorConfigurationError
from .abstract import BaseEntity

_LOGGER = logging.getLogger(__name__)


async def create_utility_meters(
    hass: HomeAssistant,
    energy_sensor: SensorEntity,
    sensor_config: dict,
) -> list[UtilityMeterSensor]:
    """Create the utility meters"""

    if not sensor_config.get(CONF_CREATE_UTILITY_METERS):
        return []

    utility_meters = []

    if DATA_UTILITY not in hass.data:
        hass.data[DATA_UTILITY] = {}

    tariffs = sensor_config.get(CONF_UTILITY_METER_TARIFFS)
    meter_types = sensor_config.get(CONF_UTILITY_METER_TYPES)
    for meter_type in meter_types:
        tariff_sensors = []

        name = f"{energy_sensor.name} {meter_type}"
        entity_id = f"{energy_sensor.entity_id}_{meter_type}"
        unique_id = None
        if energy_sensor.unique_id:
            unique_id = f"{energy_sensor.unique_id}_{meter_type}"

        if tariffs:
            tariff_select = await create_tariff_select(tariffs, hass, name, unique_id)

            for tariff in tariffs:
                utility_meter = await create_utility_meter(
                    energy_sensor.entity_id,
                    entity_id,
                    name,
                    sensor_config,
                    meter_type,
                    unique_id,
                    tariff,
                    tariff_select.entity_id,
                )
                tariff_sensors.append(utility_meter)
                utility_meters.append(utility_meter)

        else:
            utility_meter = await create_utility_meter(
                energy_sensor.entity_id,
                entity_id,
                name,
                sensor_config,
                meter_type,
                unique_id,
            )
            tariff_sensors.append(utility_meter)
            utility_meters.append(utility_meter)

        hass.data[DATA_UTILITY][entity_id] = {DATA_TARIFF_SENSORS: tariff_sensors}

    return utility_meters


async def create_tariff_select(
    tariffs: list, hass: HomeAssistant, name: str, unique_id: str | None
):
    """Create tariff selection entity"""

    _LOGGER.debug(f"Creating utility_meter tariff select: {name}")
    utility_meter_component = cast(
        EntityComponent, hass.data["entity_components"].get(UTILITY_DOMAIN)
    )
    if utility_meter_component is None:
        utility_meter_component = (
            hass.data.get("utility_meter_legacy_component") or None
        )

    if utility_meter_component is None:
        raise SensorConfigurationError("Cannot find utility_meter component")

    select_component = cast(EntityComponent, hass.data[SELECT_DOMAIN])
    select_unique_id = None
    if unique_id:
        select_unique_id = f"{unique_id}_select"
    tariff_select = TariffSelect(
        name,
        list(tariffs),
        utility_meter_component.async_add_entities,
        select_unique_id,
    )

    await select_component.async_add_entities([tariff_select])

    return tariff_select


async def create_utility_meter(
    source_entity: str,
    entity_id: str,
    name: str,
    sensor_config: dict,
    meter_type: str,
    unique_id: str = None,
    tariff: str = None,
    tariff_entity: str = None,
) -> VirtualUtilityMeter:
    """Create a utility meter entity, one per tariff"""

    parent_meter = entity_id
    if tariff:
        name = f"{name} {tariff}"
        entity_id = f"{entity_id}_{tariff}"
        if unique_id:
            unique_id = f"{unique_id}_{tariff}"

    _LOGGER.debug(f"Creating utility_meter sensor: {name} (entity_id={entity_id})")

    params = {
        "source_entity": source_entity,
        "name": name,
        "meter_type": meter_type,
        "meter_offset": sensor_config.get(CONF_UTILITY_METER_OFFSET),
        "net_consumption": False,
        "tariff": tariff,
        "tariff_entity": tariff_entity,
    }

    signature = inspect.signature(UtilityMeterSensor.__init__)
    if "parent_meter" in signature.parameters:
        params["parent_meter"] = parent_meter
    if "delta_values" in signature.parameters:
        params["delta_values"] = False
    if "unique_id" in signature.parameters:
        params["unique_id"] = unique_id
    if "cron_pattern" in signature.parameters:
        params["cron_pattern"] = None

    utility_meter = VirtualUtilityMeter(**params)
    setattr(
        utility_meter,
        "rounding_digits",
        sensor_config.get(CONF_ENERGY_SENSOR_PRECISION),
    )

    utility_meter.entity_id = entity_id

    return utility_meter


class VirtualUtilityMeter(UtilityMeterSensor, BaseEntity):
    rounding_digits: int = DEFAULT_ENERGY_SENSOR_PRECISION

    @property
    def unique_id(self):
        """Return the unique id."""
        return self._attr_unique_id

    @unique_id.setter
    def unique_id(self, value):
        """Set unique id."""
        self._attr_unique_id = value

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self.rounding_digits and self._state is not None:
            return round(self._state, self.rounding_digits)

        return self._state
