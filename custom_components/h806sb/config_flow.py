from homeassistant import config_entries, exceptions
from homeassistant.core import callback
from homeassistant.helpers.selector import selector, SelectOptionDict

import voluptuous as vol
import logging

from .discovery import H806SBDiscovery
from .controller import LedController
from .const import (
    DOMAIN, 
    CONFIG_VERSION, 
    CONF_ACTION,
    CONF_AUTO_DISCOVERY,
    CONF_MANUAL_SETUP,
    )

_LOGGER = logging.getLogger(__name__)

CONF_ACTIONS = {
    CONF_AUTO_DISCOVERY: "Automatic Discovery",
    CONF_MANUAL_SETUP: "Manual Setup",
}

@config_entries.HANDLERS.register(DOMAIN)
class H806SBFlowHandler(config_entries.ConfigFlow):
    """Config flow for H806SB."""

    VERSION = CONFIG_VERSION
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self):
        """Initialize the config flow."""
        self.discovered_device = None
        self._errors = {}

    @staticmethod
    @callback
    def async_get_option_flow(config_entry):
        """H806SB option callback."""
        _LOGGER.debug(f"GetOptionFlow:{config_entry}")
        return H806SBOptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        return await self.async_step_choice()


    async def async_step_choice(self, user_input=None):
        """Choice of type settings."""
      
        data_schema = vol.Schema(
            {
                vol.Required(CONF_ACTION, default=CONF_AUTO_DISCOVERY): vol.In(CONF_ACTIONS),
            }
        )

        if user_input is not None:
            if user_input.get(CONF_ACTION) == CONF_AUTO_DISCOVERY:
                return await self.async_step_auto_discovery()
            else:
                return await self.async_step_manual()

        return self.async_show_form(
            step_id="choice",
            data_schema=data_schema,
        )

    async def async_step_auto_discovery(self, user_input=None):
        """Automatic deiscovery step."""
        device = await self.async_discover_devices()
        if not device:
            return self.async_abort(reason="no_devices_found")

        controller = LedController(host=device["ip"])
        
        try:
            await self.async_set_unique_id(device["serial"])
            self._abort_if_unique_id_configured()
            # memorizing for future step
            self.discovered_device = device
            return await self.async_step_confirm()
        finally:
            await controller.async_close()

    async def async_step_confirm(self, user_input=None):
        """Confirming the addition of a newly discovered device."""
        device = self.discovered_device
        if user_input is None:
            return self.async_show_form(
                step_id="confirm",
                description_placeholders={
                    "name": device["name"],
                    "ip": device["ip"],
                    "serial": device["serial"]
                }
            )

        return self.async_create_entry(
            title=f"H806SB ({device['name']})",
            data={
                "host": device["ip"],
                "serial_number": device["serial"],
                "name": device["name"]
            },
        )

    async def async_step_manual(self, user_input=None):
        """Manual entry of device parameters."""
        errors = {}
        if user_input is not None:
            # Check unique device
            await self.async_set_unique_id(user_input["serial_number"])
            self._abort_if_unique_id_configured()
            
            # Create entry
            return self.async_create_entry(
                title=f"H806SB ({user_input['name']})",
                data={
                    "host": user_input["host"],
                    "serial_number": user_input["serial_number"],
                    "name": user_input["name"]
                },
            )

        return self.async_show_form(
            step_id="manual",
            data_schema=vol.Schema({
                vol.Required("host"): str,
                vol.Required("serial_number"): str,
                vol.Required("name", default="H806SB"): str,
            }),
            errors=errors
        )


    async def async_discover_devices(self):
        """Discover devices."""
        discovery = H806SBDiscovery()
        try:
            device = await discovery.discover_device()
            if device:
                ip, serial, name = device
                _LOGGER.debug(f"Device found: {name} (IP: {ip})")
                return {"ip": ip, "serial": serial.hex(), "name": name}
            _LOGGER.warning("No device found during discovery")
        except Exception as e:
            _LOGGER.error(f"Discovery error:{e}", exc_info=True)
        finally:
            if discovery:
                discovery.close()
        return None

class H806SBOptionsFlowHandler(config_entries.OptionsFlow):
    """Option flow for OpenRGB component."""
    
    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user()