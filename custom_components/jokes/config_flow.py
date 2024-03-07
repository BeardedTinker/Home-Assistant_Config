"""Config flow for Jokes integration."""

from .const import DOMAIN
from homeassistant import config_entries

@config_entries.HANDLERS.register(DOMAIN)
class JokesFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Jokes."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_CLOUD_POLL

    async def async_step_user(self, user_input=None):
        """Show config Form step."""
        return self.async_create_entry(
            title="jokes config",
            data={},
        )