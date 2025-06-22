"""Config flow for HA Frameo Control."""
from homeassistant import config_entries
from .const import DOMAIN, LOGGER

@config_entries.HANDLERS.register(DOMAIN)
class HaFrameoControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Frameo Control."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        # Allow only a single instance of the integration.
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        LOGGER.info("Creating Frameo Control integration entry. The backend add-on must be configured and running.")
        return self.async_create_entry(title="Frameo Control", data={})
