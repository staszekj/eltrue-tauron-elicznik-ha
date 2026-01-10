"""Data coordinator for Tauron eLicznik."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import logging
from typing import TYPE_CHECKING

from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import TauronApiClient, TauronApiError, TauronEnergyData
from .const import (
    CONF_BILLING_PERIOD_END,
    CONF_PREV_ENERGIA_ODDANA,
    CONF_PREV_ENERGIA_POBRANA,
    DEFAULT_SCAN_INTERVAL_HOURS,
    DOMAIN,
    NET_METERING_RATIO,
)

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)


@dataclass
class TauronCalculatedData:
    """Calculated data from Tauron readings."""

    # Raw meter readings
    energia_pobrana: float
    energia_oddana: float
    reading_date: date

    # Increments since billing period start
    energia_pobrana_increment: float
    energia_oddana_increment: float

    # Net-metering calculations
    kwh_left: float
    days_left: int
    kwh_left_per_day: float
    kwh_left_per_month: float


class TauronElicznikCoordinator(DataUpdateCoordinator[TauronCalculatedData]):
    """Coordinator to manage fetching Tauron eLicznik data."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(hours=DEFAULT_SCAN_INTERVAL_HOURS),
            config_entry=config_entry,
        )

        session = async_get_clientsession(hass)
        self._client = TauronApiClient(
            session=session,
            username=config_entry.data["username"],
            password=config_entry.data["password"],
        )

        # Billing period configuration
        self._billing_period_end = datetime.strptime(
            config_entry.data[CONF_BILLING_PERIOD_END], "%Y-%m-%d"
        ).date()
        self._prev_energia_pobrana = float(config_entry.data[CONF_PREV_ENERGIA_POBRANA])
        self._prev_energia_oddana = float(config_entry.data[CONF_PREV_ENERGIA_ODDANA])

    async def _async_update_data(self) -> TauronCalculatedData:
        """Fetch data from Tauron API and calculate net-metering values."""
        try:
            await self._client.authenticate()
            energy_data = await self._client.fetch_energy_data()
        except TauronApiError as err:
            raise UpdateFailed(f"Error fetching Tauron data: {err}") from err
        finally:
            await self._client.logout()

        return self._calculate_data(energy_data)

    def _calculate_data(self, energy_data: TauronEnergyData) -> TauronCalculatedData:
        """Calculate net-metering values from raw energy data."""
        # Calculate increments since billing period start
        en_pob_increment = energy_data.energia_pobrana - self._prev_energia_pobrana
        en_odd_increment = energy_data.energia_oddana - self._prev_energia_oddana

        # Apply 80% net-metering ratio
        en_odd_increment_80 = NET_METERING_RATIO * en_odd_increment

        # Calculate remaining energy balance
        kwh_left = en_odd_increment_80 - en_pob_increment

        # Calculate days left until billing period end
        today = date.today()
        days_left = (self._billing_period_end - today).days
        days_left = max(days_left, 1)  # Avoid division by zero

        # Calculate daily and monthly budgets
        kwh_left_per_day = kwh_left / days_left
        kwh_left_per_month = 30 * kwh_left_per_day

        return TauronCalculatedData(
            energia_pobrana=energy_data.energia_pobrana,
            energia_oddana=energy_data.energia_oddana,
            reading_date=energy_data.reading_date,
            energia_pobrana_increment=en_pob_increment,
            energia_oddana_increment=en_odd_increment,
            kwh_left=round(kwh_left, 2),
            days_left=days_left,
            kwh_left_per_day=round(kwh_left_per_day, 2),
            kwh_left_per_month=round(kwh_left_per_month, 2),
        )
