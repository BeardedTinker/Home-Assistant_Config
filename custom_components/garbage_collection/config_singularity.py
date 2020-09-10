"""Genrate configuration that is used by both YAML and config_flow."""

from collections import OrderedDict
from typing import Dict


class config_singularity:
    """Store configuration and generate configs and default values.

    Options is a dictionary (key is the parameter name),
    where each value is a dictionary with following keys
    "step".......in whict config_flow step is this in
    "valid_for"..a function to test for which this option is relevant
    "method".....vol.Optional or vol.Required
    "default"....default value (optional)
    "type".......type
    "validator"..validator
    (Type and validator are somewhat redundant.
    But I cannot use custom validators in ShowForm - it calls convert from
    voluptuous-serialize that does not accept them.
    So I pass it twice - once the type, then the validator.
    Not necesaty for standard validators, such as vol.In()
    For example: "type": str, "validator": cv.string.
    """

    options: Dict = {}

    def __init__(self) -> None:
        """Validate configuration and reset defaults."""
        for _, value in self.options.items():
            if "method" not in value:
                raise KeyError(
                    'config_singularity.options must contain the key "method"'
                )
            if "type" not in value:
                raise KeyError('config_singularity.options must contain the key "type"')
        # Set defaults
        self.reset_defaults()

    @property
    def defaults(self) -> Dict:
        """Return default values."""
        return self._defaults

    def reset_defaults(self) -> None:
        """Reset the defaults from const.py."""
        self._defaults = {}
        items = {
            key: value for (key, value) in self.options.items() if "default" in value
        }
        for key, value in items.items():
            self._defaults[key] = value["default"]

    def compile_config_flow(self, step: int, valid_for=None) -> Dict:
        """Generate configuration options relevant for current step and frequency."""
        result = OrderedDict()
        items = {
            key: value
            for (key, value) in self.options.items()
            if ("step" in value and value["step"] == step)
            and (
                valid_for is None
                or "valid_for" not in value
                or bool(value["valid_for"](valid_for))
            )
        }
        for key, value in items.items():
            if key in self._defaults:
                result[
                    value["method"](
                        key, description={"suggested_value": self._defaults[key]}
                    )
                ] = value["type"]
            else:
                result[value["method"](key)] = value["type"]
        return result

    def compile_schema(self, step: int = None, valid_for=None) -> Dict:
        """For both YAML Scheme (step is None) or config_flow Scheme."""
        result = OrderedDict()
        items = {
            key: value
            for (key, value) in self.options.items()
            if (step is None or ("step" in value and value["step"] == step))
            and (
                valid_for is None
                or "valid_for" not in value
                or bool(value["valid_for"](valid_for))
            )
        }
        for key, value in items.items():
            # use the validator if exists, otherwise the type
            t = value["validator"] if "validator" in value else value["type"]
            if "default" in value:
                result[value["method"](key, default=value["default"])] = t
            else:
                result[value["method"](key)] = t
        return result

    def set_defaults(self, step: int, data) -> None:
        """Generate default values."""
        items = {
            key: value
            for (key, value) in self.options.items()
            if "step" in value and value["step"] == step and key in data
        }
        for key, _ in items.items():
            if data[key] is not None and (
                type(data[key]) not in [list, dict] or len(data[key]) != 0
            ):
                self._defaults[key] = data[key]
