"""Button entities for Frameo control."""
from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER
from .coordinator import FrameoDataUpdateCoordinator
from . import FrameoConfigEntry

# These coordinates are optimized for a PORTRAIT screen (e.g., 800x1280).
# By tapping the sides instead of the top/bottom, they have a better chance
# of also working in landscape mode.
PORTRAIT_WIDTH = 800
PORTRAIT_HEIGHT = 1280

# Tap the screen's sides, at the vertical midpoint.
TAP_Y_COORD = int(PORTRAIT_HEIGHT / 2)  # -> 640
PREVIOUS_X_COORD = int(PORTRAIT_WIDTH * 0.15) # -> 120 (Left side)
NEXT_X_COORD = int(PORTRAIT_WIDTH * 0.85)     # -> 680 (Right side)
CENTER_X_COORD = int(PORTRAIT_WIDTH / 2)       # -> 400 (Center)


BUTTON_TYPES = {
    "next_photo": {
        "name": "Next Photo",
        "command": f"input tap {NEXT_X_COORD} {TAP_Y_COORD}",
        "icon": "mdi:arrow-right-drop-circle-outline"
    },
    "prev_photo": {
        "name": "Previous Photo",
        "command": f"input tap {PREVIOUS_X_COORD} {TAP_Y_COORD}",
        "icon": "mdi:arrow-left-drop-circle-outline"
    },
    "pause_photo": {
        "name": "Pause Photo",
        "command": f"input tap {CENTER_X_COORD} {TAP_Y_COORD}",
        "icon": "mdi:pause-circle-outline"
    },
    "start_immich": {
        "name": "Start ImmichFrame",
        "command": "am start com.immichframe.immichframe/.MainActivity",
        "icon": "mdi:image-album"
    },
    "start_frameo": {
        "name": "Start Frameo App",
        "command": "am start net.frameo.frame",
        "icon": "mdi:image-multiple"
    },
    "open_settings": {
        "name": "Open Settings",
        "command": "am start -a android.settings.SETTINGS",
        "icon": "mdi:cog"
    },
    "start_wireless": {
        "name": "Start Wireless ADB",
        "icon": "mdi:wifi-arrow-up-down",
        "device_class": ButtonDeviceClass.RESTART
    },
}

async def async_setup_entry(
    hass: HomeAssistant, entry: FrameoConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the Frameo button platform."""
    coordinator: FrameoDataUpdateCoordinator = entry.runtime_data
    entities = [
        FrameoButton(coordinator, entry, key, props) for key, props in BUTTON_TYPES.items()
    ]
    async_add_entities(entities)

class FrameoButton(CoordinatorEntity[FrameoDataUpdateCoordinator], ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: FrameoDataUpdateCoordinator, entry: FrameoConfigEntry, key: str, props: dict):
        super().__init__(coordinator)
        self.client = coordinator.client
        self.key = key
        self.props = props
        self._attr_name = props["name"]
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_icon = props["icon"]
        self._attr_device_class = props.get("device_class")
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
        }

    async def async_press(self):
        """Handle the button press."""
        LOGGER.info("Executing button '%s'", self.name)
        if self.key == "start_wireless":
            await self.client.async_post_tcpip()
        else:
            await self.client.async_post_shell(self.props["command"])