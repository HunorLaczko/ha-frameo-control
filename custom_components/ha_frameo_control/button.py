"""Button entities for Frameo control."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from homeassistant.components.button import (
    ButtonDeviceClass,
    ButtonEntity,
    ButtonEntityDescription,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import FrameoConfigEntry
from .api import FrameoApiError
from .const import DOMAIN, LOGGER
from .coordinator import FrameoDataUpdateCoordinator


class ButtonAction(StrEnum):
    """Button action types."""

    SHELL = "shell"
    TCPIP = "tcpip"


class GestureType(StrEnum):
    """Types of screen gestures."""

    SWIPE_LEFT = "swipe_left"  # Next photo in Frameo
    SWIPE_RIGHT = "swipe_right"  # Previous photo in Frameo
    TAP_LEFT = "tap_left"  # Previous in Immich
    TAP_CENTER = "tap_center"  # Pause in Immich
    TAP_RIGHT = "tap_right"  # Next in Immich


@dataclass(frozen=True, kw_only=True)
class FrameoButtonEntityDescription(ButtonEntityDescription):
    """Describes a Frameo button entity."""

    command: str | None = None
    action: ButtonAction = ButtonAction.SHELL
    gesture: GestureType | None = None


def _build_gesture_command(
    gesture: GestureType, screen_width: int, screen_height: int
) -> str:
    """Build an ADB input command for a gesture based on screen dimensions.

    Args:
        gesture: Type of gesture to perform.
        screen_width: Screen width in pixels.
        screen_height: Screen height in pixels.

    Returns:
        ADB shell command string.

    """
    # Swipe coordinates
    swipe_y = screen_height // 2 + screen_height // 8  # Slightly below center
    swipe_start_x = int(screen_width * 0.625)
    swipe_end_x = int(screen_width * 0.078)

    # Tap coordinates (screen divided into thirds)
    tap_y = screen_height // 2
    left_third_x = screen_width // 6
    center_x = screen_width // 2
    right_third_x = int(screen_width * 5 / 6)

    commands = {
        GestureType.SWIPE_LEFT: f"input swipe {swipe_start_x} {swipe_y} {swipe_end_x} {swipe_y}",
        GestureType.SWIPE_RIGHT: f"input swipe {swipe_end_x} {swipe_y} {swipe_start_x} {swipe_y}",
        GestureType.TAP_LEFT: f"input tap {left_third_x} {tap_y}",
        GestureType.TAP_CENTER: f"input tap {center_x} {tap_y}",
        GestureType.TAP_RIGHT: f"input tap {right_third_x} {tap_y}",
    }

    return commands[gesture]


# --- Button Definitions ---

BUTTON_DESCRIPTIONS: tuple[FrameoButtonEntityDescription, ...] = (
    # Frameo App Controls (swipe gestures)
    FrameoButtonEntityDescription(
        key="frameo_next",
        name="Frameo Next Photo",
        icon="mdi:skip-next-circle-outline",
        gesture=GestureType.SWIPE_LEFT,
    ),
    FrameoButtonEntityDescription(
        key="frameo_prev",
        name="Frameo Previous Photo",
        icon="mdi:skip-previous-circle-outline",
        gesture=GestureType.SWIPE_RIGHT,
    ),
    # Immich App Controls (tap gestures)
    FrameoButtonEntityDescription(
        key="immich_next",
        name="Immich Next Photo",
        icon="mdi:arrow-right-drop-circle-outline",
        gesture=GestureType.TAP_RIGHT,
    ),
    FrameoButtonEntityDescription(
        key="immich_prev",
        name="Immich Previous Photo",
        icon="mdi:arrow-left-drop-circle-outline",
        gesture=GestureType.TAP_LEFT,
    ),
    FrameoButtonEntityDescription(
        key="immich_pause",
        name="Immich Pause Photo",
        icon="mdi:pause-circle-outline",
        gesture=GestureType.TAP_CENTER,
    ),
    # App Launchers
    FrameoButtonEntityDescription(
        key="start_frameo",
        name="Start Frameo App",
        icon="mdi:image-multiple",
        command="am start net.frameo.frame/.MainActivity",
    ),
    FrameoButtonEntityDescription(
        key="start_immich",
        name="Start ImmichFrame",
        icon="mdi:image-album",
        command="am start com.immichframe.immichframe/.MainActivity",
    ),
    FrameoButtonEntityDescription(
        key="open_settings",
        name="Open Settings",
        icon="mdi:cog",
        command="am start -a android.settings.SETTINGS",
    ),
    # Utility Buttons
    FrameoButtonEntityDescription(
        key="start_wireless",
        name="Start Wireless ADB",
        icon="mdi:wifi-arrow-up-down",
        device_class=ButtonDeviceClass.RESTART,
        action=ButtonAction.TCPIP,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: FrameoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Frameo button platform.

    Args:
        hass: Home Assistant instance.
        entry: Config entry for this integration.
        async_add_entities: Callback to add entities.

    """
    coordinator: FrameoDataUpdateCoordinator = entry.runtime_data
    async_add_entities(
        FrameoButton(coordinator, entry, description)
        for description in BUTTON_DESCRIPTIONS
    )


class FrameoButton(CoordinatorEntity[FrameoDataUpdateCoordinator], ButtonEntity):
    """A button entity for controlling the Frameo device."""

    _attr_has_entity_name = True
    entity_description: FrameoButtonEntityDescription

    def __init__(
        self,
        coordinator: FrameoDataUpdateCoordinator,
        entry: FrameoConfigEntry,
        description: FrameoButtonEntityDescription,
    ) -> None:
        """Initialize the button entity.

        Args:
            coordinator: Data update coordinator.
            entry: Config entry for this integration.
            description: Entity description.

        """
        super().__init__(coordinator)
        self.entity_description = description
        self._client = coordinator.client
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
        }

    async def _async_get_command(self) -> str | None:
        """Get the command for this button, calculating gestures dynamically.

        For gesture-based commands, this refreshes the screen resolution first
        to handle orientation changes.

        Returns:
            ADB shell command or None.

        """
        description = self.entity_description

        if description.gesture:
            # Refresh screen resolution to handle orientation changes
            width, height = await self.coordinator.async_refresh_screen_resolution()
            return _build_gesture_command(description.gesture, width, height)

        return description.command

    async def async_press(self) -> None:
        """Handle the button press."""
        description = self.entity_description
        LOGGER.debug("Executing button '%s'", description.name)

        try:
            if description.action == ButtonAction.TCPIP:
                await self._client.async_enable_tcpip()
            else:
                command = await self._async_get_command()
                if command:
                    LOGGER.info("Button '%s' executing command: %s", description.name, command)
                    await self.coordinator.async_execute_command(command)
        except FrameoApiError as err:
            LOGGER.error("Button '%s' failed: %s", description.name, err)