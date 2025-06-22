"""Light entity for Frameo screen control."""
from homeassistant.components.light import LightEntity, ColorMode, ATTR_BRIGHTNESS
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .api import FrameoAddonApiClient
from . import FrameoConfigEntry


async def async_setup_entry(
    hass: HomeAssistant, entry: FrameoConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the Frameo light platform."""
    client = entry.runtime_data
    async_add_entities([FrameoScreen(client, entry)], True)


class FrameoScreen(LightEntity):
    _attr_should_poll = True
    _attr_has_entity_name = True
    _attr_name = "Screen"
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, client: FrameoAddonApiClient, entry: FrameoConfigEntry):
        """Initialize the light."""
        self.client = client
        self._attr_unique_id = f"{entry.entry_id}_screen"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
        }
        self._attr_is_on = None
        self._attr_brightness = None
        self._attr_available = False

    async def async_turn_on(self, **kwargs):
        """Turn the screen on."""
        LOGGER.error("Turning on Frameo screen for '%s'", self.name)
        if ATTR_BRIGHTNESS in kwargs:
            new_brightness = kwargs[ATTR_BRIGHTNESS]
            LOGGER.error("Setting Frameo brightness to %s", new_brightness)
            await self.client.async_post_shell(f"settings put system screen_brightness {new_brightness}")

        state = await self.client.async_get_state()
        if state and not state.get("is_on"):
            await self.client.async_post_shell("input keyevent 26")

        self.async_schedule_update_ha_state(True)

    async def async_turn_off(self, **kwargs):
        """Turn the screen off."""
        LOGGER.error("Turning off Frameo screen for '%s'", self.name)
        state = await self.client.async_get_state()
        if state and state.get("is_on"):
            await self.client.async_post_shell("input keyevent 26")

        self.async_schedule_update_ha_state(True)

    async def async_update(self):
        """Fetch the latest state from the device."""
        LOGGER.error("Updating Frameo screen state for '%s'", self.name)
        state = await self.client.async_get_state()
        if state and "is_on" in state:
            self._attr_is_on = state.get("is_on")
            self._attr_brightness = state.get("brightness")
            self._attr_available = True
        else:
            self._attr_available = False

