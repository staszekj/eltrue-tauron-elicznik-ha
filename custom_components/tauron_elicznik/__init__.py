"""The Tauron eLicznik integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN as DOMAIN
from .coordinator import TauronElicznikCoordinator

PLATFORMS: list[Platform] = [Platform.BUTTON, Platform.SENSOR]

type TauronElicznikConfigEntry = ConfigEntry[TauronElicznikCoordinator]


async def async_setup_entry(
    hass: HomeAssistant, entry: TauronElicznikConfigEntry
) -> bool:
    """Set up Tauron eLicznik from a config entry."""
    coordinator = TauronElicznikCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(
    hass: HomeAssistant, entry: TauronElicznikConfigEntry
) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
