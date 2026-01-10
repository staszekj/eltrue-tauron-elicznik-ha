"""Button platform for Tauron eLicznik."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import TauronElicznikConfigEntry
from .const import DOMAIN
from .coordinator import TauronElicznikCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TauronElicznikConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Tauron eLicznik button from a config entry."""
    coordinator = entry.runtime_data
    async_add_entities([TauronElicznikRefreshButton(coordinator, entry)])


class TauronElicznikRefreshButton(
    CoordinatorEntity[TauronElicznikCoordinator], ButtonEntity
):
    """Button to manually refresh Tauron eLicznik data."""

    _attr_has_entity_name = True
    _attr_translation_key = "refresh"

    def __init__(
        self,
        coordinator: TauronElicznikCoordinator,
        entry: TauronElicznikConfigEntry,
    ) -> None:
        """Initialize the refresh button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry.entry_id}_refresh"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="Tauron eLicznik",
            manufacturer="Tauron Dystrybucja",
            model="eLicznik",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        await self.coordinator.async_request_refresh()
