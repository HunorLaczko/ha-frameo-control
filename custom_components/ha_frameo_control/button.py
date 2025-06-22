import logging
from adb_shell.exceptions import AdbShellError

from homeassistant.components.button import ButtonEntity, ButtonDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from .const import DOMAIN, CONF_CONN_TYPE, CONN_TYPE_USB

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Frameo button platform."""
    device = hass.data[DOMAIN][entry.entry_id]["device"]
    
    entities = [
        # Slideshow Controls
        FrameoActionButton(device, "Next Photo", "next", "input swipe 800 500 100 500", entry, "mdi:skip-next"),
        FrameoActionButton(device, "Previous Photo", "previous", "input swipe 100 500 800 500", entry, "mdi:skip-previous"),
        FrameoActionButton(device, "Pause Photo", "pause", "input keyevent 85", entry, "mdi:pause"),

        # App Launchers
        FrameoActionButton(device, "Start ImmichFrame", "start_immichframe", "am start com.immichframe.immichframe/.MainActivity", entry, "mdi:image-album"),
        FrameoActionButton(device, "Start Frameo App", "start_frameo", "am start net.frameo.frame/.MainActivity", entry, "mdi:image-multiple"),
        FrameoActionButton(device, "Open Settings", "open_settings", "am start -a android.settings.SETTINGS", entry, "mdi:cog"),
    ]

    # Only add the "Start Wireless ADB" button for USB connections
    if entry.data.get(CONF_CONN_TYPE) == CONN_TYPE_USB:
        # This button is more of a restart/re-init action for the connection
        entities.append(FrameoStartWirelessAdbButton(device, entry))

    async_add_entities(entities)


class FrameoBaseButton(ButtonEntity):
    """Base class for Frameo buttons to share ADB methods."""

    def __init__(self, device, entry: ConfigEntry) -> None:
        self._device = device
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
            "manufacturer": "Frameo",
        }

    async def _async_adb_shell(self, command: str) -> str | None:
        """Wrapper for sending ADB shell commands."""
        try:
            await self._device.connect(timeout_s=5.)
            return await self._device.shell(command, timeout_s=10.)
        except AdbShellError as e:
            _LOGGER.warning("ADB command '%s' failed: %s", command, e)
        except Exception as e:
            _LOGGER.error("An unexpected error occurred while running '%s': %s", command, e)
        finally:
            await self.async_close_connection()
        return None
    
    async def async_close_connection(self) -> None:
        """Close the ADB connection."""
        try:
            await self._device.close()
        except Exception as e:
            _LOGGER.debug("Error closing ADB connection: %s", e)


class FrameoActionButton(FrameoBaseButton):
    """Representation of a generic Frameo Action Button."""

    def __init__(self, device, name: str, endpoint: str, command: str, entry: ConfigEntry, icon: str = None) -> None:
        super().__init__(device, entry)
        self._command = command
        self._attr_name = f"{entry.title} {name}"
        self._attr_unique_id = f"{entry.entry_id}_{endpoint}"
        self._attr_icon = icon

    async def async_press(self) -> None:
        """Handle the button press."""
        await self._async_adb_shell(self._command)


class FrameoStartWirelessAdbButton(FrameoBaseButton):
    """Representation of a button to start wireless ADB."""
    _attr_device_class = ButtonDeviceClass.RESTART

    def __init__(self, device, entry: ConfigEntry) -> None:
        super().__init__(device, entry)
        self._attr_name = f"{entry.title} Start Wireless ADB"
        self._attr_unique_id = f"{entry.entry_id}_start_wireless"

    async def async_press(self) -> None:
        """Handle the button press to enable TCP/IP mode."""
        try:
            _LOGGER.info("Attempting to start wireless ADB on port 5555")
            await self._device.connect(timeout_s=5.)
            await self._device.tcpip(5555)
            _LOGGER.info("Successfully sent command to start wireless ADB.")
        except AdbShellError as e:
            _LOGGER.warning("Failed to start wireless ADB: %s", e)
        except Exception as e:
            _LOGGER.error("An unexpected error occurred while starting wireless ADB: %s", e)
        finally:
            await self.async_close_connection()