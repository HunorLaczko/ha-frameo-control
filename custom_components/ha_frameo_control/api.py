"""API client for the Frameo Control Backend Add-on."""
import httpx
from homeassistant.helpers.httpx_client import get_async_client
from .const import LOGGER

class FrameoAddonApiClient:
    """API Client for the Frameo Add-on."""

    def __init__(self, hass):
        """Initialize the API client."""
        self.client = get_async_client(hass, verify_ssl=False)
        self.base_url = "http://a0d7b954-frameo_control_addon:5000"

    async def _post(self, endpoint, payload=None):
        """Generic POST request helper."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = await self.client.post(url, json=payload, timeout=20)
            response.raise_for_status()
            return await response.json()
        except httpx.RequestError as e:
            LOGGER.error("Error requesting '%s': %s", endpoint, e)
            return None
        except Exception as e:
            LOGGER.error("An unexpected error occurred for '%s': %s", endpoint, e)
            return None

    async def async_get_usb_devices(self):
        """Get a list of connected USB devices from the add-on."""
        url = f"{self.base_url}/devices/usb"
        try:
            response = await self.client.get(url, timeout=15)
            response.raise_for_status()
            return await response.json()
        except httpx.RequestError as e:
            LOGGER.error("Error getting USB devices: %s", e)
            return None
    
    async def async_post_shell(self, conn_details: dict, command: str):
        """Send a shell command to the add-on."""
        payload = {**conn_details, "command": command}
        return await self._post("/shell", payload)

    async def async_get_state(self, conn_details: dict):
        """Get the current state from the add-on."""
        return await self._post("/state", conn_details)

    async def async_post_tcpip(self, conn_details: dict):
        """Send a request to enable wireless adb."""
        return await self._post("/tcpip", conn_details)