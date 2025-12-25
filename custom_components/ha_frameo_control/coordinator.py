"""Data update coordinator for the HA Frameo Control integration."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FrameoAddonApiClient, FrameoApiError, FrameoDeviceDisconnectedError
from .const import (
    DEFAULT_SCREEN_HEIGHT,
    DEFAULT_SCREEN_WIDTH,
    DOMAIN,
    LOGGER,
)

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

# Maximum number of reconnection attempts
MAX_RECONNECT_ATTEMPTS = 3


@dataclass
class FrameoDeviceState:
    """Represents the current state of a Frameo device."""

    is_on: bool
    brightness: int
    screen_width: int
    screen_height: int

    @classmethod
    def from_api_response(
        cls,
        data: dict,
        screen_width: int = DEFAULT_SCREEN_WIDTH,
        screen_height: int = DEFAULT_SCREEN_HEIGHT,
    ) -> "FrameoDeviceState":
        """Create a FrameoDeviceState from API response data.

        Args:
            data: API response dictionary.
            screen_width: Screen width (auto-detected or configured).
            screen_height: Screen height (auto-detected or configured).

        Returns:
            FrameoDeviceState instance.

        """
        return cls(
            is_on=data.get("is_on", False),
            brightness=data.get("brightness", 0),
            screen_width=screen_width,
            screen_height=screen_height,
        )


class FrameoDataUpdateCoordinator(DataUpdateCoordinator[FrameoDeviceState]):
    """Manages fetching data from the Frameo add-on.
    
    This coordinator does NOT poll automatically. State is refreshed on-demand
    before interactions to reduce USB traffic and avoid connection issues.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: FrameoAddonApiClient,
        conn_details: dict[str, Any],
        configured_width: int = DEFAULT_SCREEN_WIDTH,
        configured_height: int = DEFAULT_SCREEN_HEIGHT,
    ) -> None:
        """Initialize the data update coordinator.

        Args:
            hass: Home Assistant instance.
            client: API client for the Frameo addon.
            conn_details: Connection details for reconnection.
            configured_width: Fallback screen width from config.
            configured_height: Fallback screen height from config.

        """
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            # Disable automatic polling - we refresh on-demand
            update_interval=None,
        )
        self.client = client
        self._conn_details = conn_details
        self._configured_width = configured_width
        self._configured_height = configured_height
        self._detected_width: int | None = None
        self._detected_height: int | None = None
        self._resolution_detected = False
        self._is_connected = True

    @property
    def screen_width(self) -> int:
        """Get the current screen width (detected or configured)."""
        return self._detected_width or self._configured_width

    @property
    def screen_height(self) -> int:
        """Get the current screen height (detected or configured)."""
        return self._detected_height or self._configured_height

    @property
    def is_connected(self) -> bool:
        """Return whether the device is currently connected."""
        return self._is_connected

    async def async_reconnect(self) -> bool:
        """Attempt to reconnect to the device.

        Returns:
            True if reconnection was successful.

        """
        LOGGER.info("Attempting to reconnect to device...")
        try:
            result = await self.client.async_connect(self._conn_details)
            if result and result.get("status") in ("connected", "already_connected"):
                LOGGER.info("Reconnection successful")
                self._is_connected = True
                return True
            LOGGER.warning("Reconnection failed: %s", result)
            return False
        except FrameoApiError as err:
            LOGGER.error("Reconnection error: %s", err)
            return False

    async def async_ensure_connected(self) -> bool:
        """Ensure the device is connected, attempting reconnection if needed.

        Returns:
            True if connected (or successfully reconnected).

        """
        if self._is_connected:
            return True

        for attempt in range(1, MAX_RECONNECT_ATTEMPTS + 1):
            LOGGER.info("Reconnection attempt %d/%d", attempt, MAX_RECONNECT_ATTEMPTS)
            if await self.async_reconnect():
                return True

        LOGGER.error("All reconnection attempts failed")
        return False

    async def async_detect_screen_resolution(self) -> bool:
        """Attempt to detect the screen resolution from the device.

        Returns:
            True if detection was successful.

        """
        try:
            resolution = await self.client.async_get_screen_resolution()
            if resolution:
                self._detected_width, self._detected_height = resolution
                self._resolution_detected = True
                LOGGER.debug(
                    "Screen resolution detected: %dx%d",
                    self._detected_width,
                    self._detected_height,
                )
                return True
        except FrameoApiError:
            pass
        LOGGER.warning(
            "Could not detect screen resolution, using configured: %dx%d",
            self._configured_width,
            self._configured_height,
        )
        return False

    async def async_refresh_screen_resolution(self) -> tuple[int, int]:
        """Refresh and return the current screen resolution.

        This should be called before gesture-based commands to handle
        orientation changes.

        Returns:
            Tuple of (width, height).

        """
        await self.async_detect_screen_resolution()
        LOGGER.info(
            "Using screen resolution for gesture: %dx%d",
            self.screen_width,
            self.screen_height,
        )
        return (self.screen_width, self.screen_height)

    async def _async_update_data(self) -> FrameoDeviceState:
        """Fetch the latest state from the device.

        Returns:
            Current device state.

        Raises:
            UpdateFailed: When communication with the device fails.

        """
        try:
            # Ensure we're connected first
            if not await self.async_ensure_connected():
                raise UpdateFailed(
                    "Device disconnected and reconnection failed. "
                    "Check the connection and reload the integration."
                )

            # Try to detect resolution on first update if not already done
            if not self._resolution_detected:
                await self.async_detect_screen_resolution()

            state = await self.client.async_get_state()

            if not state or "is_on" not in state:
                raise UpdateFailed("Invalid or empty state response from add-on")

            return FrameoDeviceState.from_api_response(
                state,
                screen_width=self.screen_width,
                screen_height=self.screen_height,
            )

        except FrameoDeviceDisconnectedError:
            self._is_connected = False
            # Try to reconnect
            if await self.async_ensure_connected():
                # Retry the state fetch after reconnection
                try:
                    state = await self.client.async_get_state()
                    if state and "is_on" in state:
                        return FrameoDeviceState.from_api_response(
                            state,
                            screen_width=self.screen_width,
                            screen_height=self.screen_height,
                        )
                except FrameoApiError:
                    pass
            raise UpdateFailed(
                "Device disconnected. Reconnection will be attempted on next interaction."
            )
        except FrameoApiError as err:
            raise UpdateFailed(f"Error communicating with add-on: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

    async def async_execute_command(self, command: str) -> dict[str, Any] | None:
        """Execute an ADB command with automatic reconnection.

        Args:
            command: ADB shell command to execute.

        Returns:
            Command result or None.

        Raises:
            FrameoApiError: If command fails after reconnection attempts.

        """
        # Ensure connected before executing
        if not await self.async_ensure_connected():
            raise FrameoApiError("Device not connected")

        try:
            return await self.client.async_shell(command)
        except FrameoDeviceDisconnectedError:
            self._is_connected = False
            # Try to reconnect and retry once
            if await self.async_reconnect():
                return await self.client.async_shell(command)
            raise