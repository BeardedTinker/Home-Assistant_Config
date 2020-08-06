from collections import OrderedDict


class config_singularity:
    """
    Options is a dictionary (key is the parameter name), 
    where each value is a dictionary with following keys
    "step".......in whict config_flow step is this in
    "valid_for"..a function to test for which this option is relevant
    "method".....vol.Optional or vol.Required
    "default"....default value (optional)
    "type".......type
    "validator"..validator
    (Type and validator are somewhat redundant. 
    But I cannot use custom validators in ShowForm - it calls convert from voluptuous-serialize that does not accept them.
    So I pass it twice - once the type, then the validator. Not necesaty for standard validators, such as vol.In()
    For example: "type": str, "validator": cv.string.
    )
    """

    options = {}

    def __init__(self):
        # Validate
        for key, value in self.options.items():
            if "method" not in value:
                raise ('config_singularity.options must contain the key "method"')
            if "type" not in value:
                raise ('config_singularity.options must contain the key "type"')
        # Set defaults
        self.reset_defaults()

    @property
    def defaults(self):
        return self.__defaults

    def reset_defaults(self):
        self.__defaults = {}
        items = {
            key: value for (key, value) in self.options.items() if "default" in value
        }
        for key, value in items.items():
            self.__defaults[key] = value["default"]

    def compile_config_flow(self, step, valid_for=None):
        """
        Generate dictionary with relevant configuration options
        For the current step and relevant for the current frequency
        """
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
            if key in self.__defaults:
                result[
                    value["method"](
                        key, description={"suggested_value": self.__defaults[key]}
                    )
                ] = value["type"]
            else:
                result[value["method"](key)] = value["type"]
        return result

    def compile_schema(self, step=None, valid_for=None):
        """
        For both YAML Scheme (step is None) or config_flow Scheme
        """
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

    def set_defaults(self, step, data) -> None:
        items = {
            key: value
            for (key, value) in self.options.items()
            if "step" in value and value["step"] == step and key in data
        }
        for key, value in items.items():  # pylint: disable=W0612
            if data[key] != None and (
                type(data[key]) not in [list, dict] or len(data[key]) != 0
            ):
                self.__defaults[key] = data[key]
