"""Sensor entity for Frameo IP address."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import FrameoDataUpdateCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
):
    """Set up the Frameo sensor platform."""
    coordinator: FrameoDataUpdateCoordinator = entry.runtime_data
    async_add_entities([FrameoIpSensor(coordinator, entry)])


class FrameoIpSensor(CoordinatorEntity[FrameoDataUpdateCoordinator], SensorEntity):
    _attr_has_entity_name = True
    _attr_name = "IP Address"
    _attr_icon = "mdi:ip-network"

    def __init__(self, coordinator: FrameoDataUpdateCoordinator, entry: ConfigEntry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_ip_address"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": entry.title,
        }
        self._update_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_state()
        self.async_write_ha_state()

    def _update_state(self):
        """Update the state of the sensor."""
        self._attr_native_value = self.coordinator.data.get("ip_address", "Unknown")