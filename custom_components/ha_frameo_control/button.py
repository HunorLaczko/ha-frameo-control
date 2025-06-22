import logging
from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, CONF_CONN_TYPE, CONN_TYPE_USB

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the Frameo button platform."""
    client = hass.data[DOMAIN][entry.entry_id]
    
    entities = [
        # Slideshow Controls
        FrameoActionButton(client, "Next Photo", "next", "input swipe 800 500 100 500", entry, "mdi:skip-next"),
        FrameoActionButton(client, "Previous Photo", "previous", "input swipe 100 500 800 500", entry, "mdi:skip-previous"),
        FrameoActionButton(client, "Pause Photo", "pause", "input keyevent 85", entry, "mdi:pause"),

        # App Launchers
        FrameoActionButton(client, "Start ImmichFrame", "start_immichframe", "am start com.immichframe.immichframe/.MainActivity", entry, "mdi:image-album"),
        FrameoActionButton(client, "Start Frameo App", "start_frameo", "am start net.frameo.frame/.MainActivity", entry, "mdi:image-multiple"),
        FrameoActionButton(client, "Open Settings", "open_settings", "am start -a android.settings.SETTINGS", entry, "mdi:cog"),
    ]

    # Only add the "Start Wireless ADB" button for USB connections
    if entry.data.get(CONF_CONN_TYPE) == CONN_TYPE_USB:
        entities.append(FrameoStartWirelessAdbButton(client, entry))

    async_add_entities(entities)

class FrameoActionButton(ButtonEntity):
    """Representation of a generic Frameo Action Button."""

    def __init__(self, client, name: str, endpoint: str, command: str, entry: ConfigEntry, icon: str = None) -> None:
        self.client = client
        self._command = command
        self._attr_name = f"{entry.title} {name}"
        self._attr_unique_id = f"{entry.entry_id}_{endpoint}"
        self._attr_icon = icon
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

    async def async_press(self) -> None:
        """Handle the button press by executing an ADB command."""
        _LOGGER.info("Executing button '%s' with command: %s", self.name, self._command)
        await self.client.async_shell(self._command)

class FrameoStartWirelessAdbButton(ButtonEntity):
    """Representation of a button to start wireless ADB."""
    _attr_device_class = ButtonDeviceClass.RESTART

    def __init__(self, client, entry: ConfigEntry) -> None:
        self.client = client
        self._attr_name = f"{entry.title} Start Wireless ADB"
        self._attr_unique_id = f"{entry.entry_id}_start_wireless"
        self._attr_device_info = {"identifiers": {(DOMAIN, entry.entry_id)}}

    async def async_press(self) -> None:
        """Handle the button press to enable TCP/IP mode."""
        _LOGGER.info("Executing 'Start Wireless ADB' button.")
        await self.client.async_tcpip(5555)