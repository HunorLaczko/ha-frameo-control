"""Config flow for HA Frameo Control."""
import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

from .api import FrameoAddonApiClient
from .const import (
    CONF_CONN_TYPE,
    CONF_SERIAL,
    CONN_TYPE_NETWORK,
    CONN_TYPE_USB,
    DOMAIN,
    LOGGER,
)

# Use the logger defined in const.py if you have one, or define it here.


@config_entries.HANDLERS.register(DOMAIN)
class HaFrameoControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Frameo Control."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.api_client = None
        self.discovered_serials: list[str] = []
        self.conn_details: dict = {}

    async def async_step_user(self, user_input=None):
        """Handle the initial step where the user chooses the connection type."""
        # This will show a menu with "USB" and "Network" options.
        return self.async_show_menu(
            step_id="user",
            menu_options=[CONN_TYPE_USB, CONN_TYPE_NETWORK],
        )

    async def async_step_Network(self, user_input=None):
        """Handle the network connection setup."""
        errors = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            
            self.conn_details = {
                CONF_CONN_TYPE: CONN_TYPE_NETWORK,
                CONF_HOST: host,
                CONF_PORT: port,
            }

            # Set a unique ID to prevent configuring the same device twice.
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            # Now, tell the addon to connect.
            self.api_client = FrameoAddonApiClient(self.hass)
            LOGGER.info(f"Telling addon to connect to network device: {host}:{port}")
            connect_result = await self.api_client.async_connect(self.conn_details)

            if connect_result and connect_result.get("status") in ["connected", "already_connected"]:
                return self.async_create_entry(
                    title=f"Frameo ({host})",
                    data=self.conn_details,
                )
            
            LOGGER.error(f"Failed to connect during config flow: {connect_result}")
            errors["base"] = "cannot_connect"

        # Show the form for entering Host and Port
        return self.async_show_form(
            step_id="Network",
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=5555): int,
            }),
            errors=errors,
            description_placeholders={
                "message": "Enter the IP address of your Frameo device. You must enable Wireless ADB on the device first."
            }
        )

    async def async_step_USB(self, user_input=None):
        """Scan for available USB devices before showing the selection form."""
        self.api_client = FrameoAddonApiClient(self.hass)
        
        try:
            LOGGER.info("Config flow: Scanning for USB devices...")
            self.discovered_serials = await self.api_client.async_get_usb_devices()

            if self.discovered_serials is None:
                return self.async_abort(reason="addon_not_running")
            if not self.discovered_serials:
                return self.async_abort(reason="no_devices_found")
            
            LOGGER.info(f"Discovered USB devices: {self.discovered_serials}")
        except Exception as e:
            LOGGER.error("Unexpected error during USB scan: %s", e, exc_info=True)
            return self.async_abort(reason="unknown")

        # If devices are found, move to the selection step
        return await self.async_step_usb_select()

    async def async_step_usb_select(self, user_input=None):
        """Handle the USB device selection and trigger the connection."""
        errors = {}
        if user_input is not None:
            serial = user_input[CONF_SERIAL]
            self.conn_details = {
                CONF_CONN_TYPE: CONN_TYPE_USB,
                CONF_SERIAL: serial,
            }

            # Set the unique ID based on the serial number.
            await self.async_set_unique_id(serial)
            self._abort_if_unique_id_configured()
            
            # The user needs to be ready to approve the connection on the device.
            LOGGER.info(f"Telling addon to connect to USB device: {serial}. Please check device screen.")
            connect_result = await self.api_client.async_connect(self.conn_details)

            if connect_result and connect_result.get("status") in ["connected", "already_connected"]:
                LOGGER.info("Connection successful, creating config entry.")
                return self.async_create_entry(
                    title=f"Frameo (USB: {serial})",
                    data=self.conn_details,
                )
            
            LOGGER.error(f"Failed to connect during config flow: {connect_result}")
            errors["base"] = "cannot_connect_usb"

        # Show the form to the user.
        return self.async_show_form(
            step_id="usb_select",
            data_schema=vol.Schema({
                vol.Required(CONF_SERIAL): SelectSelector(
                    SelectSelectorConfig(options=self.discovered_serials)
                )
            }),
            errors=errors,
            description_placeholders={
                "message": "Select your device from the list. After clicking Submit, **check the Frameo device's screen to 'Allow USB Debugging'**. You have 1 minute to approve it."
            }
        )