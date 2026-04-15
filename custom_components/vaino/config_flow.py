"""Config flow for Väinö MusicMaster."""
from __future__ import annotations

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .api import VainoApiClient, CannotConnect, VainoApiError
from .const import CONF_HOST, CONF_PORT, DEFAULT_PORT, DEFAULT_NAME, DOMAIN

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
    }
)


async def validate_host(hass: HomeAssistant, host: str, port: int) -> str:
    """Test the connection and return the device version string."""
    async with VainoApiClient(host, port) as client:
        status = await client.test_connection()
    return status.version


class VainoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the Väinö setup flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input.get(CONF_PORT, DEFAULT_PORT)

            # Prevent duplicate entries for the same device
            await self.async_set_unique_id(f"vaino_{host}_{port}")
            self._abort_if_unique_id_configured()

            try:
                await validate_host(self.hass, host, port)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except VainoApiError:
                errors["base"] = "unknown"
            except Exception:  # noqa: BLE001
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=DEFAULT_NAME,
                    data={CONF_HOST: host, CONF_PORT: port},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )
