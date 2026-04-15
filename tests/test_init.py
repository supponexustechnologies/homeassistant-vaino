"""Tests for Väinö integration setup and teardown."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from custom_components.vaino.const import CONF_HOST, CONF_PORT, DEFAULT_PORT, DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


async def test_setup_entry(hass: HomeAssistant, mock_client) -> None:
    """Test that async_setup_entry stores coordinator and client and forwards platforms."""
    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry"
    entry.data = {CONF_HOST: "192.168.5.248", CONF_PORT: DEFAULT_PORT}

    with (
        patch("custom_components.vaino.VainoApiClient", return_value=mock_client),
        patch("custom_components.vaino.async_get_clientsession", return_value=MagicMock()),
        patch(
            "custom_components.vaino.VainoDataUpdateCoordinator.async_config_entry_first_refresh",
            new_callable=AsyncMock,
        ),
        patch(
            "homeassistant.config_entries.ConfigEntries.async_forward_entry_setups",
            return_value=True,
        ),
    ):
        from custom_components.vaino import async_setup_entry
        result = await async_setup_entry(hass, entry)

    assert result is True
    assert entry.entry_id in hass.data[DOMAIN]
    assert "coordinator" in hass.data[DOMAIN][entry.entry_id]
    assert "client" in hass.data[DOMAIN][entry.entry_id]


async def test_unload_entry(hass: HomeAssistant, mock_client) -> None:
    """Test that async_unload_entry removes data and returns True."""
    entry_id = "test_entry_unload"
    hass.data.setdefault(DOMAIN, {})[entry_id] = {
        "coordinator": MagicMock(),
        "client": mock_client,
    }

    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = entry_id

    with patch(
        "homeassistant.config_entries.ConfigEntries.async_unload_platforms",
        return_value=True,
    ):
        from custom_components.vaino import async_unload_entry
        result = await async_unload_entry(hass, entry)

    assert result is True
    assert entry_id not in hass.data.get(DOMAIN, {})
