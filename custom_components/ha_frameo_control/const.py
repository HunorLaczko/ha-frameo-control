"""Constants for the HA Frameo Control integration."""
import logging
from homeassistant.const import Platform

LOGGER = logging.getLogger(__package__)
DOMAIN = "ha_frameo_control"
ADDON_URL = "http://addon_467cfd57_frameo_control:5000"

# Define the platforms that this integration will create entities for
PLATFORMS: list[Platform] = [Platform.LIGHT, Platform.BUTTON]

# Configuration Keys
CONF_CONN_TYPE = "connection_type"
CONF_SERIAL = "serial"
CONF_HOST = "host"
CONF_PORT = "port"

# Connection Types
CONN_TYPE_USB = "USB"
CONN_TYPE_NETWORK = "Network"