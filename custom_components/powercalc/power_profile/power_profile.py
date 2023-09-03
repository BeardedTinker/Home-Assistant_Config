from __future__ import annotations

import json
import logging
import os
import re
from typing import NamedTuple, Protocol

from awesomeversion.awesomeversion import AwesomeVersion
from homeassistant.const import __version__ as HA_VERSION  # noqa

if AwesomeVersion(HA_VERSION) >= AwesomeVersion("2023.8.0"):
    from enum import StrEnum
else:
    from homeassistant.backports.enum import StrEnum  # pragma: no cover

from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN
from homeassistant.components.camera import DOMAIN as CAMERA_DOMAIN
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.media_player import DOMAIN as MEDIA_PLAYER_DOMAIN
from homeassistant.components.switch import DOMAIN as SWITCH_DOMAIN
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.typing import ConfigType

from custom_components.powercalc.common import SourceEntity
from custom_components.powercalc.const import CONF_POWER, CalculationStrategy
from custom_components.powercalc.errors import (
    ModelNotSupportedError,
    PowercalcSetupError,
    UnsupportedStrategyError,
)

_LOGGER = logging.getLogger(__name__)


class DeviceType(StrEnum):
    CAMERA = "camera"
    LIGHT = "light"
    SMART_SWITCH = "smart_switch"
    SMART_SPEAKER = "smart_speaker"
    NETWORK = "network"


class SubProfileMatcherType(StrEnum):
    ATTRIBUTE = "attribute"
    ENTITY_ID = "entity_id"
    ENTITY_STATE = "entity_state"
    INTEGRATION = "integration"


DEVICE_DOMAINS = {
    DeviceType.CAMERA: CAMERA_DOMAIN,
    DeviceType.LIGHT: LIGHT_DOMAIN,
    DeviceType.SMART_SWITCH: SWITCH_DOMAIN,
    DeviceType.SMART_SPEAKER: MEDIA_PLAYER_DOMAIN,
    DeviceType.NETWORK: BINARY_SENSOR_DOMAIN,
}


class PowerProfile:
    def __init__(
        self,
        hass: HomeAssistant,
        manufacturer: str,
        model: str,
        directory: str,
        json_data: ConfigType,
    ) -> None:
        self._manufacturer = manufacturer
        self._model = model.replace("#slash#", "/")
        self._hass = hass
        self._directory = directory
        self._json_data = json_data
        self.sub_profile: str | None = None
        self._sub_profile_dir: str | None = None

    def get_model_directory(self, root_only: bool = False) -> str:
        """Get the model directory containing the data files."""
        if self.linked_lut:
            return os.path.join(os.path.dirname(__file__), "../data", self.linked_lut)

        if root_only:
            return self._directory

        return self._sub_profile_dir or self._directory

    def supports(self, model: str) -> bool:
        """Check whether this power profile supports a given model ID.
        Also looks at possible aliases.
        """
        model = model.lower().replace("#slash#", "/")

        if self._model.lower() == model:
            return True

        # @todo implement Regex/Json path
        for alias in self.aliases:
            if alias.lower() == model:
                return True

        # Also try to match model ID between parentheses.
        if match := re.search(r"\(([^\(\)]+)\)$", model):
            return self.supports(match.group(1))

        return False

    @property
    def manufacturer(self) -> str:
        return self._manufacturer

    @property
    def model(self) -> str:
        return self._model

    @property
    def name(self) -> str:
        return self._json_data.get("name") or ""

    @property
    def standby_power(self) -> float:
        return self._json_data.get("standby_power") or 0

    @property
    def standby_power_on(self) -> float:
        return self._json_data.get("standby_power_on") or 0

    @property
    def calculation_strategy(self) -> CalculationStrategy:
        """Get the calculation strategy this profile provides.
        supported modes is here for BC purposes.
        """
        if "calculation_strategy" in self._json_data:
            return CalculationStrategy(str(self._json_data.get("calculation_strategy")))
        return CalculationStrategy.LUT

    @property
    def linked_lut(self) -> str | None:
        return self._json_data.get("linked_lut")

    @property
    def calculation_enabled_condition(self) -> str | None:
        return self._json_data.get("calculation_enabled_condition")

    @property
    def aliases(self) -> list[str]:
        return self._json_data.get("aliases") or []

    @property
    def linear_mode_config(self) -> ConfigType | None:
        """Get configuration to setup linear strategy."""
        if not self.is_strategy_supported(CalculationStrategy.LINEAR):
            raise UnsupportedStrategyError(
                f"Strategy linear is not supported by model: {self._model}",
            )
        return self._json_data.get("linear_config")

    @property
    def fixed_mode_config(self) -> ConfigType | None:
        """Get configuration to setup fixed strategy."""
        if not self.is_strategy_supported(CalculationStrategy.FIXED):
            raise UnsupportedStrategyError(
                f"Strategy fixed is not supported by model: {self._model}",
            )
        fixed_config = self._json_data.get("fixed_config")
        if fixed_config is None and self.standby_power_on:
            fixed_config = {CONF_POWER: 0}
        return fixed_config

    @property
    def sensor_config(self) -> ConfigType:
        """Additional sensor configuration."""
        return self._json_data.get("sensor_config") or {}

    def is_strategy_supported(self, mode: CalculationStrategy) -> bool:
        """Whether a certain calculation strategy is supported by this profile."""
        return mode == self.calculation_strategy

    @property
    def needs_fixed_config(self) -> bool:
        """Used for smart switches which only provides standby power values.
        This indicates the user must supply the power values in the config flow.
        """
        return self.is_strategy_supported(
            CalculationStrategy.FIXED,
        ) and not self._json_data.get("fixed_config")

    @property
    def device_type(self) -> DeviceType:
        device_type = self._json_data.get("device_type")
        if not device_type:
            return DeviceType.LIGHT
        return DeviceType(device_type)

    @property
    def config_flow_discovery_remarks(self) -> str | None:
        return self._json_data.get("config_flow_discovery_remarks")

    def get_sub_profiles(self) -> list[str]:
        """Get listing of possible sub profiles."""
        return sorted(next(os.walk(self.get_model_directory(True)))[1])

    @property
    def has_sub_profiles(self) -> bool:
        return len(self.get_sub_profiles()) > 0

    @property
    def sub_profile_select(self) -> SubProfileSelectConfig | None:
        """Get the configuration for automatic sub profile switching."""
        select_dict = self._json_data.get("sub_profile_select")
        if not select_dict:
            return None
        return SubProfileSelectConfig(**select_dict)

    def select_sub_profile(self, sub_profile: str) -> None:
        """Select a sub profile. Only applicable when to profile actually supports sub profiles."""
        if not self.has_sub_profiles:
            return

        # Sub profile already selected, no need to load it again
        if self.sub_profile == sub_profile:
            return

        self._sub_profile_dir = os.path.join(self._directory, sub_profile)
        _LOGGER.debug("Loading sub profile directory %s", sub_profile)
        if not os.path.exists(self._sub_profile_dir):
            raise ModelNotSupportedError(
                f"Sub profile not found (manufacturer: {self._manufacturer}, model: {self._model}, "
                f"sub_profile: {sub_profile})",
            )

        # When the sub LUT directory also has a model.json (not required),
        # merge this json into the main model.json data.
        file_path = os.path.join(self._sub_profile_dir, "model.json")
        if os.path.exists(file_path):
            with open(file_path) as json_file:
                self._json_data = {**self._json_data, **json.load(json_file)}

        self.sub_profile = sub_profile

    def is_entity_domain_supported(self, source_entity: SourceEntity) -> bool:
        """Check whether this power profile supports a given entity domain."""
        entity_entry = source_entity.entity_entry
        if (
            self.device_type == DeviceType.SMART_SWITCH
            and entity_entry
            and entity_entry.platform in ["hue"]
            and source_entity.domain == LIGHT_DOMAIN
        ):  # see https://github.com/bramstroker/homeassistant-powercalc/issues/1491
            return True
        return DEVICE_DOMAINS[self.device_type] == source_entity.domain


