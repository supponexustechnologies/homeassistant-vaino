"""Tests for the Väinö config flow."""
from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.vaino.api import CannotConnect, SystemStatus
from custom_components.vaino.const import CONF_HOST, CONF_PORT, DEFAULT_PORT, DOMAIN


MOCK_STATUS = SystemStatus(
    version="1.0.0",
    mpd_connected=True,
    database_track_count=1234,
    uptime="01:23:45",
)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests in this module."""
    yield


async def test_successful_setup(hass: HomeAssistant) -> None:
    """Test the full happy-path config flow."""
    with patch(
        "custom_components.vaino.config_flow.validate_host",
        return_value=MOCK_STATUS.version,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert not result["errors"]

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "192.168.5.248", CONF_PORT: DEFAULT_PORT},
        )

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "Väinö"
    assert result["data"][CONF_HOST] == "192.168.5.248"
    assert result["data"][CONF_PORT] == DEFAULT_PORT


async def test_cannot_connect(hass: HomeAssistant) -> None:
    """Test that a connection failure surfaces the correct error."""
    with patch(
        "custom_components.vaino.config_flow.validate_host",
        side_effect=CannotConnect("Connection refused"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "192.168.5.248", CONF_PORT: DEFAULT_PORT},
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}


async def test_unknown_error(hass: HomeAssistant) -> None:
    """Test that an unexpected exception surfaces the unknown error."""
    with patch(
        "custom_components.vaino.config_flow.validate_host",
        side_effect=Exception("Unexpected"),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "192.168.5.248", CONF_PORT: DEFAULT_PORT},
        )

    assert result["type"] == FlowResultType.FORM
    assert result["errors"] == {"base": "unknown"}


async def test_duplicate_entry_aborted(hass: HomeAssistant) -> None:
    """Test that configuring the same host twice is rejected."""
    with patch(
        "custom_components.vaino.config_flow.validate_host",
        return_value=MOCK_STATUS.version,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_HOST: "192.168.5.248", CONF_PORT: DEFAULT_PORT},
        )

        # Second attempt with the same host
        result2 = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result2 = await hass.config_entries.flow.async_configure(
            result2["flow_id"],
            {CONF_HOST: "192.168.5.248", CONF_PORT: DEFAULT_PORT},
        )

    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "already_configured"
