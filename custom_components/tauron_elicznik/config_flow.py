"""Config flow for Tauron eLicznik integration."""

from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import TauronApiClient, TauronApiError, TauronAuthError
from .const import (
    CONF_BILLING_PERIOD_START,
    CONF_PREV_ENERGIA_ODDANA,
    CONF_PREV_ENERGIA_POBRANA,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _get_default_billing_start() -> str:
    """Get default billing period start (March 1 of current or previous year)."""
    today = datetime.now()
    year = today.year if today.month >= 3 else today.year - 1
    return f"{year}-03-01"


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_BILLING_PERIOD_START, default=_get_default_billing_start()): str,
    }
)


class TauronElicznikConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Tauron eLicznik."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            billing_start = None
            energy_at_start = None

            # Validate date format
            try:
                billing_start = datetime.strptime(
                    user_input[CONF_BILLING_PERIOD_START], "%Y-%m-%d"
                ).date()
            except ValueError:
                errors["base"] = "invalid_date"

            if not errors:
                # Set unique ID based on username to prevent duplicates
                await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
                self._abort_if_unique_id_configured()

                # Authenticate and fetch initial readings for billing period start
                try:
                    session = async_get_clientsession(self.hass)
                    client = TauronApiClient(
                        session=session,
                        username=user_input[CONF_USERNAME],
                        password=user_input[CONF_PASSWORD],
                    )
                    await client.authenticate()
                    energy_at_start = await client.fetch_energy_data(billing_start)
                    await client.logout()
                except TauronAuthError:
                    errors["base"] = "invalid_auth"
                except TauronApiError:
                    errors["base"] = "cannot_connect"
                except Exception:
                    _LOGGER.exception("Unexpected error during config flow")
                    errors["base"] = "unknown"

            if not errors:
                return self.async_create_entry(
                    title=f"Tauron ({user_input[CONF_USERNAME]})",
                    data={
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                        CONF_BILLING_PERIOD_START: user_input[CONF_BILLING_PERIOD_START],
                        CONF_PREV_ENERGIA_POBRANA: energy_at_start.energia_pobrana,
                        CONF_PREV_ENERGIA_ODDANA: energy_at_start.energia_oddana,
                    },
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
