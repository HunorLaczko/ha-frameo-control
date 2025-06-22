import voluptuous as vol
from adb_shell.adb_device import AdbDeviceUsb
from adb_shell.adb_device_async import AdbDeviceTcpAsync
from adb_shell.exceptions import AdbShellError, UsbDeviceNotFoundError

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, CONF_PORT
from .const import DOMAIN, CONF_CONN_TYPE, CONN_TYPE_NETWORK, CONN_TYPE_USB, CONF_SERIAL

async def _test_connection_usb(hass: HomeAssistant, serial: str | None) -> bool:
    """Test the USB ADB connection in an executor job."""
    def test_sync_usb():
        """Synchronous USB test."""
        device = AdbDeviceUsb(serial=serial)
        device.connect(timeout_s=5.0)
        device.close()
        return True
    
    return await hass.async_add_executor_job(test_sync_usb)


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
                await _test_connection_usb(self.hass, user_input.get(CONF_SERIAL))
                return self.async_create_entry(
                    title="Frameo (USB)",
                    data={CONF_CONN_TYPE: CONN_TYPE_USB, **user_input},
                )
            except (UsbDeviceNotFoundError, AdbShellError):
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