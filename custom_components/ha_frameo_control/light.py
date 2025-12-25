"""Light entity for Frameo screen control."""
from __future__ import annotations

from typing import Any

from homeassistant.components.light import ATTR_BRIGHTNESS, ColorMode, LightEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FrameoConfigEntry
from .api import FrameoApiError
from .const import ADB_CMD_BRIGHTNESS, ADB_CMD_POWER_KEY, DOMAIN, LOGGER
from .coordinator import FrameoDataUpdateCoordinator, FrameoDeviceState


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FrameoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Frameo light platform.

    Args:
        hass: Home Assistant instance.
        entry: Config entry for this integration.
        async_add_entities: Callback to add entities.

    """
    coordinator: FrameoDataUpdateCoordinator = entry.runtime_data
    async_add_entities([FrameoScreenLight(coordinator, entry)])


class FrameoScreenLight(CoordinatorEntity[FrameoDataUpdateCoordinator], LightEntity):
    """Represents the Frameo device screen as a dimmable light."""

    _attr_has_entity_name = True
    _attr_name = "Screen"
    _attr_color_mode = ColorMode.BRIGHTNESS
    _attr_supported_color_modes = {ColorMode.BRIGHTNESS}

    def __init__(
        self,
        coordinator: FrameoDataUpdateCoordinator,
        entry: FrameoConfigEntry,
    ) -> None:
        """Initialize the light entity.

        Args:
            coordinator: Data update coordinator.
            entry: Config entry for this integration.

        """
        super().__init__(coordinator)
        self._client = coordinator.client
        self._attr_unique_id = f"{entry.entry_id}_screen"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
        }

    @property
    def _state(self) -> FrameoDeviceState | None:
        """Get the current device state from coordinator."""
        return self.coordinator.data

    @property
    def is_on(self) -> bool | None:
        """Return true if the screen is on."""
        if self._state is None:
            return None
        return self._state.is_on

    @property
    def brightness(self) -> int | None:
        """Return the brightness of the screen (0-255)."""
        if self._state is None:
            return None
        return self._state.brightness

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the screen on and/or set brightness.

        Args:
            **kwargs: Optional parameters including ATTR_BRIGHTNESS.

        """
        # Refresh state before action to ensure we have current state
        await self.coordinator.async_request_refresh()

        try:
            if ATTR_BRIGHTNESS in kwargs:
                new_brightness = kwargs[ATTR_BRIGHTNESS]
                LOGGER.debug("Setting Frameo brightness to %s", new_brightness)
                await self.coordinator.async_execute_command(
                    ADB_CMD_BRIGHTNESS.format(brightness=new_brightness)
                )

            if not self.is_on:
                LOGGER.debug("Turning on Frameo screen")
                await self.coordinator.async_execute_command(ADB_CMD_POWER_KEY)

            # Refresh state after action
            await self.coordinator.async_request_refresh()
        except FrameoApiError as err:
            LOGGER.error("Failed to turn on screen: %s", err)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the screen off.

        Args:
            **kwargs: Optional parameters (unused).

        """
        # Refresh state before action
        await self.coordinator.async_request_refresh()

        try:
            if self.is_on:
                LOGGER.debug("Turning off Frameo screen")
                await self.coordinator.async_execute_command(ADB_CMD_POWER_KEY)

            # Refresh state after action
            await self.coordinator.async_request_refresh()
        except FrameoApiError as err:
            LOGGER.error("Failed to turn off screen: %s", err)

        await self.coordinator.async_request_refresh()