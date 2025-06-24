"""API client for the Frameo Control Backend Add-on."""
import httpx
from homeassistant.helpers.httpx_client import get_async_client
from .const import LOGGER, ADDON_URL

class FrameoAddonApiClient:
    """API Client for the Frameo Add-on."""

    def __init__(self, hass):
        self.client = get_async_client(hass, verify_ssl=False)
        self.base_url = ADDON_URL

    async def _request(self, method, endpoint, payload=None, timeout=20):
        """Generic request helper."""
        url = f"{self.base_url}{endpoint}"
        try:
            response = await self.client.request(
                method, url, json=payload if payload is not None else {}, timeout=timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            LOGGER.error("An unexpected error occurred for '%s': %s", endpoint, e)
            return None

    async def async_get_usb_devices(self):
        return await self._request("GET", "/devices/usb", timeout=15)
    
    async def async_connect(self, conn_details: dict):
        return await self._request("POST", "/connect", payload=conn_details, timeout=130)

    async def async_post_shell(self, command: str):
        return await self._request("POST", "/shell", {"command": command})

    async def async_get_state(self):
        return await self._request("POST", "/state")

    async def async_post_tcpip(self):
        return await self._request("POST", "/tcpip")