"""Data update coordinator for the HA Frameo Control integration."""
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FrameoAddonApiClient
from .const import DOMAIN, LOGGER

class FrameoDataUpdateCoordinator(DataUpdateCoordinator):
    """Manages fetching data from the Frameo add-on."""

    def __init__(self, hass: HomeAssistant, client: FrameoAddonApiClient):
        """Initialize the data update coordinator."""
        self.client = client
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
        )

    async def _async_update_data(self):
        """Fetch the latest state from the device."""
        try:
            state = await self.client.async_get_state()
            if not state or "is_on" not in state:
                raise UpdateFailed("Failed to get device state from add-on")
            
            return {
                "is_on": state.get("is_on"),
                "brightness": state.get("brightness"),
            }
        except Exception as err:
            raise UpdateFailed(f"Error communicating with add-on: {err}") from err