class SubProfileSelector:
    def __init__(
        self,
        hass: HomeAssistant,
        config: SubProfileSelectConfig,
        source_entity: SourceEntity,
    ) -> None:
        self._hass = hass
        self._config = config
        self._source_entity = source_entity
        self._matchers: list[SubProfileMatcher] = self._build_matchers()

    def _build_matchers(self) -> list[SubProfileMatcher]:
        matchers: list[SubProfileMatcher] = []
        for matcher_config in self._config.matchers:
            matchers.append(self._create_matcher(matcher_config))
        return matchers

    def select_sub_profile(self, entity_state: State) -> str:
        """Dynamically tries to select a sub profile depending on the entity state.
        This method always need to return a sub profile, when nothing is matched it will return a default.
        """
        for matcher in self._matchers:
            sub_profile = matcher.match(entity_state, self._source_entity)
            if sub_profile:
                return sub_profile

        return self._config.default

    def get_tracking_entities(self) -> list[str]:
        """Get additional list of entities to track for state changes."""
        return [
            entity_id
            for matcher in self._matchers
            for entity_id in matcher.get_tracking_entities()
        ]

    def _create_matcher(self, matcher_config: dict) -> SubProfileMatcher:
        """Create a matcher from json config. Can be extended for more matchers in the future."""
        matcher_type: SubProfileMatcherType = matcher_config["type"]
        if matcher_type == SubProfileMatcherType.ATTRIBUTE:
            return AttributeMatcher(matcher_config["attribute"], matcher_config["map"])
        if matcher_type == SubProfileMatcherType.ENTITY_STATE:
            return EntityStateMatcher(
                self._hass,
                self._source_entity,
                matcher_config["entity_id"],
                matcher_config["map"],
            )
        if matcher_type == SubProfileMatcherType.ENTITY_ID:
            return EntityIdMatcher(matcher_config["pattern"], matcher_config["profile"])
        if matcher_type == SubProfileMatcherType.INTEGRATION:
            return IntegrationMatcher(
                matcher_config["integration"],
                matcher_config["profile"],
            )
        raise PowercalcSetupError(f"Unknown sub profile matcher type: {matcher_type}")


class SubProfileSelectConfig(NamedTuple):
    default: str
    matchers: list[dict]


class SubProfileMatcher(Protocol):
    def match(self, entity_state: State, source_entity: SourceEntity) -> str | None:
        """Returns a sub profile."""

    def get_tracking_entities(self) -> list[str]:
        """Get extra entities to track for state changes."""


class EntityStateMatcher(SubProfileMatcher):
    def __init__(
        self,
        hass: HomeAssistant,
        source_entity: SourceEntity | None,
        entity_id: str,
        mapping: dict[str, str],
    ) -> None:
        self._hass = hass
        if source_entity:
            entity_id = entity_id.replace(
                "{{source_object_id}}",
                source_entity.object_id,
            )
        self._entity_id = entity_id
        self._mapping = mapping

    def match(self, entity_state: State, source_entity: SourceEntity) -> str | None:
        state = self._hass.states.get(self._entity_id)
        if state is None:
            return None

        return self._mapping.get(state.state)

    def get_tracking_entities(self) -> list[str]:
        return [self._entity_id]


class AttributeMatcher(SubProfileMatcher):
    def __init__(self, attribute: str, mapping: dict[str, str]) -> None:
        self._attribute = attribute
        self._mapping = mapping

    def match(self, entity_state: State, source_entity: SourceEntity) -> str | None:
        val = entity_state.attributes.get(self._attribute)
        if val is None:
            return None

        return self._mapping.get(val)

    def get_tracking_entities(self) -> list[str]:
        return []


class EntityIdMatcher(SubProfileMatcher):
    def __init__(self, pattern: str, profile: str) -> None:
        self._pattern = pattern
        self._profile = profile

    def match(self, entity_state: State, source_entity: SourceEntity) -> str | None:
        if re.search(self._pattern, entity_state.entity_id):
            return self._profile

        return None

    def get_tracking_entities(self) -> list[str]:
        return []


class IntegrationMatcher(SubProfileMatcher):
    def __init__(self, integration: str, profile: str) -> None:
        self._integration = integration
        self._profile = profile

    def match(self, entity_state: State, source_entity: SourceEntity) -> str | None:
        registry_entry = source_entity.entity_entry
        if not registry_entry:
            return None

        if registry_entry.platform == self._integration:
            return self._profile

        return None

    def get_tracking_entities(self) -> list[str]:
        return []
