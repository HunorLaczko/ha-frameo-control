import logging
from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, CONF_CONN_TYPE, CONN_TYPE_USB
from . import FrameoConfigEntry

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: FrameoConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Frameo button platform."""
    client = entry.runtime_data
    
    entities = [
        FrameoActionButton(client, "Next Photo", "next", "input swipe 800 500 100 500", entry, "mdi:skip-next"),
        FrameoActionButton(client, "Previous Photo", "previous", "input swipe 100 500 800 500", entry, "mdi:skip-previous"),
        FrameoActionButton(client, "Pause Photo", "pause", "input keyevent 85", entry, "mdi:pause"),
        FrameoActionButton(client, "Start ImmichFrame", "start_immichframe", "am start com.immichframe.immichframe/.MainActivity", entry, "mdi:image-album"),
        FrameoActionButton(client, "Start Frameo App", "start_frameo", "am start net.frameo.frame/.MainActivity", entry, "mdi:image-multiple"),
        FrameoActionButton(client, "Open Settings", "open_settings", "am start -a android.settings.SETTINGS", entry, "mdi:cog"),
    ]

    if entry.data.get(CONF_CONN_TYPE) == CONN_TYPE_USB:
        entities.append(FrameoStartWirelessAdbButton(client, entry))

    async_add_entities(entities)

class FrameoActionButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, client, name: str, endpoint: str, command: str, entry: FrameoConfigEntry, icon: str = None) -> None:
        self.client = client
        self._command = command
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_{endpoint}"
        self._attr_icon = icon
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

    async def async_press(self) -> None:
        _LOGGER.info("Executing button '%s'", self.name)
        await self.client.async_shell(self._command)

class FrameoStartWirelessAdbButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_device_class = ButtonDeviceClass.RESTART
    _attr_name = "Start Wireless ADB"

    def __init__(self, client, entry: FrameoConfigEntry) -> None:
        self.client = client
        self._attr_unique_id = f"{entry.entry_id}_start_wireless"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

    async def async_press(self) -> None:
        _LOGGER.info("Executing 'Start Wireless ADB' button.")
        await self.client.async_tcpip(5555)