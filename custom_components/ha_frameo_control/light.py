"""Light entity for Frameo screen control."""
from homeassistant.components.light import LightEntity, ColorMode, ATTR_BRIGHTNESS
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER
from .coordinator import FrameoDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the Frameo light platform."""
    coordinator: FrameoDataUpdateCoordinator = entry.runtime_data
    async_add_entities([FrameoScreen(coordinator, entry)])

class FrameoScreen(CoordinatorEntity[FrameoDataUpdateCoordinator], LightEntity):
    _attr_has_entity_name = True
    _attr_name = "Screen"
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, coordinator: FrameoDataUpdateCoordinator, entry: ConfigEntry):
        """Initialize the light."""
        super().__init__(coordinator)
        self.client = coordinator.client
        self._attr_unique_id = f"{entry.entry_id}_screen"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
        }
    
    @property
    def is_on(self) -> bool | None:
        """Return true if the light is on."""
        return self.coordinator.data.get("is_on")

    @property
    def brightness(self) -> int | None:
        """Return the brightness of this light between 0..255."""
        return self.coordinator.data.get("brightness")

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the screen on."""
        if ATTR_BRIGHTNESS in kwargs:
            new_brightness = kwargs[ATTR_BRIGHTNESS]
            LOGGER.info("Setting Frameo brightness to %s", new_brightness)
            await self.client.async_post_shell(f"settings put system screen_brightness {new_brightness}")
        
        if not self.is_on:
            LOGGER.info("Turning on Frameo screen")
            await self.client.async_post_shell("input keyevent 26")
        
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the screen off."""
        if self.is_on:
            LOGGER.info("Turning off Frameo screen")
            await self.client.async_post_shell("input keyevent 26")
        
        await self.coordinator.async_request_refresh()