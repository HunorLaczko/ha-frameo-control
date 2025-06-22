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
        """Initialize the light."""
        self.client = client
        self._attr_name = f"{entry.title} Screen"
        self._attr_unique_id = f"{entry.entry_id}_screen"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}
        self._attr_is_on = None
        self._attr_brightness = None

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the screen on."""
        _LOGGER.info("Turning on Frameo screen for '%s'", self._attr_name)
        
        if ATTR_BRIGHTNESS in kwargs:
            new_brightness = kwargs[ATTR_BRIGHTNESS]
            _LOGGER.info("Setting Frameo brightness to %s", new_brightness)
            await self.client.async_shell(f"settings put system screen_brightness {new_brightness}")
            self._attr_brightness = new_brightness
        
        # To avoid sending an unnecessary key press, first check if it's already on.
        # But if we are certain it's off from the last update, just send the command.
        if self._attr_is_on is False:
             await self.client.async_shell("input keyevent 26") # KEYCODE_POWER
        else:
            # If state is unknown or on, check before pressing
            power_state = await self.client.async_shell("dumpsys power")
            if power_state and "mWakefulness=Asleep" in power_state:
                await self.client.async_shell("input keyevent 26") # KEYCODE_POWER

        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the screen off."""
        _LOGGER.info("Turning off Frameo screen for '%s'", self._attr_name)
        
        # To avoid sending an unnecessary key press, first check if it's already off.
        if self._attr_is_on is True:
            await self.client.async_shell("input keyevent 26") # KEYCODE_POWER
        else:
            # If state is unknown or off, check before pressing
            power_state = await self.client.async_shell("dumpsys power")
            if power_state and "mWakefulness=Awake" in power_state:
                await self.client.async_shell("input keyevent 26") # KEYCODE_POWER

        self._attr_is_on = False
        self.async_write_ha_state()

    async def async_update(self) -> None:
        """Fetch the latest state from the device."""
        _LOGGER.debug("Updating Frameo screen state for '%s'", self._attr_name)
        power_state = await self.client.async_shell("dumpsys power")
        if not power_state:
            self._attr_available = False
            return

        self._attr_available = True
        self._attr_is_on = "mWakefulness=Awake" in power_state
        
        # Brightness is part of the same dumpsys command
        for line in power_state.splitlines():
            if "mScreenBrightnessSetting=" in line:
                try:
                    self._attr_brightness = int(line.split("=")[1])
                    break
                except (ValueError, IndexError):
                    _LOGGER.warning("Could not parse brightness from line: %s", line)
                    pass