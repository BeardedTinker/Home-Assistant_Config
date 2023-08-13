from __future__ import annotations

from homeassistant.const import CONF_CONDITION
from homeassistant.core import HomeAssistant
from homeassistant.helpers import condition
from homeassistant.helpers.template import Template
from homeassistant.helpers.typing import ConfigType

from custom_components.powercalc.common import SourceEntity
from custom_components.powercalc.const import (
    CONF_COMPOSITE,
    CONF_FIXED,
    CONF_LINEAR,
    CONF_PLAYBOOK,
    CONF_POWER,
    CONF_POWER_TEMPLATE,
    CONF_STANDBY_POWER,
    CONF_STATES_POWER,
    CONF_WLED,
    CalculationStrategy,
)
from custom_components.powercalc.errors import (
    StrategyConfigurationError,
    UnsupportedStrategyError,
)
from custom_components.powercalc.power_profile.power_profile import PowerProfile

from .composite import CompositeStrategy, SubStrategy
from .fixed import FixedStrategy
from .linear import LinearStrategy
from .lut import LutRegistry, LutStrategy
from .playbook import PlaybookStrategy
from .selector import detect_calculation_strategy
from .strategy_interface import PowerCalculationStrategyInterface
from .wled import WledStrategy


class PowerCalculatorStrategyFactory:
    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._lut_registry = LutRegistry()

    async def create(
        self,
        config: dict,
        strategy: str,
        power_profile: PowerProfile | None,
        source_entity: SourceEntity,
    ) -> PowerCalculationStrategyInterface:
        """Create instance of calculation strategy based on configuration."""
        if strategy == CalculationStrategy.LINEAR:
            return self._create_linear(source_entity, config, power_profile)

        if strategy == CalculationStrategy.FIXED:
            return self._create_fixed(source_entity, config, power_profile)

        if strategy == CalculationStrategy.LUT:
            return self._create_lut(source_entity, power_profile)

        if strategy == CalculationStrategy.PLAYBOOK:
            return self._create_playbook(config)

        if strategy == CalculationStrategy.WLED:
            return self._create_wled(source_entity, config)

        if strategy == CalculationStrategy.COMPOSITE:
            return await self._create_composite(config, power_profile, source_entity)

        raise UnsupportedStrategyError("Invalid calculation mode", strategy)

    def _create_linear(
        self,
        source_entity: SourceEntity,
        config: dict,
        power_profile: PowerProfile | None,
    ) -> LinearStrategy:
        """Create the linear strategy."""
        linear_config = config.get(CONF_LINEAR)

        if linear_config is None:
            if power_profile and power_profile.linear_mode_config:
                linear_config = power_profile.linear_mode_config
            else:
                raise StrategyConfigurationError("No linear configuration supplied")

        return LinearStrategy(
            linear_config,
            self._hass,
            source_entity,
            config.get(CONF_STANDBY_POWER),
        )

    def _create_fixed(
        self,
        source_entity: SourceEntity,
        config: dict,
        power_profile: PowerProfile | None,
    ) -> FixedStrategy:
        """Create the fixed strategy."""
        fixed_config = config.get(CONF_FIXED)
        if fixed_config is None:
            if power_profile and power_profile.fixed_mode_config:
                fixed_config = power_profile.fixed_mode_config
            else:
                raise StrategyConfigurationError("No fixed configuration supplied")

        power = fixed_config.get(CONF_POWER)
        if power is None:
            power = fixed_config.get(CONF_POWER_TEMPLATE)
        if isinstance(power, Template):
            power.hass = self._hass

        states_power: dict = fixed_config.get(CONF_STATES_POWER)  # type: ignore
        if states_power:
            for p in states_power.values():
                if isinstance(p, Template):
                    p.hass = self._hass

        return FixedStrategy(source_entity, power, states_power)

    def _create_lut(
        self,
        source_entity: SourceEntity,
        power_profile: PowerProfile | None,
    ) -> LutStrategy:
        """Create the lut strategy."""
        if power_profile is None:
            raise StrategyConfigurationError(
                "You must supply a valid manufacturer and model to use the LUT mode",
            )

        return LutStrategy(source_entity, self._lut_registry, power_profile)

    def _create_wled(self, source_entity: SourceEntity, config: dict) -> WledStrategy:
        """Create the WLED strategy."""
        if CONF_WLED not in config:
            raise StrategyConfigurationError("No WLED configuration supplied")

        return WledStrategy(
            config=config.get(CONF_WLED),  # type: ignore
            light_entity=source_entity,
            hass=self._hass,
            standby_power=config.get(CONF_STANDBY_POWER),
        )

    def _create_playbook(self, config: ConfigType) -> PlaybookStrategy:
        if CONF_PLAYBOOK not in config:
            raise StrategyConfigurationError("No Playbook configuration supplied")

        playbook_config = config.get(CONF_PLAYBOOK)
        return PlaybookStrategy(self._hass, playbook_config)  # type: ignore

    async def _create_composite(
        self,
        config: ConfigType,
        power_profile: PowerProfile | None,
        source_entity: SourceEntity,
    ) -> CompositeStrategy:
        sub_strategies = list(config.get(CONF_COMPOSITE))  # type: ignore

        async def _create_sub_strategy(strategy_config: ConfigType) -> SubStrategy:
            condition_instance = None
            condition_config = strategy_config.get(CONF_CONDITION)
            if condition_config:
                condition_instance = await condition.async_from_config(
                    self._hass,
                    condition_config,
                )

            strategy = detect_calculation_strategy(strategy_config, power_profile)
            strategy_instance = await self.create(
                strategy_config,
                strategy,
                power_profile,
                source_entity,
            )
            return SubStrategy(condition_config, condition_instance, strategy_instance)

        strategies = [await _create_sub_strategy(config) for config in sub_strategies]
        return CompositeStrategy(self._hass, strategies)
