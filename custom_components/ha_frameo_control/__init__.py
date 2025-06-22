"""The HA Frameo Control integration."""
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, PLATFORMS, LOGGER
from .api import FrameoAddonApiClient

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA Frameo Control from a config entry."""
    api_client = FrameoAddonApiClient(hass)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = api_client
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok