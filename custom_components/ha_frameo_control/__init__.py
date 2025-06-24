"""The HA Frameo Control integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .api import FrameoAddonApiClient
from .const import LOGGER, PLATFORMS
from .coordinator import FrameoDataUpdateCoordinator

type FrameoConfigEntry = ConfigEntry[FrameoDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: FrameoConfigEntry) -> bool:
    """Set up HA Frameo Control from a config entry."""
    LOGGER.info("Setting up Frameo integration for %s", entry.title)

    api_client = FrameoAddonApiClient(hass)

    # On every startup, explicitly tell the addon to connect using the stored config data.
    LOGGER.info("Attempting to establish connection with the Frameo addon...")
    connect_result = await api_client.async_connect(entry.data)

    # Check if the initial connection was successful.
    if not connect_result or connect_result.get("status") not in ["connected", "already_connected"]:
        # If it fails, we raise ConfigEntryNotReady. Home Assistant will automatically
        # try to set up the integration again later.
        raise ConfigEntryNotReady(f"Initial connection to Frameo device failed: {connect_result}")

    LOGGER.info("Connection successful. Initializing coordinator.")

    coordinator = FrameoDataUpdateCoordinator(hass, api_client)
    
    # Fetch initial data so we have it before entities are set up
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_update_listener))
    return True


async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: FrameoConfigEntry) -> bool:
    """Unload a config entry."""
    LOGGER.info("Unloading Frameo integration for %s", entry.title)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)