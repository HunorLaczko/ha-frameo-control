"""Data update coordinator for the HA Frameo Control integration."""
from datetime import timedelta
from asyncio import gather

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import FrameoAddonApiClient
from .const import DOMAIN, LOGGER


class FrameoDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the Frameo add-on."""

    def __init__(self, hass: HomeAssistant, client: FrameoAddonApiClient, config_data: dict):
        """Initialize the data update coordinator."""
        self.client = client
        self.config_data = config_data
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )

    async def _async_update_data(self):
        """Fetch data from the add-on."""
        try:
            # Fetch the two key pieces of information in parallel
            state_task = self.client.async_get_state(self.config_data)
            ip_task = self.client.async_get_ip_address(self.config_data)

            state, ip_info = await gather(state_task, ip_task)

            if not state or "is_on" not in state:
                raise UpdateFailed("Failed to get device state from add-on")
            
            # Combine the results into a single data object
            data = {
                "is_on": state.get("is_on"),
                "brightness": state.get("brightness"),
                "ip_address": ip_info.get("ip_address") if ip_info else "Unknown",
            }
            return data

        except Exception as err:
            raise UpdateFailed(f"Error communicating with add-on: {err}") from err