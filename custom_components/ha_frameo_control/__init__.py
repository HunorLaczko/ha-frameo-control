"""The HA Frameo Control integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .api import FrameoAddonApiClient
from .const import LOGGER, PLATFORMS
from .coordinator import FrameoDataUpdateCoordinator

type FrameoConfigEntry = ConfigEntry[FrameoDataUpdateCoordinator]


async def async_setup_entry(hass: HomeAssistant, entry: FrameoConfigEntry) -> bool:
    """Set up HA Frameo Control from a config entry."""
    LOGGER.error("Setting up Frameo integration for %s", entry.title)

    api_client = FrameoAddonApiClient(hass)
    coordinator = FrameoDataUpdateCoordinator(hass, api_client, entry.data)
    
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
    LOGGER.error("Unloading Frameo integration for %s", entry.title)
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)