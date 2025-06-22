"""The ADB client wrapper."""
from adb_shell.adb_device import AdbDeviceUsb
from adb_shell.adb_device_async import AdbDeviceTcpAsync
from adb_shell.exceptions import AdbConnectionError, AdbTimeoutError

from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_HOST, CONF_PORT

from .const import (
    CONF_CONN_TYPE,
    CONN_TYPE_NETWORK,
    CONN_TYPE_USB,
    CONF_SERIAL,
    LOGGER,
)

class AdbClient:
    """A unified ADB client for both async TCP and sync USB connections."""

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        """Initialize the ADB client."""
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
            LOGGER.error("ADB command '%s' failed: %s", command, e)
        except Exception as e:
            LOGGER.error("An unexpected error occurred while running '%s': %s", command, e)
        return None

    async def async_tcpip(self, port: int) -> None:
        """Enable tcpip on the device (only for USB)."""
        if not self.is_usb:
            LOGGER.error("Cannot enable tcpip on a network connection")
            return

        try:
            await self.hass.async_add_executor_job(self.device.tcpip, port)
        except (AdbConnectionError, AdbTimeoutError) as e:
            LOGGER.error("Failed to start wireless ADB: %s", e)
        except Exception as e:
            LOGGER.error("An unexpected error occurred while starting wireless ADB: %s", e)