import logging
from adb_shell.adb_device import AdbDeviceUsb
from adb_shell.adb_device_async import AdbDeviceTcpAsync
from adb_shell.exceptions import AdbConnectionError, AdbTimeoutError, UsbDeviceNotFoundError

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_HOST, CONF_PORT
from .const import DOMAIN, CONF_CONN_TYPE, CONN_TYPE_NETWORK, CONN_TYPE_USB, CONF_SERIAL

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.LIGHT, Platform.BUTTON]

class AdbClient:
    """A unified ADB client for both async TCP and sync USB connections."""

    def __init__(self, hass: HomeAssistant, config: dict):
        self.hass = hass
        self.is_usb = config.get(CONF_CONN_TYPE) == CONN_TYPE_USB
        
        if self.is_usb:
            self.device = AdbDeviceUsb(serial=config.get(CONF_SERIAL), default_transport_timeout_s=5.)
        else:
            self.device = AdbDeviceTcpAsync(host=config[CONF_HOST], port=config[CONF_PORT], default_transport_timeout_s=5.)

    async def async_shell(self, command: str) -> str | None:
        """Execute a shell command, handling both connection types."""
        try:
            if self.is_usb:
                # Run synchronous blocking call in an executor job
                return await self.hass.async_add_executor_job(
                    self.device.shell, command
                )
            
            # Await the coroutine for the async TCP device
            return await self.device.shell(command)
        except (AdbConnectionError, AdbTimeoutError) as e:
            _LOGGER.warning("ADB command '%s' failed: %s", command, e)
        except Exception as e:
            _LOGGER.error("An unexpected error occurred while running '%s': %s", command, e)
        return None

    async def async_tcpip(self, port: int) -> None:
        """Enable tcpip on the device (only for USB)."""
        if not self.is_usb:
            _LOGGER.error("Cannot enable tcpip on a network connection")
            return

        try:
            await self.hass.async_add_executor_job(self.device.tcpip, port)
        except (AdbConnectionError, AdbTimeoutError) as e:
            _LOGGER.warning("Failed to start wireless ADB: %s", e)
        except Exception as e:
            _LOGGER.error("An unexpected error occurred while starting wireless ADB: %s", e)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA Frameo Control from a config entry."""
    adb_client = AdbClient(hass, entry.data)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = adb_client
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok