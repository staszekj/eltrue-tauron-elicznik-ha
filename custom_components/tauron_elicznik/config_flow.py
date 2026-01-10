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
    CONF_BILLING_PERIOD_END,
    CONF_PREV_ENERGIA_ODDANA,
    CONF_PREV_ENERGIA_POBRANA,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


def _get_default_billing_end() -> str:
    """Get default billing period end (end of current month)."""
    today = datetime.now()
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
    last_day = (next_month - datetime.resolution).day
    return today.replace(day=last_day).strftime("%Y-%m-%d")


STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Required(CONF_BILLING_PERIOD_END, default=_get_default_billing_end()): str,
        vol.Required(CONF_PREV_ENERGIA_POBRANA, default=0): vol.Coerce(float),
        vol.Required(CONF_PREV_ENERGIA_ODDANA, default=0): vol.Coerce(float),
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
            # Validate date format
            try:
                datetime.strptime(user_input[CONF_BILLING_PERIOD_END], "%Y-%m-%d")
            except ValueError:
                errors["base"] = "invalid_date"

            if not errors:
                # Set unique ID based on username to prevent duplicates
                await self.async_set_unique_id(user_input[CONF_USERNAME].lower())
                self._abort_if_unique_id_configured()

                # Test connection
                try:
                    session = async_get_clientsession(self.hass)
                    client = TauronApiClient(
                        session=session,
                        username=user_input[CONF_USERNAME],
                        password=user_input[CONF_PASSWORD],
                    )
                    await client.test_connection()
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
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )
