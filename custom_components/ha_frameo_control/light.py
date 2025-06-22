"""Light entity for Frameo screen control."""
from homeassistant.components.light import LightEntity, ColorMode, ATTR_BRIGHTNESS
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, LOGGER
from .api import FrameoAddonApiClient

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Set up the Frameo light platform."""
    client: FrameoAddonApiClient = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FrameoScreen(client, entry)], True)

class FrameoScreen(LightEntity):
    _attr_should_poll = True
    _attr_has_entity_name = True
    _attr_name = "Screen"
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, client: FrameoAddonApiClient, entry: ConfigEntry):
        self.client = client
        self.config_data = entry.data
        self._attr_unique_id = f"{entry.entry_id}_screen"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}, "name": entry.title}
        self._attr_available = False

    async def async_turn_on(self, **kwargs) -> None:
        if ATTR_BRIGHTNESS in kwargs:
            new_brightness = kwargs[ATTR_BRIGHTNESS]
            LOGGER.info("Setting Frameo brightness to %s", new_brightness)
            await self.client.async_post_shell(self.config_data, f"settings put system screen_brightness {new_brightness}")
        
        state = await self.client.async_get_state(self.config_data)
        if state and not state.get("is_on"):
            LOGGER.info("Turning on Frameo screen")
            await self.client.async_post_shell(self.config_data, "input keyevent 26")
        
        self.async_schedule_update_ha_state(True)

    async def async_turn_off(self, **kwargs) -> None:
        state = await self.client.async_get_state(self.config_data)
        if state and state.get("is_on"):
            LOGGER.info("Turning off Frameo screen")
            await self.client.async_post_shell(self.config_data, "input keyevent 26")
        
        self.async_schedule_update_ha_state(True)

    async def async_update(self):
        state = await self.client.async_get_state(self.config_data)
        if state and "is_on" in state:
            self._attr_is_on = state.get("is_on")
            self._attr_brightness = state.get("brightness")
            self._attr_available = True
        else:
            self._attr_available = False