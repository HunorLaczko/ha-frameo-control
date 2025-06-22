import logging
from adb_shell.adb_device_async import AdbDeviceTcpAsync, AdbDeviceUsbAsync
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_HOST, CONF_PORT
from .const import DOMAIN, CONF_CONN_TYPE, CONN_TYPE_NETWORK, CONN_TYPE_USB, CONF_SERIAL

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.LIGHT, Platform.BUTTON]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA Frameo Control from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    
    # Create the correct ADB device object based on the connection type
    if entry.data[CONF_CONN_TYPE] == CONN_TYPE_NETWORK:
        device = AdbDeviceTcpAsync(
            host=entry.data[CONF_HOST],
            port=entry.data[CONF_PORT],
            default_transport_timeout_s=5.
        )
    elif entry.data[CONF_CONN_TYPE] == CONN_TYPE_USB:
        device = AdbDeviceUsbAsync(
            serial=entry.data.get(CONF_SERIAL),
            default_transport_timeout_s=5.
        )
    else:
        _LOGGER.error("Unknown connection type: %s", entry.data[CONF_CONN_TYPE])
        return False

    hass.data[DOMAIN][entry.entry_id] = {"device": device}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Ensure the device connection is closed
    device = hass.data[DOMAIN][entry.entry_id]["device"]
    await device.close()
    
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok