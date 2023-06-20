from __future__ import annotations

import logging
from decimal import Decimal

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import CONF_NAME, UnitOfPower
from homeassistant.core import HomeAssistant
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import ConfigType

from custom_components.powercalc.common import create_source_entity
from custom_components.powercalc.const import (
    CONF_CREATE_ENERGY_SENSORS,
    CONF_POWER_SENSOR_PRECISION,
    DATA_STANDBY_POWER_SENSORS,
    DOMAIN,
    DUMMY_ENTITY_ID,
    SIGNAL_POWER_SENSOR_STATE_CHANGE,
)
from custom_components.powercalc.sensors.energy import create_energy_sensor
from custom_components.powercalc.sensors.power import PowerSensor

_LOGGER = logging.getLogger(__name__)


async def create_general_standby_sensors(
    hass: HomeAssistant,
    config: ConfigType,
) -> list[Entity]:
    sensors: list[Entity] = []
    power_sensor = StandbyPowerSensor(
        hass,
        rounding_digits=config.get(CONF_POWER_SENSOR_PRECISION),  # type: ignore
    )
    sensors.append(power_sensor)
    if config.get(CONF_CREATE_ENERGY_SENSORS):
        power_sensor.entity_id = "sensor.all_standby_power"
        sensor_config = config.copy()
        sensor_config[CONF_NAME] = "All standby"
        source_entity = await create_source_entity(DUMMY_ENTITY_ID, hass)
        energy_sensor = await create_energy_sensor(
            hass,
            sensor_config,
            power_sensor,
            source_entity,
        )
        sensors.append(energy_sensor)
    return sensors


class StandbyPowerSensor(SensorEntity, PowerSensor):
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_has_entity_name = True
    _attr_unique_id = "powercalc_standby_group"

    @property
    def name(self) -> str:
        """Name of the entity."""
        return "All standby power"

    def __init__(self, hass: HomeAssistant, rounding_digits: int = 2) -> None:
        self.standby_sensors: dict[str, Decimal] = hass.data[DOMAIN][
            DATA_STANDBY_POWER_SENSORS
        ]
        self._rounding_digits = rounding_digits

    async def async_added_to_hass(self) -> None:
        """Register state listeners."""
        await super().async_added_to_hass()
        async_dispatcher_connect(
            self.hass,
            SIGNAL_POWER_SENSOR_STATE_CHANGE,
            self._recalculate,
        )

    async def _recalculate(self) -> None:
        """Calculate sum of all power sensors in standby, and update the state of the sensor."""
        if self.standby_sensors:
            self._attr_native_value = round(
                sum(self.standby_sensors.values()),
                self._rounding_digits,
            )
        else:
            self._attr_native_value = None
        self.async_schedule_update_ha_state(True)
