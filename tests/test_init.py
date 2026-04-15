"""Tests for Väinö integration setup and teardown."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntryState

from custom_components.vaino.const import CONF_HOST, CONF_PORT, DEFAULT_PORT, DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    yield


async def test_setup_entry(hass: HomeAssistant, mock_client) -> None:
    """Test that a config entry sets up cleanly."""
    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.data = {CONF_HOST: "192.168.5.248", CONF_PORT: DEFAULT_PORT}

    with (
        patch("custom_components.vaino.VainoApiClient", return_value=mock_client),
        patch("custom_components.vaino.async_get_clientsession"),
        patch("custom_components.vaino.hass.config_entries.async_forward_entry_setups", return_value=True),
    ):
        from custom_components.vaino import async_setup_entry
        result = await async_setup_entry(hass, entry)

    assert result is True
    assert DOMAIN in hass.data
    assert "coordinator" in hass.data[DOMAIN][entry.entry_id]
    assert "client" in hass.data[DOMAIN][entry.entry_id]


async def test_unload_entry(hass: HomeAssistant, mock_client) -> None:
    """Test that a config entry unloads cleanly."""
    entry_id = "test_entry_unload"
    hass.data.setdefault(DOMAIN, {})[entry_id] = {
        "coordinator": MagicMock(),
        "client": mock_client,
    }

    entry = MagicMock()
    entry.entry_id = entry_id

    with patch(
        "custom_components.vaino.hass.config_entries.async_unload_platforms",
        return_value=True,
    ):
        from custom_components.vaino import async_unload_entry
        result = await async_unload_entry(hass, entry)

    assert result is True
    assert entry_id not in hass.data.get(DOMAIN, {})
