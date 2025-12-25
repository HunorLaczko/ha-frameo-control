"""Config flow for HA Frameo Control."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
)

from .api import FrameoAddonApiClient, FrameoApiError
from .const import (
    CONF_ADDON_HOST,
    CONF_ADDON_PORT,
    CONF_CONN_TYPE,
    CONF_SCREEN_HEIGHT,
    CONF_SCREEN_WIDTH,
    CONF_SERIAL,
    DEFAULT_ADDON_HOST,
    DEFAULT_ADDON_PORT,
    DEFAULT_DEVICE_PORT,
    DEFAULT_SCREEN_HEIGHT,
    DEFAULT_SCREEN_WIDTH,
    DOMAIN,
    LOGGER,
    ConnectionType,
)

# Valid connection statuses from the addon
_CONNECTED_STATUSES = frozenset({"connected", "already_connected"})


class FrameoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for HA Frameo Control."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._api_client: FrameoAddonApiClient | None = None
        self._discovered_serials: list[str] = []
        self._conn_details: dict[str, Any] = {}
        self._addon_host: str = DEFAULT_ADDON_HOST
        self._addon_port: int = DEFAULT_ADDON_PORT

    def _get_api_client(self) -> FrameoAddonApiClient:
        """Get or create the API client with current addon settings."""
        if self._api_client is None:
            self._api_client = FrameoAddonApiClient(
                self.hass,
                host=self._addon_host,
                port=self._addon_port,
            )
        return self._api_client

    def _reset_api_client(self) -> None:
        """Reset the API client to force recreation with new settings."""
        self._api_client = None

    async def _async_try_connect(self) -> bool:
        """Attempt to connect to the device.

        Returns:
            True if connection was successful.

        """
        try:
            result = await self._get_api_client().async_connect(self._conn_details)
            return result.get("status") in _CONNECTED_STATUSES
        except FrameoApiError as err:
            LOGGER.error("Connection failed: %s", err)
            return False

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step to configure addon connection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._addon_host = user_input[CONF_ADDON_HOST]
            self._addon_port = int(user_input[CONF_ADDON_PORT])
            self._reset_api_client()

            # Test connection to the addon
            try:
                await self._get_api_client().async_get_usb_devices()
                # Connection successful, proceed to connection type selection
                return await self.async_step_connection_type()
            except FrameoApiError:
                errors["base"] = "addon_not_running"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ADDON_HOST, default=self._addon_host): TextSelector(),
                    vol.Required(CONF_ADDON_PORT, default=self._addon_port): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=65535,
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_connection_type(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the step where the user chooses the connection type."""
        return self.async_show_menu(
            step_id="connection_type",
            menu_options=[ConnectionType.USB, ConnectionType.NETWORK],
        )

    async def async_step_Network(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the network connection setup."""
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]

            self._conn_details = {
                CONF_CONN_TYPE: ConnectionType.NETWORK,
                CONF_HOST: host,
                CONF_PORT: port,
                CONF_ADDON_HOST: self._addon_host,
                CONF_ADDON_PORT: self._addon_port,
            }

            # Set unique ID to prevent duplicate configurations
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            LOGGER.info("Connecting to network device: %s:%s", host, port)

            if await self._async_try_connect():
                return self.async_create_entry(
                    title=f"Frameo ({host})",
                    data=self._conn_details,
                )

            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="Network",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST): str,
                    vol.Required(CONF_PORT, default=DEFAULT_DEVICE_PORT): int,
                }
            ),
            errors=errors,
            description_placeholders={
                "message": (
                    "Enter the IP address of your Frameo device. "
                    "You must enable Wireless ADB on the device first."
                )
            },
        )

    async def async_step_USB(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Scan for available USB devices before showing the selection form."""
        try:
            LOGGER.info("Scanning for USB devices")
            self._discovered_serials = await self._get_api_client().async_get_usb_devices()

            if not self._discovered_serials:
                return self.async_abort(reason="no_devices_found")

            LOGGER.info("Discovered USB devices: %s", self._discovered_serials)

        except FrameoApiError:
            return self.async_abort(reason="addon_not_running")
        except Exception:
            LOGGER.exception("Unexpected error during USB scan")
            return self.async_abort(reason="unknown")

        return await self.async_step_usb_select()

    async def async_step_usb_select(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the USB device selection and trigger the connection."""
        errors: dict[str, str] = {}

        if user_input is not None:
            serial = user_input[CONF_SERIAL]
            self._conn_details = {
                CONF_CONN_TYPE: ConnectionType.USB,
                CONF_SERIAL: serial,
                CONF_ADDON_HOST: self._addon_host,
                CONF_ADDON_PORT: self._addon_port,
            }

            # Set unique ID based on serial number
            await self.async_set_unique_id(serial)
            self._abort_if_unique_id_configured()

            LOGGER.info(
                "Connecting to USB device: %s (check device screen for approval)",
                serial,
            )

            if await self._async_try_connect():
                LOGGER.info("Connection successful, creating config entry")
                return self.async_create_entry(
                    title=f"Frameo (USB: {serial})",
                    data=self._conn_details,
                )

            errors["base"] = "cannot_connect_usb"

        return self.async_show_form(
            step_id="usb_select",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_SERIAL): SelectSelector(
                        SelectSelectorConfig(options=self._discovered_serials)
                    )
                }
            ),
            errors=errors,
            description_placeholders={
                "message": (
                    "Select your device from the list. After clicking Submit, "
                    "check the Frameo device's screen to 'Allow USB Debugging'. "
                    "You have 1 minute to approve it."
                )
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return FrameoOptionsFlowHandler()


class FrameoOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Frameo Control."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Convert numeric values to proper types (NumberSelector returns floats)
            processed_input = {
                **user_input,
                CONF_ADDON_PORT: int(user_input.get(CONF_ADDON_PORT, DEFAULT_ADDON_PORT)),
                CONF_SCREEN_WIDTH: int(user_input.get(CONF_SCREEN_WIDTH, DEFAULT_SCREEN_WIDTH)),
                CONF_SCREEN_HEIGHT: int(user_input.get(CONF_SCREEN_HEIGHT, DEFAULT_SCREEN_HEIGHT)),
            }
            return self.async_create_entry(title="", data=processed_input)

        # Get current values - check options first, then data (from initial config), then defaults
        current_options = self.config_entry.options
        current_data = self.config_entry.data

        def get_value(key: str, default: Any) -> Any:
            """Get value from options, then data, then default."""
            return current_options.get(key, current_data.get(key, default))

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_ADDON_HOST,
                        default=get_value(CONF_ADDON_HOST, DEFAULT_ADDON_HOST),
                    ): TextSelector(),
                    vol.Optional(
                        CONF_ADDON_PORT,
                        default=get_value(CONF_ADDON_PORT, DEFAULT_ADDON_PORT),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=1,
                            max=65535,
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional(
                        CONF_SCREEN_WIDTH,
                        default=current_options.get(CONF_SCREEN_WIDTH, DEFAULT_SCREEN_WIDTH),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=100,
                            max=4096,
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                    vol.Optional(
                        CONF_SCREEN_HEIGHT,
                        default=current_options.get(CONF_SCREEN_HEIGHT, DEFAULT_SCREEN_HEIGHT),
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=100,
                            max=4096,
                            mode=NumberSelectorMode.BOX,
                        )
                    ),
                }
            ),
            errors=errors,
        )