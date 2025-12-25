"""Constants for the HA Frameo Control integration."""
from __future__ import annotations

import logging
from enum import StrEnum
from typing import Final

from homeassistant.const import Platform

LOGGER: Final = logging.getLogger(__package__)

# Integration identifiers
DOMAIN: Final = "ha_frameo_control"

# Platforms supported by this integration
PLATFORMS: Final[list[Platform]] = [Platform.LIGHT, Platform.BUTTON]


class ConnectionType(StrEnum):
    """Connection types for Frameo devices."""

    USB = "USB"
    NETWORK = "Network"


# Configuration keys
CONF_CONN_TYPE: Final = "connection_type"
CONF_SERIAL: Final = "serial"
CONF_ADDON_HOST: Final = "addon_host"
CONF_ADDON_PORT: Final = "addon_port"
CONF_SCREEN_WIDTH: Final = "screen_width"
CONF_SCREEN_HEIGHT: Final = "screen_height"

# Default configuration values
DEFAULT_DEVICE_PORT: Final = 5555
DEFAULT_ADDON_HOST: Final = "127.0.0.1"
DEFAULT_ADDON_PORT: Final = 5000

# Timeouts (in seconds)
DEFAULT_TIMEOUT: Final = 20
CONNECT_TIMEOUT: Final = 130
USB_SCAN_TIMEOUT: Final = 15

# ADB shell commands
ADB_CMD_POWER_KEY: Final = "input keyevent 26"
ADB_CMD_BRIGHTNESS: Final = "settings put system screen_brightness {brightness}"
ADB_CMD_POWER_STATE: Final = "dumpsys power"
ADB_CMD_SCREEN_SIZE: Final = "wm size"

# Default screen dimensions for gestures (1280x800 landscape)
DEFAULT_SCREEN_WIDTH: Final = 1280
DEFAULT_SCREEN_HEIGHT: Final = 800

# Service names
SERVICE_RUN_ADB_COMMAND: Final = "run_adb_command"

# Attributes
ATTR_COMMAND: Final = "command"
ATTR_RESULT: Final = "result"

# Events
EVENT_ADB_RESPONSE: Final = f"{DOMAIN}_adb_response"