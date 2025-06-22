import logging
from homeassistant.components.light import LightEntity, ColorMode, ATTR_BRIGHTNESS
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Frameo light platform."""
    client = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FrameoScreen(client, entry)], update_before_add=True)

class FrameoScreen(LightEntity):
    """Representation of the Frameo Screen."""
    _attr_should_poll = True
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(self, client, entry: ConfigEntry) -> None:
        self.client = client
        self._attr_name = entry.title
        self._attr_unique_id = f"{entry.entry_id}_screen"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}
        self._attr_is_on = None
        self._attr_brightness = None

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the screen on."""
        if ATTR_BRIGHTNESS in kwargs:
            new_brightness = kwargs[ATTR_BRIGHTNESS]
            await self.client.async_shell(f"settings put system screen_brightness {new_brightness}")
            self._attr_brightness = new_brightness
        
        power_state = await self.client.async_shell("dumpsys power")
        if power_state and "mWakefulness=Asleep" in power_state:
            await self.client.async_shell("input keyevent 26")
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the screen off."""
        power_state = await self.client.async_shell("dumpsys power")
        if power_state and "mWakefulness=Awake" in power_state:
            await self.client.async_shell("input keyevent 26")
        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Fetch the latest state from the device."""
        power_state = await self.client.async_shell("dumpsys power")
        if not power_state:
            self._attr_is_on = None
            return

        self._attr_is_on = "mWakefulness=Awake" in power_state
        for line in power_state.splitlines():
            if "mScreenBrightnessSetting=" in line:
                try:
                    self._attr_brightness = int(line.split("=")[1])
                    break
                except (ValueError, IndexError):
                    pass