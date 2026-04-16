"""Tests for diagnostics."""

from unittest.mock import MagicMock

import pytest

# The conftest.py mocks are loaded before this import
from custom_components.ha_light_controller.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.ha_light_controller.preset_manager import PresetManager


class TestDiagnostics:
    """Test diagnostics output."""

    @pytest.mark.asyncio
    async def test_diagnostics_basic(self, hass, config_entry):
        """Test basic diagnostics output."""
        result = await async_get_config_entry_diagnostics(hass, config_entry)

        assert "config_entry_data" in result
        assert "options" in result
        assert "preset_count" in result
        assert "presets" in result
        assert "runtime_status" in result
        assert result["preset_count"] == 0
        assert result["presets"] == {}

    @pytest.mark.asyncio
    async def test_diagnostics_with_presets(self, hass, config_entry_with_presets):
        """Test diagnostics with presets configured."""
        result = await async_get_config_entry_diagnostics(
            hass, config_entry_with_presets
        )

        assert result["preset_count"] == 2
        assert len(result["presets"]) == 2

        # Verify preset data is summarized (not full config dump)
        for preset_info in result["presets"].values():
            assert "name" in preset_info
            assert "entity_count" in preset_info
            assert "state" in preset_info
            assert "has_targets" in preset_info
            assert "skip_verification" in preset_info

    @pytest.mark.asyncio
    async def test_diagnostics_excludes_raw_presets(
        self, hass, config_entry_with_presets
    ):
        """Test that raw preset data is excluded from config_entry_data."""
        result = await async_get_config_entry_diagnostics(
            hass, config_entry_with_presets
        )

        # CONF_PRESETS should not appear in config_entry_data
        assert "presets" not in result["config_entry_data"]

    @pytest.mark.asyncio
    async def test_diagnostics_options(self, hass, config_entry_with_presets):
        """Test that options are included."""
        result = await async_get_config_entry_diagnostics(
            hass, config_entry_with_presets
        )

        assert result["options"] == {
            "default_brightness_pct": 100,
            "brightness_tolerance": 5,
        }

    @pytest.mark.asyncio
    async def test_diagnostics_preset_names_redacted(
        self, hass, config_entry_with_presets
    ):
        """Test preset names are redacted in diagnostics output."""
        result = await async_get_config_entry_diagnostics(
            hass, config_entry_with_presets
        )

        preset_1 = result["presets"]["preset_1"]
        assert preset_1["name"] == "**REDACTED**"
        assert preset_1["entity_count"] == 2
        assert preset_1["state"] == "on"
        assert preset_1["has_targets"] is False
        assert preset_1["skip_verification"] is False

    @pytest.mark.asyncio
    async def test_diagnostics_runtime_status(self, hass, config_entry_with_presets):
        """Test diagnostics includes runtime preset status when loaded."""
        pm = PresetManager(hass, config_entry_with_presets)
        runtime_data = MagicMock()
        runtime_data.preset_manager = pm
        config_entry_with_presets.runtime_data = runtime_data

        result = await async_get_config_entry_diagnostics(
            hass, config_entry_with_presets
        )

        assert "runtime_status" in result
        assert "preset_1" in result["runtime_status"]
        assert result["runtime_status"]["preset_1"]["status"] == "idle"
