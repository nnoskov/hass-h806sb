"""The H806SB Led Controller integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, TRACK_INTERVAL
from .controller import LedController
from datetime import timedelta

_LOGGER = logging.getLogger(__name__)
_PLATFORMS: list[str] = ["light"]

async def async_setup(hass: HomeAssistant, config: dict):
    """Setting integration by configuration.yaml."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Setting up from a config entry."""
    
    controller = LedController(host=entry.data["host"])

    # Create coordinator for periodically check
    coordinator = H806SBCoordinator(hass, controller)
    await coordinator.async_config_entry_first_refresh()

    config = {**entry.data, **entry.options}
    if entry.options:
        hass.config_entries.async_update_entry(entry, data=config, options={})

    _LOGGER.debug("Initializing H806SB controller entry (%s)", config)

    # Default config creation
    hass.data.setdefault(DOMAIN, {})
    
    hass.data[DOMAIN][entry.entry_id] = {
        "controller": controller,
        "coordinator": coordinator
    }

    """Settings integration by UI."""
    await hass.config_entries.async_forward_entry_setups(entry, _PLATFORMS)
    return True

class H806SBCoordinator(DataUpdateCoordinator):
    """Coordiantor for periodically check."""
    
    def __init__(self, hass, controller):
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            name="H806SB Device Status",
            update_interval=TRACK_INTERVAL
        )
        self.controller = controller
        
    async def _async_update_data(self):
        """Checking the available devices."""
        try:
            available = await self.controller.async_check_availability()
            _LOGGER.debug(f"available:{available}")
            return {"available": available}
        except Exception as err:
            _LOGGER.error("Error checking device availability: %s", err)
            raise UpdateFailed(f"Error checking device: {err}")


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Upload integrations."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, _PLATFORMS):
        # Remove data of integration
        hass.data[DOMAIN].pop(entry.entry_id)
        # In case last integration - clear domain
        if not hass.data[DOMAIN]:
            hass.data.pop(DOMAIN)
    return unload_ok