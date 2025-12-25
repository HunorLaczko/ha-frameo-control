"""The HA Frameo Control integration."""
from __future__ import annotations

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.exceptions import ConfigEntryNotReady, HomeAssistantError
from homeassistant.helpers import config_validation as cv

from .api import FrameoAddonApiClient, FrameoApiError
from .const import (
    ATTR_COMMAND,
    ATTR_RESULT,
    CONF_ADDON_HOST,
    CONF_ADDON_PORT,
    CONF_SCREEN_HEIGHT,
    CONF_SCREEN_WIDTH,
    DEFAULT_ADDON_HOST,
    DEFAULT_ADDON_PORT,
    DEFAULT_SCREEN_HEIGHT,
    DEFAULT_SCREEN_WIDTH,
    DOMAIN,
    EVENT_ADB_RESPONSE,
    LOGGER,
    PLATFORMS,
    SERVICE_RUN_ADB_COMMAND,
)
from .coordinator import FrameoDataUpdateCoordinator

type FrameoConfigEntry = ConfigEntry[FrameoDataUpdateCoordinator]

# Valid connection statuses from the addon
_CONNECTED_STATUSES = frozenset({"connected", "already_connected"})

# Service schema
SERVICE_RUN_ADB_COMMAND_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_COMMAND): cv.string,
    }
)


async def async_setup_entry(hass: HomeAssistant, entry: FrameoConfigEntry) -> bool:
    """Set up HA Frameo Control from a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry being set up.

    Returns:
        True if setup was successful.

    Raises:
        ConfigEntryNotReady: If the device connection fails.

    """
    LOGGER.info("Setting up Frameo integration for %s", entry.title)

    # Get addon connection settings - check options first, then data, then defaults
    # (options takes precedence if user has reconfigured, otherwise use initial config data)
    addon_host = entry.options.get(
        CONF_ADDON_HOST,
        entry.data.get(CONF_ADDON_HOST, DEFAULT_ADDON_HOST)
    )
    addon_port = entry.options.get(
        CONF_ADDON_PORT,
        entry.data.get(CONF_ADDON_PORT, DEFAULT_ADDON_PORT)
    )

    # Get screen resolution settings from options or use defaults
    screen_width = entry.options.get(CONF_SCREEN_WIDTH, DEFAULT_SCREEN_WIDTH)
    screen_height = entry.options.get(CONF_SCREEN_HEIGHT, DEFAULT_SCREEN_HEIGHT)

    api_client = FrameoAddonApiClient(hass, host=addon_host, port=addon_port)

    # Establish connection with the device via the addon
    LOGGER.debug("Attempting to establish connection with the Frameo addon at %s:%s", addon_host, addon_port)
    try:
        connect_result = await api_client.async_connect(dict(entry.data))
    except FrameoApiError as err:
        raise ConfigEntryNotReady(f"Failed to connect to Frameo addon: {err}") from err

    if not connect_result or connect_result.get("status") not in _CONNECTED_STATUSES:
        raise ConfigEntryNotReady(
            f"Initial connection to Frameo device failed: {connect_result}"
        )

    LOGGER.info("Connection successful, initializing coordinator")

    coordinator = FrameoDataUpdateCoordinator(
        hass,
        api_client,
        conn_details=dict(entry.data),
        configured_width=screen_width,
        configured_height=screen_height,
    )

    # Fetch initial data before entities are set up
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # Register services
    await _async_setup_services(hass, entry)

    return True


async def _async_setup_services(hass: HomeAssistant, entry: FrameoConfigEntry) -> None:
    """Set up integration services.

    Args:
        hass: Home Assistant instance.
        entry: Config entry.

    """
    async def handle_run_adb_command(call: ServiceCall) -> ServiceResponse:
        """Handle the run_adb_command service call.

        Args:
            call: Service call data.

        Returns:
            Service response with command output.

        """
        command = call.data[ATTR_COMMAND]
        coordinator: FrameoDataUpdateCoordinator = entry.runtime_data

        LOGGER.info("Running custom ADB command: %s", command)

        try:
            result = await coordinator.async_execute_command(command)
            output = result.get("result", "") if result else ""

            # Fire an event so users can capture the response in automations
            hass.bus.async_fire(
                EVENT_ADB_RESPONSE,
                {
                    ATTR_COMMAND: command,
                    ATTR_RESULT: output,
                },
            )

            return {
                "command": command,
                "result": output,
                "success": True,
            }
        except FrameoApiError as err:
            LOGGER.error("ADB command failed: %s", err)
            raise HomeAssistantError(f"ADB command failed: {err}") from err

    # Only register if not already registered
    if not hass.services.has_service(DOMAIN, SERVICE_RUN_ADB_COMMAND):
        hass.services.async_register(
            DOMAIN,
            SERVICE_RUN_ADB_COMMAND,
            handle_run_adb_command,
            schema=SERVICE_RUN_ADB_COMMAND_SCHEMA,
            supports_response=SupportsResponse.OPTIONAL,
        )


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update by reloading the integration.

    Args:
        hass: Home Assistant instance.
        entry: Config entry that was updated.

    """
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: FrameoConfigEntry) -> bool:
    """Unload a config entry.

    Args:
        hass: Home Assistant instance.
        entry: Config entry being unloaded.

    Returns:
        True if unload was successful.

    """
    LOGGER.info("Unloading Frameo integration for %s", entry.title)

    # Unregister services if this is the last config entry
    if len(hass.config_entries.async_entries(DOMAIN)) == 1:
        hass.services.async_remove(DOMAIN, SERVICE_RUN_ADB_COMMAND)

    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)