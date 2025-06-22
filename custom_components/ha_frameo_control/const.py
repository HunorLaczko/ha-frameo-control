"""Constants for the HA Frameo Control integration."""
import logging

LOGGER = logging.getLogger(__package__)
DOMAIN = "ha_frameo_control"

# Configuration Keys
CONF_CONN_TYPE = "connection_type"
CONF_SERIAL = "serial"
CONF_HOST = "host"
CONF_PORT = "port"

# Connection Types
CONN_TYPE_USB = "USB"
CONN_TYPE_NETWORK = "Network"