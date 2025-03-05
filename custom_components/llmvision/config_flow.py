from homeassistant import config_entries
from homeassistant.helpers.selector import selector
from homeassistant.exceptions import ServiceValidationError
from .providers import (
    OpenAI,
    AzureOpenAI,
    Anthropic,
    Google,
    Groq,
    LocalAI,
    Ollama,
    AWSBedrock
)
from .const import (
    DOMAIN,
    CONF_OPENAI_API_KEY,
    CONF_AZURE_API_KEY,
    CONF_AZURE_BASE_URL,
    CONF_AZURE_DEPLOYMENT,
    CONF_AZURE_VERSION,
    ENDPOINT_AZURE,
    CONF_ANTHROPIC_API_KEY,
    CONF_GOOGLE_API_KEY,
    CONF_GROQ_API_KEY,
    CONF_LOCALAI_IP_ADDRESS,
    CONF_LOCALAI_PORT,
    CONF_LOCALAI_HTTPS,
    CONF_OLLAMA_IP_ADDRESS,
    CONF_OLLAMA_PORT,
    CONF_OLLAMA_HTTPS,
    CONF_CUSTOM_OPENAI_API_KEY,
    CONF_CUSTOM_OPENAI_ENDPOINT,
    CONF_CUSTOM_OPENAI_DEFAULT_MODEL,
    CONF_RETENTION_TIME,
    CONF_MEMORY_PATHS,
    CONF_MEMORY_STRINGS,
    CONF_SYSTEM_PROMPT,
    CONF_AWS_ACCESS_KEY_ID,
    CONF_AWS_SECRET_ACCESS_KEY,
    CONF_AWS_REGION_NAME,
    CONF_AWS_DEFAULT_MODEL,
    CONF_OPENWEBUI_IP_ADDRESS,
    CONF_OPENWEBUI_PORT,
    CONF_OPENWEBUI_HTTPS,
    CONF_OPENWEBUI_API_KEY,
    CONF_OPENWEBUI_DEFAULT_MODEL,
    ENDPOINT_OPENWEBUI,
    DEFAULT_SYSTEM_PROMPT,
    CONF_TITLE_PROMPT,
    DEFAULT_TITLE_PROMPT,
)
import voluptuous as vol
import os
import logging

_LOGGER = logging.getLogger(__name__)


class llmvisionConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 3
    MINOR_VERSION = 0

    async def handle_provider(self, provider):
        provider_steps = {
            "Timeline": self.async_step_timeline,
            "Memory": self.async_step_memory,
            "Anthropic": self.async_step_anthropic,
            "AWS Bedrock": self.async_step_aws_bedrock,
            "Azure": self.async_step_azure,
            "Custom OpenAI": self.async_step_custom_openai,
            "Google": self.async_step_google,
            "Groq": self.async_step_groq,
            "LocalAI": self.async_step_localai,
            "Ollama": self.async_step_ollama,
            "OpenAI": self.async_step_openai,
            "OpenWebUI": self.async_step_openwebui,
        }

        step_method = provider_steps.get(provider)
        if step_method:
            return await step_method()
        else:
            _LOGGER.error(f"Unknown provider: {provider}")
            return self.async_abort(reason="unknown_provider")

    async def async_step_user(self, user_input=None):
        data_schema = vol.Schema({
            vol.Required("provider", default="Timeline"): selector({
                "select": {
                    # Azure removed until fixed
                    "options": ["Timeline", "Memory", "Anthropic", "AWS Bedrock", "Google", "Groq", "LocalAI", "Ollama", "OpenAI", "OpenWebUI", "Custom OpenAI"],
                    "mode": "dropdown",
                    "sort": False,
                    "custom_value": False
                }
            }),
        })

        if user_input is not None:
            self.init_info = user_input
            provider = user_input["provider"]
            return await self.handle_provider(provider)

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            description_placeholders=user_input
        )

    async def async_step_localai(self, user_input=None):
        data_schema = vol.Schema({
            vol.Required(CONF_LOCALAI_IP_ADDRESS): str,
            vol.Required(CONF_LOCALAI_PORT, default=8080): int,
            vol.Required(CONF_LOCALAI_HTTPS, default=False): bool,
        })

        if self.source == config_entries.SOURCE_RECONFIGURE:
            # load existing configuration and add it to the dialog
            self.init_info = self._get_reconfigure_entry().data
            data_schema = self.add_suggested_values_to_schema(
                data_schema, self.init_info
            )

        if user_input is not None:
            # save provider to user_input
            user_input["provider"] = self.init_info["provider"]
            try:
                localai = LocalAI(self.hass, endpoint={
                    'ip_address': user_input[CONF_LOCALAI_IP_ADDRESS],
                    'port': user_input[CONF_LOCALAI_PORT],
                    'https': user_input[CONF_LOCALAI_HTTPS]
                })
                await localai.validate()
                # add the mode to user_input
                if self.source == config_entries.SOURCE_RECONFIGURE:
                    # we're reconfiguring an existing config
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(),
                        data_updates=user_input,
                    )
                else:
                    # New config entry
                    return self.async_create_entry(title=f"LocalAI ({user_input[CONF_LOCALAI_IP_ADDRESS]})", data=user_input)
            except ServiceValidationError as e:
                _LOGGER.error(f"Validation failed: {e}")
                return self.async_show_form(
                    step_id="localai",
                    data_schema=data_schema,
                    errors={"base": "handshake_failed"}
                )

        return self.async_show_form(
            step_id="localai",
            data_schema=data_schema
        )

    async def async_step_ollama(self, user_input=None):
        data_schema = vol.Schema({
            vol.Required(CONF_OLLAMA_IP_ADDRESS): str,
            vol.Required(CONF_OLLAMA_PORT, default=11434): int,
            vol.Required(CONF_OLLAMA_HTTPS, default=False): bool,
        })

        if self.source == config_entries.SOURCE_RECONFIGURE:
            # load existing configuration and add it to the dialog
            self.init_info = self._get_reconfigure_entry().data
            data_schema = self.add_suggested_values_to_schema(
                data_schema, self.init_info
            )

        if user_input is not None:
            # save provider to user_input
            user_input["provider"] = self.init_info["provider"]
            try:
                ollama = Ollama(self.hass, endpoint={
                    'ip_address': user_input[CONF_OLLAMA_IP_ADDRESS],
                    'port': user_input[CONF_OLLAMA_PORT],
                    'https': user_input[CONF_OLLAMA_HTTPS]
                })
                await ollama.validate()
                # add the mode to user_input
                if self.source == config_entries.SOURCE_RECONFIGURE:
                    # we're reconfiguring an existing config
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(),
                        data_updates=user_input,
                    )
                else:
                    # New config entry
                    return self.async_create_entry(title=f"Ollama ({user_input[CONF_OLLAMA_IP_ADDRESS]})", data=user_input)
            except ServiceValidationError as e:
                _LOGGER.error(f"Validation failed: {e}")
                return self.async_show_form(
                    step_id="ollama",
                    data_schema=data_schema,
                    errors={"base": "handshake_failed"}
                )

        return self.async_show_form(
            step_id="ollama",
            data_schema=data_schema,
        )

    async def async_step_openwebui(self, user_input=None):
        data_schema = vol.Schema({
            vol.Required(CONF_OPENWEBUI_API_KEY): str,
            vol.Required(CONF_OPENWEBUI_DEFAULT_MODEL, default="minicpm-v"): str,
            vol.Required(CONF_OPENWEBUI_IP_ADDRESS): str,
            vol.Required(CONF_OPENWEBUI_PORT, default=3000): int,
            vol.Required(CONF_OPENWEBUI_HTTPS, default=False): bool,
        })

        if self.source == config_entries.SOURCE_RECONFIGURE:
            # load existing configuration and add it to the dialog
            self.init_info = self._get_reconfigure_entry().data
            data_schema = self.add_suggested_values_to_schema(
                data_schema, self.init_info
            )

        if user_input is not None:
            # save provider to user_input
            user_input["provider"] = self.init_info["provider"]
            try:
                endpoint = ENDPOINT_OPENWEBUI.format(
                    ip_address=user_input[CONF_OPENWEBUI_IP_ADDRESS],
                    port=user_input[CONF_OPENWEBUI_PORT],
                    protocol="https" if user_input[CONF_OPENWEBUI_HTTPS] else "http"
                )
                openwebui = OpenAI(hass=self.hass,
                                   api_key=user_input[CONF_OPENWEBUI_API_KEY],
                                   default_model=user_input[CONF_OPENWEBUI_DEFAULT_MODEL],
                                   endpoint={'base_url': endpoint})
                await openwebui.validate()
                # add the mode to user_input
                if self.source == config_entries.SOURCE_RECONFIGURE:
                    # we're reconfiguring an existing config
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(),
                        data_updates=user_input,
                    )
                else:
                    # New config entry
                    return self.async_create_entry(title=f"OpenWebUI ({user_input[CONF_OPENWEBUI_IP_ADDRESS]})", data=user_input)
            except ServiceValidationError as e:
                _LOGGER.error(f"Validation failed: {e}")
                return self.async_show_form(
                    step_id="openwebui",
                    data_schema=data_schema,
                    errors={"base": "handshake_failed"}
                )

        return self.async_show_form(
            step_id="openwebui",
            data_schema=data_schema,
        )

    async def async_step_openai(self, user_input=None):
        data_schema = vol.Schema({
            vol.Required(CONF_OPENAI_API_KEY): str,
        })

        if self.source == config_entries.SOURCE_RECONFIGURE:
            # load existing configuration and add it to the dialog
            self.init_info = self._get_reconfigure_entry().data
            data_schema = self.add_suggested_values_to_schema(
                data_schema, self.init_info
            )

        if user_input is not None:
            # save provider to user_input
            user_input["provider"] = self.init_info["provider"]
            try:
                openai = OpenAI(
                    self.hass, api_key=user_input[CONF_OPENAI_API_KEY])
                await openai.validate()
                # add the mode to user_input
                user_input["provider"] = self.init_info["provider"]
                if self.source == config_entries.SOURCE_RECONFIGURE:
                    # we're reconfiguring an existing config
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(),
                        data_updates=user_input,
                    )
                else:
                    # New config entry
                    return self.async_create_entry(title="OpenAI", data=user_input)
            except ServiceValidationError as e:
                _LOGGER.error(f"Validation failed: {e}")
                return self.async_show_form(
                    step_id="openai",
                    data_schema=data_schema,
                    errors={"base": "handshake_failed"}
                )

        return self.async_show_form(
            step_id="openai",
            data_schema=data_schema,
        )

    async def async_step_azure(self, user_input=None):
        data_schema = vol.Schema({
            vol.Required(CONF_AZURE_API_KEY): str,
            vol.Required(CONF_AZURE_BASE_URL, default="https://domain.openai.azure.com/"): str,
            vol.Required(CONF_AZURE_DEPLOYMENT, default="deployment"): str,
            vol.Required(CONF_AZURE_VERSION, default="2024-10-01-preview"): str,
        })

        if self.source == config_entries.SOURCE_RECONFIGURE:
            # load existing configuration and add it to the dialog
            self.init_info = self._get_reconfigure_entry().data
            data_schema = self.add_suggested_values_to_schema(
                data_schema, self.init_info
            )

        if user_input is not None:
            # save provider to user_input
            user_input["provider"] = self.init_info["provider"]
            try:
                azure = AzureOpenAI(self.hass, api_key=user_input[CONF_AZURE_API_KEY], endpoint={
                    'base_url': ENDPOINT_AZURE,
                    'endpoint': user_input[CONF_AZURE_BASE_URL],
                    'deployment': user_input[CONF_AZURE_DEPLOYMENT],
                    'api_version': user_input[CONF_AZURE_VERSION]
                })
                await azure.validate()
                # add the mode to user_input
                user_input["provider"] = self.init_info["provider"]
                if self.source == config_entries.SOURCE_RECONFIGURE:
                    # we're reconfiguring an existing config
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(),
                        data_updates=user_input,
                    )
                else:
                    # New config entry
                    return self.async_create_entry(title="Azure", data=user_input)
            except ServiceValidationError as e:
                _LOGGER.error(f"Validation failed: {e}")
                return self.async_show_form(
                    step_id="azure",
                    data_schema=data_schema,
                    errors={"base": "handshake_failed"}
                )

        return self.async_show_form(
            step_id="azure",
            data_schema=data_schema,
        )

    async def async_step_anthropic(self, user_input=None):
        data_schema = vol.Schema({
            vol.Required(CONF_ANTHROPIC_API_KEY): str,
        })

        if self.source == config_entries.SOURCE_RECONFIGURE:
            # load existing configuration and add it to the dialog
            self.init_info = self._get_reconfigure_entry().data
            data_schema = self.add_suggested_values_to_schema(
                data_schema, self.init_info
            )

        if user_input is not None:
            # save provider to user_input
            user_input["provider"] = self.init_info["provider"]
            try:
                anthropic = Anthropic(
                    self.hass, api_key=user_input[CONF_ANTHROPIC_API_KEY])
                await anthropic.validate()
                # add the mode to user_input
                user_input["provider"] = self.init_info["provider"]
                if self.source == config_entries.SOURCE_RECONFIGURE:
                    # we're reconfiguring an existing config
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(),
                        data_updates=user_input,
                    )
                else:
                    # New config entry
                    return self.async_create_entry(title="Anthropic Claude", data=user_input)
            except ServiceValidationError as e:
                _LOGGER.error(f"Validation failed: {e}")
                return self.async_show_form(
                    step_id="anthropic",
                    data_schema=data_schema,
                    errors={"base": "empty_api_key"}
                )

        return self.async_show_form(
            step_id="anthropic",
            data_schema=data_schema,
        )

    async def async_step_google(self, user_input=None):
        data_schema = vol.Schema({
            vol.Required(CONF_GOOGLE_API_KEY): str,
        })

        if self.source == config_entries.SOURCE_RECONFIGURE:
            # load existing configuration and add it to the dialog
            self.init_info = self._get_reconfigure_entry().data
            data_schema = self.add_suggested_values_to_schema(
                data_schema, self.init_info
            )

        if user_input is not None:
            # save provider to user_input
            user_input["provider"] = self.init_info["provider"]
            try:
                google = Google(
                    self.hass, api_key=user_input[CONF_GOOGLE_API_KEY])
                await google.validate()
                # add the mode to user_input
                user_input["provider"] = self.init_info["provider"]
                if self.source == config_entries.SOURCE_RECONFIGURE:
                    # we're reconfiguring an existing config
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(),
                        data_updates=user_input,
                    )
                else:
                    # New config entry
                    return self.async_create_entry(title="Google Gemini", data=user_input)
            except ServiceValidationError as e:
                _LOGGER.error(f"Validation failed: {e}")
                return self.async_show_form(
                    step_id="google",
                    data_schema=data_schema,
                    errors={"base": "empty_api_key"}
                )

        return self.async_show_form(
            step_id="google",
            data_schema=data_schema,
        )

    async def async_step_groq(self, user_input=None):
        data_schema = vol.Schema({
            vol.Required(CONF_GROQ_API_KEY): str,
        })

        if self.source == config_entries.SOURCE_RECONFIGURE:
            # load existing configuration and add it to the dialog
            self.init_info = self._get_reconfigure_entry().data
            data_schema = self.add_suggested_values_to_schema(
                data_schema, self.init_info
            )

        if user_input is not None:
            # save provider to user_input
            user_input["provider"] = self.init_info["provider"]
            try:
                groq = Groq(self.hass, api_key=user_input[CONF_GROQ_API_KEY])
                await groq.validate()
                # add the mode to user_input
                user_input["provider"] = self.init_info["provider"]
                if self.source == config_entries.SOURCE_RECONFIGURE:
                    # we're reconfiguring an existing config
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(),
                        data_updates=user_input,
                    )
                else:
                    # New config entry
                    return self.async_create_entry(title="Groq", data=user_input)
            except ServiceValidationError as e:
                _LOGGER.error(f"Validation failed: {e}")
                return self.async_show_form(
                    step_id="groq",
                    data_schema=data_schema,
                    errors={"base": "handshake_failed"}
                )

        return self.async_show_form(
            step_id="groq",
            data_schema=data_schema,
        )

    async def async_step_custom_openai(self, user_input=None):
        data_schema = vol.Schema({
            vol.Required(CONF_CUSTOM_OPENAI_ENDPOINT, default="http://replace.with.your.host.com/v1/chat/completions"): str,
            vol.Required(CONF_CUSTOM_OPENAI_DEFAULT_MODEL, default="gpt-4o-mini"): str,
            vol.Required(CONF_CUSTOM_OPENAI_API_KEY): str,
        })

        if self.source == config_entries.SOURCE_RECONFIGURE:
            # load existing configuration and add it to the dialog
            self.init_info = self._get_reconfigure_entry().data
            data_schema = self.add_suggested_values_to_schema(
                data_schema, self.init_info
            )

        if user_input is not None:
            # save provider to user_input
            user_input["provider"] = self.init_info["provider"]
            try:
                custom_openai = OpenAI(self.hass,
                                       api_key=user_input[CONF_CUSTOM_OPENAI_API_KEY],
                                       endpoint={
                                           'base_url': user_input[CONF_CUSTOM_OPENAI_ENDPOINT]},
                                       default_model=user_input[CONF_CUSTOM_OPENAI_DEFAULT_MODEL],
                                       )
                await custom_openai.validate()
                # add the mode to user_input
                user_input["provider"] = self.init_info["provider"]
                if self.source == config_entries.SOURCE_RECONFIGURE:
                    # we're reconfiguring an existing config
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(),
                        data_updates=user_input,
                    )
                else:
                    # New config entry
                    return self.async_create_entry(title="Custom OpenAI compatible Provider", data=user_input)
            except ServiceValidationError as e:
                _LOGGER.error(f"Validation failed: {e}")
                return self.async_show_form(
                    step_id="custom_openai",
                    data_schema=data_schema,
                    errors={"base": "handshake_failed"}
                )

        return self.async_show_form(
            step_id="custom_openai",
            data_schema=data_schema,
        )

    async def async_step_timeline(self, user_input=None):
        data_schema = vol.Schema({
            vol.Required(CONF_RETENTION_TIME, default=7): int,
        })

        if self.source == config_entries.SOURCE_RECONFIGURE:
            # load existing configuration and add it to the dialog
            self.init_info = self._get_reconfigure_entry().data
            data_schema = self.add_suggested_values_to_schema(
                data_schema, self.init_info
            )

        if user_input is not None:
            user_input["provider"] = self.init_info["provider"]

            try:
                for uid in self.hass.data[DOMAIN]:
                    if 'retention_time' in self.hass.data[DOMAIN][uid]:
                        self.async_abort(reason="already_configured")
            except KeyError:
                # no existing configuration, continue
                pass
            if self.source == config_entries.SOURCE_RECONFIGURE:
                # we're reconfiguring an existing config
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    data_updates=user_input,
                )
            else:
                # New config entry
                return self.async_create_entry(title="LLM Vision Timeline", data=user_input)

        return self.async_show_form(
            step_id="timeline",
            data_schema=data_schema,
        )

    async def async_step_memory(self, user_input=None):
        data_schema = vol.Schema({
            vol.Optional(CONF_MEMORY_PATHS, default="/config/llmvision/memory/example.jpg"): selector({
                "text": {
                    "multiline": False,
                    "multiple": True
                }
            }),
            vol.Optional(CONF_MEMORY_STRINGS, default="This an example"): selector({
                "text": {
                    "multiline": False,
                    "multiple": True
                }
            }),
            vol.Optional(CONF_SYSTEM_PROMPT, default=DEFAULT_SYSTEM_PROMPT): selector({
                "text": {
                    "multiline": True,
                    "multiple": False
                }
            }),
            vol.Optional(CONF_TITLE_PROMPT, default=DEFAULT_TITLE_PROMPT): selector({
                "text": {
                    "multiline": True,
                    "multiple": False
                }
            }),
        })

        if self.source == config_entries.SOURCE_RECONFIGURE:
            # load existing configuration and add it to the dialog
            self.init_info = self._get_reconfigure_entry().data
            data_schema = self.add_suggested_values_to_schema(
                data_schema, self.init_info
            )

        if user_input is not None:
            user_input["provider"] = self.init_info["provider"]

            try:
                for uid in self.hass.data[DOMAIN]:
                    if 'system_prompt' in self.hass.data[DOMAIN][uid]:
                        self.async_abort(reason="already_configured")
            except KeyError:
                # no existing configuration, continue
                pass

            errors = {}
            if len(user_input.get(CONF_MEMORY_PATHS, [])) != len(user_input.get(CONF_MEMORY_STRINGS, [])):
                errors = {"base": "mismatched_lengths"}
            for path in user_input.get(CONF_MEMORY_PATHS, []):
                if not os.path.exists(path):
                    errors = {"base": "invalid_image_path"}
            
            if errors:
                return self.async_show_form(
                    step_id="memory",
                    data_schema=data_schema,
                    errors=errors
                )
            if self.source == config_entries.SOURCE_RECONFIGURE:
                # we're reconfiguring an existing config
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    data_updates=user_input,
                )
            else:
                # New config entry
                return self.async_create_entry(title="LLM Vision Memory", data=user_input)

        return self.async_show_form(
            step_id="memory",
            data_schema=data_schema,
        )

    async def async_step_aws_bedrock(self, user_input=None):
        data_schema = vol.Schema({
            vol.Required(CONF_AWS_REGION_NAME, default="us-east-1"): str,
            vol.Required(CONF_AWS_DEFAULT_MODEL, default="us.amazon.nova-pro-v1:0"): str,
            vol.Required(CONF_AWS_ACCESS_KEY_ID): str,
            vol.Required(CONF_AWS_SECRET_ACCESS_KEY): str,
        })

        if self.source == config_entries.SOURCE_RECONFIGURE:
            # load existing configuration and add it to the dialog
            self.init_info = self._get_reconfigure_entry().data
            data_schema = self.add_suggested_values_to_schema(
                data_schema, self.init_info
            )

        if user_input is not None:
            # save provider to user_input
            user_input["provider"] = self.init_info["provider"]
            try:
                aws_bedrock = AWSBedrock(self.hass,
                                         aws_access_key_id=user_input[CONF_AWS_ACCESS_KEY_ID],
                                         aws_secret_access_key=user_input[CONF_AWS_SECRET_ACCESS_KEY],
                                         aws_region_name=user_input[CONF_AWS_REGION_NAME],
                                         model=user_input[CONF_AWS_DEFAULT_MODEL],
                                         )
                await aws_bedrock.validate()
                # add the mode to user_input
                user_input["provider"] = self.init_info["provider"]
                if self.source == config_entries.SOURCE_RECONFIGURE:
                    # we're reconfiguring an existing config
                    return self.async_update_reload_and_abort(
                        self._get_reconfigure_entry(),
                        data_updates=user_input,
                    )
                else:
                    # New config entry
                    return self.async_create_entry(title="AWS Bedrock Provider", data=user_input)
            except ServiceValidationError as e:
                _LOGGER.error(f"Validation failed: {e}")
                return self.async_show_form(
                    step_id="aws_bedrock",
                    data_schema=data_schema,
                    errors={"base": "handshake_failed"}
                )

        return self.async_show_form(
            step_id="aws_bedrock",
            data_schema=data_schema,
        )

    async def async_step_reconfigure(self, user_input):
        data = self._get_reconfigure_entry().data
        provider = data["provider"]
        return await self.handle_provider(provider)
