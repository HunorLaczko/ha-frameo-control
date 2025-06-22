import voluptuous as vol
from adb_shell.adb_device_async import AdbDeviceTcpAsync, AdbDeviceUsbAsync
from adb_shell.exceptions import AdbShellError

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from .const import DOMAIN, CONF_CONN_TYPE, CONN_TYPE_NETWORK, CONN_TYPE_USB, CONF_SERIAL

class HaFrameoControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Frameo Control."""
    VERSION = 1

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
            try:
                # Test connection
                device = AdbDeviceTcpAsync(host=user_input[CONF_HOST], port=user_input[CONF_PORT])
                await device.connect(timeout_s=5.0)
                await device.close()
                
                return self.async_create_entry(
                    title=f"Frameo ({user_input[CONF_HOST]})",
                    data={CONF_CONN_TYPE: CONN_TYPE_NETWORK, **user_input},
                )
            except AdbShellError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id=CONN_TYPE_NETWORK,
            data_schema=vol.Schema({
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_PORT, default=5555): int,
            }),
            errors=errors,
        )

    async def async_step_USB(self, user_input=None):
        """Handle the USB connection setup."""
        errors = {}
        if user_input is not None:
            try:
                # Test connection
                device = AdbDeviceUsbAsync(serial=user_input.get(CONF_SERIAL))
                await device.connect(timeout_s=5.0)
                await device.close()

                return self.async_create_entry(
                    title=f"Frameo (USB)",
                    data={CONF_CONN_TYPE: CONN_TYPE_USB, **user_input},
                )
            except AdbShellError:
                errors["base"] = "cannot_connect"
            except Exception:
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id=CONN_TYPE_USB,
            data_schema=vol.Schema({
                vol.Optional(CONF_SERIAL): str,
            }),
            description_placeholders={"docs_url": "https://www.home-assistant.io/integrations/androidtv/#adb-troubleshooting"},
            errors=errors,
        )