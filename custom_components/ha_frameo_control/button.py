"""Button entities for Frameo control."""
from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, LOGGER
from .api import FrameoAddonApiClient
from . import FrameoConfigEntry

BUTTON_TYPES = {
    "next_photo": {"name": "Next Photo", "command": "input swipe 800 500 100 500", "icon": "mdi:skip-next"},
    "prev_photo": {"name": "Previous Photo", "command": "input swipe 100 500 800 500", "icon": "mdi:skip-previous"},
    "pause_photo": {"name": "Pause Photo", "command": "input keyevent 85", "icon": "mdi:pause"},
    "start_immich": {"name": "Start ImmichFrame", "command": "am start com.immichframe.immichframe/.MainActivity", "icon": "mdi:image-album"},
    "start_frameo": {"name": "Start Frameo App", "command": "am start net.frameo.frame/.MainActivity", "icon": "mdi:image-multiple"},
    "open_settings": {"name": "Open Settings", "command": "am start -a android.settings.SETTINGS", "icon": "mdi:cog"},
    "start_wireless": {"name": "Start Wireless ADB", "command": "tcpip", "icon": "mdi:wifi-arrow-up-down", "device_class": ButtonDeviceClass.RESTART},
}

async def async_setup_entry(
    hass: HomeAssistant, entry: FrameoConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the Frameo button platform."""
    client = entry.runtime_data
    entities = [
        FrameoButton(client, entry, key, props) for key, props in BUTTON_TYPES.items()
    ]
    async_add_entities(entities)

class FrameoButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, client: FrameoAddonApiClient, entry: FrameoConfigEntry, key: str, props: dict):
        self.client = client
        self.config_data = entry.data
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
        LOGGER.error("Executing button '%s'", self.name)
        if self.key == "start_wireless":
            await self.client.async_post_tcpip(self.config_data)
        else:
            await self.client.async_post_shell(self.config_data, self.props["command"])