"""Button entities for Frameo control."""
from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER
from .coordinator import FrameoDataUpdateCoordinator
from . import FrameoConfigEntry

# --- Hardcoded coordinates for a typical 1280x800 landscape screen ---

# For Frameo swipes
SWIPE_Y = 500
SWIPE_START_X = 800
SWIPE_END_X = 100

# For Immich taps (dividing the screen into thirds)
TAP_Y = 400 # Vertical center of an 800px high screen
LEFT_THIRD_TAP_X = 213   # Middle of the left third (0-426)
CENTER_THIRD_TAP_X = 640 # Middle of the center third (427-853)
RIGHT_THIRD_TAP_X = 1067 # Middle of the right third (854-1280)


BUTTON_TYPES = {
    # --- Frameo App Controls (using swipes) ---
    "frameo_next": {
        "name": "Frameo Next Photo",
        "command": f"input swipe {SWIPE_START_X} {SWIPE_Y} {SWIPE_END_X} {SWIPE_Y}",
        "icon": "mdi:skip-next-circle-outline"
    },
    "frameo_prev": {
        "name": "Frameo Previous Photo",
        "command": f"input swipe {SWIPE_END_X} {SWIPE_Y} {SWIPE_START_X} {SWIPE_Y}",
        "icon": "mdi:skip-previous-circle-outline"
    },

    # --- Immich App Controls (using taps/clicks) ---
    "immich_next": {
        "name": "Immich Next Photo",
        "command": f"input tap {RIGHT_THIRD_TAP_X} {TAP_Y}",
        "icon": "mdi:arrow-right-drop-circle-outline"
    },
    "immich_prev": {
        "name": "Immich Previous Photo",
        "command": f"input tap {LEFT_THIRD_TAP_X} {TAP_Y}",
        "icon": "mdi:arrow-left-drop-circle-outline"
    },
    "immich_pause": {
        "name": "Immich Pause Photo",
        "command": f"input tap {CENTER_THIRD_TAP_X} {TAP_Y}",
        "icon": "mdi:pause-circle-outline"
    },

    # --- General Utility Buttons ---
    "start_frameo": {
        "name": "Start Frameo App",
        "command": "am start net.frameo.frame/.MainActivity",
        "icon": "mdi:image-multiple"
    },
    "start_immich": {
        "name": "Start ImmichFrame",
        "command": "am start com.immichframe.immichframe/.MainActivity",
        "icon": "mdi:image-album"
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