"""API client for the Frameo Control Backend Add-on."""
from __future__ import annotations

import re
from typing import Any, TYPE_CHECKING

import httpx

from homeassistant.helpers.httpx_client import get_async_client

from .const import (
    CONNECT_TIMEOUT,
    DEFAULT_ADDON_HOST,
    DEFAULT_ADDON_PORT,
    DEFAULT_TIMEOUT,
    LOGGER,
    USB_SCAN_TIMEOUT,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant


class FrameoApiError(Exception):
    """Exception raised when API communication fails."""


class FrameoDeviceDisconnectedError(FrameoApiError):
    """Exception raised when the device is disconnected."""


class FrameoAddonApiClient:
    """API Client for the Frameo Add-on."""

    def __init__(
        self,
        hass: HomeAssistant,
        host: str = DEFAULT_ADDON_HOST,
        port: int = DEFAULT_ADDON_PORT,
    ) -> None:
        """Initialize the API client.

        Args:
            hass: Home Assistant instance.
            host: Addon host address.
            port: Addon port number.

        """
        self._client = get_async_client(hass, verify_ssl=False)
        self._base_url = f"http://{host}:{port}"

    async def _request(
        self,
        method: str,
        endpoint: str,
        payload: dict[str, Any] | None = None,
        timeout: int = DEFAULT_TIMEOUT,
    ) -> dict[str, Any] | list[str] | None:
        """Make an HTTP request to the addon API.

        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint path.
            payload: JSON payload for the request.
            timeout: Request timeout in seconds.

        Returns:
            JSON response data or None on error.

        Raises:
            FrameoApiError: When the request fails.

        """
        url = f"{self._base_url}{endpoint}"
        try:
            response = await self._client.request(
                method,
                url,
                json=payload or {},
                timeout=timeout,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as err:
            status = err.response.status_code
            if status == 503:
                LOGGER.warning(
                    "Device disconnected (HTTP 503 from '%s')",
                    endpoint,
                )
                raise FrameoDeviceDisconnectedError("Device disconnected") from err
            LOGGER.error(
                "HTTP error for '%s': %s - %s",
                endpoint,
                status,
                err.response.text,
            )
            raise FrameoApiError(f"HTTP {status}") from err
        except httpx.RequestError as err:
            LOGGER.error("Request error for '%s': %s", endpoint, err)
            raise FrameoApiError(str(err)) from err
        except Exception as err:
            LOGGER.exception("Unexpected error for '%s'", endpoint)
            raise FrameoApiError(str(err)) from err

    async def async_get_usb_devices(self) -> list[str]:
        """Scan for available USB ADB devices.

        Returns:
            List of device serial numbers.

        """
        result = await self._request("GET", "/devices/usb", timeout=USB_SCAN_TIMEOUT)
        return result if isinstance(result, list) else []

    async def async_connect(self, conn_details: dict[str, Any]) -> dict[str, Any]:
        """Establish connection to a Frameo device.

        Args:
            conn_details: Connection configuration (type, host/serial, port).

        Returns:
            Connection result with status.

        """
        result = await self._request(
            "POST", "/connect", payload=conn_details, timeout=CONNECT_TIMEOUT
        )
        return result if isinstance(result, dict) else {"status": "error"}

    async def async_shell(self, command: str) -> dict[str, Any] | None:
        """Execute an ADB shell command on the device.

        Args:
            command: Shell command to execute.

        Returns:
            Command result with 'result' key containing output.

        """
        return await self._request("POST", "/shell", {"command": command})

    async def async_get_state(self) -> dict[str, Any] | None:
        """Get the current device state (screen on/off, brightness).

        Returns:
            Device state dictionary.

        """
        return await self._request("POST", "/state")

    async def async_enable_tcpip(self) -> dict[str, Any] | None:
        """Enable wireless ADB debugging on the device.

        Returns:
            Result of the operation.

        """
        return await self._request("POST", "/tcpip")

    async def async_get_screen_resolution(self) -> tuple[int, int] | None:
        """Get the device's current screen resolution accounting for rotation.

        Returns:
            Tuple of (width, height) or None if detection fails.

        """
        try:
            # First try dumpsys display which shows actual viewport dimensions
            result = await self._request(
                "POST", "/shell", 
                {"command": "dumpsys display | grep -E 'mViewport|mCurrentDisplayRect'"}
            )
            if result and "result" in result:
                output = result["result"]
                # Look for viewport or display rect like "deviceWidth=800, deviceHeight=1280"
                # or "mCurrentDisplayRect=Rect(0, 0 - 800, 1280)"
                match = re.search(r"deviceWidth=(\d+),\s*deviceHeight=(\d+)", output)
                if match:
                    width, height = int(match.group(1)), int(match.group(2))
                    LOGGER.debug("Detected screen resolution from viewport: %dx%d", width, height)
                    return (width, height)
                
                # Alternative pattern: mCurrentDisplayRect=Rect(0, 0 - 800, 1280)
                match = re.search(r"Rect\(\d+,\s*\d+\s*-\s*(\d+),\s*(\d+)\)", output)
                if match:
                    width, height = int(match.group(1)), int(match.group(2))
                    LOGGER.debug("Detected screen resolution from DisplayRect: %dx%d", width, height)
                    return (width, height)

            # Fallback to wm size
            result = await self._request("POST", "/shell", {"command": "wm size"})
            if result and "result" in result:
                output = result["result"]
                # wm size output can have multiple lines - take the last resolution
                matches = re.findall(r"(\d+)x(\d+)", output)
                if matches:
                    width, height = int(matches[-1][0]), int(matches[-1][1])
                    LOGGER.debug("Detected screen resolution from wm size: %dx%d", width, height)
                    return (width, height)
        except FrameoApiError:
            LOGGER.warning("Failed to detect screen resolution")
        return None