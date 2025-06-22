"""Config flow for HA Frameo Control."""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

from .const import (
    CONF_CONN_TYPE,
    CONF_SERIAL,
    CONN_TYPE_NETWORK,
    CONN_TYPE_USB,
    CONF_HOST,
    CONF_PORT,
    DOMAIN,
    LOGGER,
)


class HaFrameoControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Frameo Control."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.discovered_serials: list[str] = []

    async def async_step_user(self, user_input=None):
        """Handle the initial step where the user chooses the connection type."""
        return self.async_show_menu(
            step_id="user",
            menu_options=[CONN_TYPE_NETWORK, CONN_TYPE_USB],
        )

    async def async_step_Network(self, user_input=None):
        """Handle the network connection setup."""
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Frameo ({user_input[CONF_HOST]})",
                data={
                    CONF_CONN_TYPE: CONN_TYPE_NETWORK,
                    CONF_HOST: user_input[CONF_HOST],
                    CONF_PORT: user_input[CONF_PORT],
                },
            )

        return self.async_show_form(step_id="Network", errors=errors)

    async def async_step_USB(self, user_input=None):
        """Scan for USB devices and then proceed to the selection step."""
        LOGGER.info("Scanning for USB devices...")
        client = get_async_client(self.hass, verify_ssl=False)
        url = "http://a0d7b954-frameo_control_addon:5000/devices/usb"
        try:
            response = await client.get(url, timeout=15)
            response.raise_for_status()
            self.discovered_serials = await response.json()
        except Exception as e:
            LOGGER.error("Could not fetch USB devices from add-on: %s", e)
            return self.async_abort(reason="addon_not_running")

        if not self.discovered_serials:
            return self.async_abort(reason="no_devices_found")

        return await self.async_step_usb_select()

    async def async_step_usb_select(self, user_input=None):
        """Handle the USB device selection."""
        errors = {}
        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_SERIAL])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Frameo (USB: {user_input[CONF_SERIAL]})",
                data={
                    CONF_CONN_TYPE: CONN_TYPE_USB,
                    CONF_SERIAL: user_input[CONF_SERIAL],
                },
            )

        return self.async_show_form(
            step_id="usb_select",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SERIAL): SelectSelector(
                        SelectSelectorConfig(options=self.discovered_serials)
                    )
                }
            ),
            errors=errors,
        )