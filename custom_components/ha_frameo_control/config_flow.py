import voluptuous as vol
from adb_shell.adb_device import AdbDeviceUsb
from adb_shell.adb_device_async import AdbDeviceTcpAsync
from adb_shell.exceptions import (
    AdbConnectionError,
    AdbTimeoutError,
    TcpTimeoutException,
    UsbDeviceNotFoundError,
)

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

from .const import (
    CONF_CONN_TYPE,
    CONF_SERIAL,
    CONN_TYPE_NETWORK,
    CONN_TYPE_USB,
    DOMAIN,
    LOGGER,
)

async def _find_usb_devices(hass: HomeAssistant) -> list[str]:
    """Scan for and return a list of serial numbers for connected USB ADB devices."""
    def find_sync():
        """Synchronous USB device scan."""
        try:
            devices = AdbDeviceUsb.find_all()
            serials = [dev.serial for dev in devices]
            LOGGER.error("Discovered USB devices with serials: %s", serials)
            return serials
        except UsbDeviceNotFoundError:
            LOGGER.error("No USB devices found by adb-shell library.")
            return []
    
    return await hass.async_add_executor_job(find_sync)


class HaFrameoControlConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Frameo Control."""
    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.discovered_serials: list[str] = []

    async def async_step_user(self, user_input=None):
        """Handle the initial step where the user chooses the connection type."""
        LOGGER.error("Starting config flow: user step")
        return self.async_show_menu(
            step_id="user",
            menu_options=[CONN_TYPE_NETWORK, CONN_TYPE_USB],
        )

    async def async_step_Network(self, user_input=None):
        """Handle the network connection setup."""
        LOGGER.error("Config flow: network step")
        errors = {}
        if user_input is not None:
            LOGGER.error("User provided network input: %s", user_input)
            await self.async_set_unique_id(user_input[CONF_HOST])
            self._abort_if_unique_id_configured()

            try:
                LOGGER.error(
                    "Testing network connection to %s:%s",
                    user_input[CONF_HOST],
                    user_input[CONF_PORT],
                )
                device = AdbDeviceTcpAsync(
                    host=user_input[CONF_HOST], port=user_input[CONF_PORT]
                )
                await device.connect(transport_timeout_s=5.0)
                await device.close()
                LOGGER.error("Network connection test successful")

                return self.async_create_entry(
                    title=f"Frameo ({user_input[CONF_HOST]})",
                    data={CONF_CONN_TYPE: CONN_TYPE_NETWORK, **user_input},
                )
            except (AdbConnectionError, AdbTimeoutError, TcpTimeoutException) as e:
                LOGGER.error("Could not connect via network: %s", e)
                errors["base"] = "cannot_connect"
            except Exception as e:
                LOGGER.error("An unknown error occurred during network setup: %s", e)
                errors["base"] = "unknown"

        LOGGER.error("Showing network configuration form")
        return self.async_show_form(step_id="Network", errors=errors)


    async def async_step_USB(self, user_input=None):
        """This step scans for USB devices and then proceeds to the selection step."""
        LOGGER.error("Config flow: USB step - scanning for devices")
        self.discovered_serials = await _find_usb_devices(self.hass)
        
        if not self.discovered_serials:
            # Show an error on the menu step if no devices are found
            return self.async_show_menu(
                step_id="user",
                menu_options=[CONN_TYPE_NETWORK, CONN_TYPE_USB],
                errors={"base": "no_devices_found"}
            )
        
        # If devices are found, move to the selection step
        return await self.async_step_usb_select()

    async def async_step_usb_select(self, user_input=None):
        """Handle the USB device selection."""
        LOGGER.error("Config flow: USB selection step")
        errors = {}
        
        if user_input is not None:
            LOGGER.error("User selected USB serial: %s", user_input[CONF_SERIAL])
            await self.async_set_unique_id(user_input[CONF_SERIAL])
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=f"Frameo (USB: {user_input[CONF_SERIAL]})",
                data={CONF_CONN_TYPE: CONN_TYPE_USB, **user_input},
            )

        LOGGER.error("Showing USB device selection form with devices: %s", self.discovered_serials)
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