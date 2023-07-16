""" Risk of mold growth at present temperature and humidity. """
from __future__ import annotations

from math import exp
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorDeviceClass,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.const import (
    PERCENTAGE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_state_change_event

from .const import (
    CONF_HUM_ID,
    CONF_TEMP_ID,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """ Initialize mold risk index config entry. """
    registry = er.async_get(hass)
    
    hum_entity_id = er.async_validate_entity_id(
        registry, config_entry.options[CONF_HUM_ID]
    )
    temp_entity_id = er.async_validate_entity_id(
        registry, config_entry.options[CONF_TEMP_ID]
    )
    mold_calc = MoldRiskCalculator(hum_entity_id, temp_entity_id)

    async_add_entities(
        [
            MoldRiskLimitSensor(
                hum_entity_id,
                temp_entity_id,
                config_entry.title,
                config_entry.entry_id,
                mold_calc,
            ),
            MoldRiskIndexSensor(
                hum_entity_id,
                temp_entity_id,
                config_entry.title,
                config_entry.entry_id,
                mold_calc,
            ),
        ]
    )


class MoldRiskCalculator:
    """ Calculate the limits and risk of mold growth. """
    def __init__(self, hum_entity_id: str, temp_entity_id: str):
        """ Initialize the calculator. """
        self._hum_entity_id = hum_entity_id
        self._temp_entity_id = temp_entity_id
        
        self._last_receiver_event: Event | None = None
        self.humidity: float | None = None
        self.temperature: float | None = None
        self.risk: int | None = None
        self.humidity_limit_level_1: int | None = None
        self.humidity_limit_level_2: int | None = None
        self.humidity_limit_level_3: int | None = None
    
    def calc_limit_1(self, temp: float | int) -> int:
        """ Calculate limit for risk level 1 """
        if 0 <= temp <= 50:
            limit = round(20 * exp( -temp * 0.15 ) + 73)
            return max(min(100,limit),72)
        else:
            return 100
    
    def calc_limit_2(self, temp: float | int) -> int:
        """ Calculate limit for risk level 2 """
        if 0 <= temp <= 50:
            limit = round(17 * exp( -temp * 0.11 ) + 80)
            return max(min(100,limit),79)
        else:
            return 100
        
    def calc_limit_3(self, temp: float | int) -> int:
        """ Calculate limit for risk level 3 """
        if 0 <= temp <= 50:
            limit = round(15 * exp( -temp * 0.10 ) + 85)
            return max(min(100,limit),84)
        else:
            return 100

    @callback
    def async_event_receiver(self, event: Event,) -> None:
        """ Receives events about state changes. """
        if event == self._last_receiver_event:
            return
        self._last_receiver_event = event
        
        state = event.data.get("new_state")
        entity = event.data.get("entity_id")
        
        if (
            state is None
            or state.state is None
            or state.state
            in [
                STATE_UNKNOWN,
                STATE_UNAVAILABLE,
            ]
        ):
            new_state = None
        else:
            try:
                new_state = float(state.state)
            except ValueError:
                _LOGGER.warning(
                    "Only numerical states are supported for input sensors"
                )
                new_state = None

        if entity == self._temp_entity_id:
            if new_state == self.temperature:
                return
            self.temperature = new_state
            self._calc_limit()
            self._calc_risk()
        
        if entity == self._hum_entity_id:
            if not new_state is None and new_state > 100:
                new_state = 100
            if not new_state is None and  new_state < 0:
                new_state = 0
            if new_state == self.humidity:
                return
            self.humidity = new_state
            self._calc_risk()

    @callback
    def _calc_limit(self) -> None:
        """ Calculate limits. """
        # Without temperature no calculations can be done
        if self.temperature is None:
            self.risk = None
            self.humidity_limit_level_1 = None
            self.humidity_limit_level_2 = None
            self.humidity_limit_level_3 = None
            return

        self.humidity_limit_level_1 = self.calc_limit_1(self.temperature)
        self.humidity_limit_level_2 = self.calc_limit_2(self.temperature)
        self.humidity_limit_level_3 = self.calc_limit_3(self.temperature)

    @callback
    def _calc_risk(self) -> None:
        """ Calculate risk. """
        # Without temperature or humidity no calculations can be done
        if self.humidity is None or self.temperature is None:
            self.risk = None
            return

        if self.humidity > self.humidity_limit_level_3:
            # Mold will start grow in less than 4 weeks
            self.risk = 3
        elif self.humidity > self.humidity_limit_level_2:
            # Mold will start grow in 4 to 8 weeks
            self.risk = 2
        elif self.humidity > self.humidity_limit_level_1:
            # Mold will start after 8 weeks or more
            self.risk = 1
        else:
            self.risk = 0


class MoldRiskBaseSensor(SensorEntity):
    """ Base class for mold risk index sensors. """

    _attr_has_entity_name = True
    _attr_should_poll = False
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(
        self,
        hum_entity_id: str,
        temp_entity_id: str,
        name: str,
        entry_id: str,
        mold_calc: MoldRiskCalculator
    ) -> None:
        """ Initialize the base sensor. """
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name=name,
            )
        self._entry_id = entry_id
        self._hum_entity_id = hum_entity_id
        self._temp_entity_id = temp_entity_id
        self._mold_calc = mold_calc


class MoldRiskLimitSensor(MoldRiskBaseSensor):
    """ Representation of a mold risk limit sensor. """
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_icon = "mdi:water-percent-alert"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_name = "Limit"

    _limit_level_1: int | None = None
    _limit_level_2: int | None = None
    _limit_level_3: int | None = None

    async def async_added_to_hass(self) -> None:
        """ Handle added to Hass. """
        state = self.hass.states.get(self._temp_entity_id)
        event = Event("", {"entity_id": self._temp_entity_id, "new_state": state})
        self._async_state_listener(event)
        
        entity_ids = [self._temp_entity_id]
        self.async_on_remove(
            async_track_state_change_event(
                    self.hass, entity_ids, self._async_state_listener
            )
        )
    
    @callback
    def _async_state_listener(self, event: Event) -> None:
        """ Listen for sensor state changes. """
        updated = False
        self._mold_calc.async_event_receiver(event)
        
        if self._mold_calc.humidity_limit_level_1 != self._limit_level_1:
            self._limit_level_1 = self._mold_calc.humidity_limit_level_1
            updated = True
        if self._mold_calc.humidity_limit_level_2 != self._limit_level_2:
            self._limit_level_2 = self._mold_calc.humidity_limit_level_2
            updated = True
        if self._mold_calc.humidity_limit_level_3 != self._limit_level_3:
            self._limit_level_3 = self._mold_calc.humidity_limit_level_3
            updated = True
        
        if updated:
            self.async_write_ha_state()

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """ Return the state attributes of the sensor. """
        return {
            "Level 1 limit": self._limit_level_1,
            "Level 2 limit": self._limit_level_2,
            "Level 3 limit": self._limit_level_3,
        }
    
    @property
    def native_value(self) -> int | None:
        """ Return the state of the sensor. """
        return self._limit_level_1
    
    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return f"{self._entry_id}-limit"


class MoldRiskIndexSensor(MoldRiskBaseSensor):
    """ Representation of a mold risk index sensor. """
    _attr_icon = "mdi:alert-outline"
    _attr_name = "Risk Index"
    
    _risk: int | None = None

    async def async_added_to_hass(self) -> None:
        """ Handle added to Hass. """
        state = self.hass.states.get(self._hum_entity_id)
        event = Event("", {"entity_id": self._hum_entity_id, "new_state": state})
        self._async_state_listener(event)
        state = self.hass.states.get(self._temp_entity_id)
        event = Event("", {"entity_id": self._temp_entity_id, "new_state": state})
        self._async_state_listener(event)
        
        entity_ids = [self._hum_entity_id, self._temp_entity_id]
        self.async_on_remove(
            async_track_state_change_event(
                    self.hass, entity_ids, self._async_state_listener
            )
        )
    
    @callback
    def _async_state_listener(self, event: Event) -> None:
        """ Listen for sensor state changes. """
        self._mold_calc.async_event_receiver(event)
        if self._mold_calc.risk != self._risk:
            self._risk = self._mold_calc.risk
            self.async_write_ha_state()
    
    @property
    def native_value(self) -> int | None:
        """ Return the state of the sensor. """
        return self._risk

    @property
    def unique_id(self) -> str | None:
        """Return a unique ID."""
        return f"{self._entry_id}-index"
