"""API client for the Frameo Control Backend Add-on."""
import httpx
from homeassistant.helpers.httpx_client import get_async_client

from .const import LOGGER

class FrameoAddonApiClient:
    """API Client for the Frameo Add-on."""

    def __init__(self, hass):
        """Initialize the API client."""
        # The add-on is on the host network, accessed via its slug as the hostname
        self.client = get_async_client(hass, verify_ssl=False)
        self.base_url = "http://a0d7b954-frameo_control_addon:5000"

    async def async_post_shell(self, command: str):
        """Send a shell command to the add-on."""
        url = f"{self.base_url}/shell"
        try:
            response = await self.client.post(url, json={"command": command}, timeout=15)
            response.raise_for_status()
            return await response.json()
        except httpx.RequestError as e:
            LOGGER.error("Error sending shell command '%s': %s", command, e)
            return None

    async def async_get_state(self):
        """Get the current state from the add-on."""
        url = f"{self.base_url}/state"
        try:
            response = await self.client.get(url, timeout=10)
            response.raise_for_status()
            return await response.json()
        except httpx.RequestError as e:
            LOGGER.error("Error getting state: %s", e)
            return None

    async def async_post_tcpip(self):
        """Send a request to enable wireless adb."""
        url = f"{self.base_url}/tcpip"
        try:
            response = await self.client.post(url, timeout=10)
            response.raise_for_status()
            return await response.json()
        except httpx.RequestError as e:
            LOGGER.error("Error enabling wireless ADB: %s", e)
            return None
