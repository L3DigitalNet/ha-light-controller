"""Tests for the Light Controller preset manager module."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from homeassistant.const import STATE_OFF, STATE_ON

from custom_components.ha_light_controller.const import (
    CONF_PRESETS,
    PRESET_BRIGHTNESS_PCT,
    PRESET_COLOR_TEMP_KELVIN,
    PRESET_EFFECT,
    PRESET_ENTITIES,
    PRESET_ID,
    PRESET_NAME,
    PRESET_RGB_COLOR,
    PRESET_SKIP_VERIFICATION,
    PRESET_STATE,
    PRESET_STATUS_ACTIVATING,
    PRESET_STATUS_FAILED,
    PRESET_STATUS_IDLE,
    PRESET_STATUS_SUCCESS,
    PRESET_TARGETS,
    PRESET_TRANSITION,
)
from custom_components.ha_light_controller.preset_manager import (
    PresetConfig,
    PresetManager,
    PresetStatus,
)

# =============================================================================
# PresetConfig Tests
# =============================================================================


class TestPresetConfig:
    """Tests for PresetConfig dataclass."""

    def test_default_values(self):
        """Test default values."""
        preset = PresetConfig(
            id="test_id",
            name="Test Preset",
            entities=["light.test"],
        )
        assert preset.id == "test_id"
        assert preset.name == "Test Preset"
        assert preset.entities == ["light.test"]
        assert preset.state == "on"
        assert preset.brightness_pct == 100
        assert preset.rgb_color is None
        assert preset.color_temp_kelvin is None
        assert preset.effect is None
        assert preset.targets == []
        assert preset.transition == 0.0
        assert preset.skip_verification is False

    def test_from_dict_minimal(self):
        """Test creating from minimal dictionary."""
        data = {
            PRESET_ID: "preset_1",
            PRESET_NAME: "My Preset",
            PRESET_ENTITIES: ["light.a", "light.b"],
        }
        preset = PresetConfig.from_dict(data)
        assert preset.id == "preset_1"
        assert preset.name == "My Preset"
        assert preset.entities == ["light.a", "light.b"]
        assert preset.state == "on"
        assert preset.brightness_pct == 100

    def test_from_dict_full(self):
        """Test creating from full dictionary."""
        data = {
            PRESET_ID: "preset_2",
            PRESET_NAME: "Full Preset",
            PRESET_ENTITIES: ["light.living_room"],
            PRESET_STATE: "on",
            PRESET_BRIGHTNESS_PCT: 75,
            PRESET_RGB_COLOR: [255, 128, 64],
            PRESET_COLOR_TEMP_KELVIN: 4000,
            PRESET_EFFECT: "rainbow",
            PRESET_TARGETS: [{"entity_id": "light.living_room", "brightness_pct": 50}],
            PRESET_TRANSITION: 2.5,
            PRESET_SKIP_VERIFICATION: True,
        }
        preset = PresetConfig.from_dict(data)
        assert preset.id == "preset_2"
        assert preset.name == "Full Preset"
        assert preset.brightness_pct == 75
        assert preset.rgb_color == [255, 128, 64]
        assert preset.color_temp_kelvin == 4000
        assert preset.effect == "rainbow"
        assert preset.transition == 2.5
        assert preset.skip_verification is True

    def test_from_dict_generates_id_if_missing(self):
        """Test that a UUID is generated if ID is missing."""
        data = {
            PRESET_NAME: "No ID Preset",
            PRESET_ENTITIES: ["light.test"],
        }
        preset = PresetConfig.from_dict(data)
        assert preset.id is not None
        assert len(preset.id) == 36  # UUID format

    def test_to_dict(self):
        """Test converting to dictionary."""
        preset = PresetConfig(
            id="test_id",
            name="Test",
            entities=["light.a"],
            state="off",
            brightness_pct=50,
            rgb_color=[255, 0, 0],
            color_temp_kelvin=None,
            effect="pulse",
            targets=[{"entity_id": "light.a", "brightness_pct": 25}],
            transition=1.0,
            skip_verification=True,
        )
        data = preset.to_dict()

        assert data[PRESET_ID] == "test_id"
        assert data[PRESET_NAME] == "Test"
        assert data[PRESET_ENTITIES] == ["light.a"]
        assert data[PRESET_STATE] == "off"
        assert data[PRESET_BRIGHTNESS_PCT] == 50
        assert data[PRESET_RGB_COLOR] == [255, 0, 0]
        assert data[PRESET_COLOR_TEMP_KELVIN] is None
        assert data[PRESET_EFFECT] == "pulse"
        assert data[PRESET_TRANSITION] == 1.0
        assert data[PRESET_SKIP_VERIFICATION] is True


# =============================================================================
# PresetStatus Tests
# =============================================================================


class TestPresetStatus:
    """Tests for PresetStatus dataclass."""

    def test_default_values(self):
        """Test default status values."""
        status = PresetStatus()
        assert status.status == PRESET_STATUS_IDLE
        assert status.last_result is None
        assert status.last_activated is None

    def test_custom_values(self):
        """Test custom status values."""
        status = PresetStatus(
            status=PRESET_STATUS_SUCCESS,
            last_result={"success": True},
            last_activated="2024-01-15T10:30:00",
        )
        assert status.status == PRESET_STATUS_SUCCESS
        assert status.last_result == {"success": True}
        assert status.last_activated == "2024-01-15T10:30:00"


# =============================================================================
# PresetManager Tests
# =============================================================================


class TestPresetManagerInit:
    """Tests for PresetManager initialization."""

    def test_init_empty(self, hass, config_entry):
        """Test initialization with no presets."""
        manager = PresetManager(hass, config_entry)
        assert len(manager.presets) == 0
        assert manager._listeners == []

    def test_init_with_presets(self, hass, config_entry_with_presets):
        """Test initialization with existing presets."""
        manager = PresetManager(hass, config_entry_with_presets)
        assert len(manager.presets) == 2
        assert "preset_1" in manager.presets
        assert "preset_2" in manager.presets

    def test_init_loads_preset_data(self, hass, config_entry_with_presets):
        """Test that preset data is loaded correctly."""
        manager = PresetManager(hass, config_entry_with_presets)
        preset = manager.get_preset("preset_1")
        assert preset is not None
        assert preset.name == "Test Preset"
        assert preset.brightness_pct == 75
        assert preset.color_temp_kelvin == 4000


class TestPresetManagerCRUD:
    """Tests for PresetManager CRUD operations."""

    @pytest.mark.asyncio
    async def test_create_preset(self, hass, config_entry):
        """Test creating a new preset."""
        manager = PresetManager(hass, config_entry)
        preset = await manager.create_preset(
            name="New Preset",
            entities=["light.test"],
            brightness_pct=80,
            rgb_color=[255, 200, 100],
        )

        assert preset is not None
        assert preset.name == "New Preset"
        assert preset.brightness_pct == 80
        assert preset.rgb_color == [255, 200, 100]
        assert preset.id in manager.presets

    @pytest.mark.asyncio
    async def test_create_preset_saves_to_entry(self, hass, config_entry):
        """Test that creating a preset saves to config entry."""
        manager = PresetManager(hass, config_entry)
        await manager.create_preset(
            name="Save Test",
            entities=["light.test"],
        )

        hass.config_entries.async_update_entry.assert_called()

    @pytest.mark.asyncio
    async def test_delete_preset(self, hass, config_entry_with_presets):
        """Test deleting a preset removes data and entity registry entries."""
        from homeassistant.helpers import entity_registry as er

        mock_ent_reg = MagicMock()
        mock_ent_reg.async_get_entity_id = MagicMock(
            side_effect=lambda domain, platform, unique_id: (
                f"{domain}.test_entity" if "preset_1" in unique_id else None
            )
        )
        mock_ent_reg.async_remove = MagicMock()
        er.async_get = MagicMock(return_value=mock_ent_reg)

        manager = PresetManager(hass, config_entry_with_presets)
        assert "preset_1" in manager.presets

        result = await manager.delete_preset("preset_1")

        assert result is True
        assert "preset_1" not in manager.presets

        # Verify entity registry cleanup for both button and sensor
        assert mock_ent_reg.async_get_entity_id.call_count == 2
        assert mock_ent_reg.async_remove.call_count == 2

    @pytest.mark.asyncio
    async def test_delete_preset_entity_registry_error(
        self, hass, config_entry_with_presets
    ):
        """Test deleting a preset when entity registry raises an exception."""
        from homeassistant.helpers import entity_registry as er

        mock_ent_reg = MagicMock()
        mock_ent_reg.async_get_entity_id = MagicMock(
            side_effect=Exception("Registry error")
        )
        er.async_get = MagicMock(return_value=mock_ent_reg)

        manager = PresetManager(hass, config_entry_with_presets)

        # Should still succeed - exception is caught and logged
        result = await manager.delete_preset("preset_1")

        assert result is True
        assert "preset_1" not in manager.presets

    @pytest.mark.asyncio
    async def test_delete_preset_entity_not_in_registry(
        self, hass, config_entry_with_presets
    ):
        """Test delete_preset when entities are not in the registry."""
        manager = PresetManager(hass, config_entry_with_presets)
        # Entity registry returns None by default (from conftest)
        result = await manager.delete_preset("preset_1")
        assert result is True
        assert "preset_1" not in manager.presets

    @pytest.mark.asyncio
    async def test_delete_preset_not_found(self, hass, config_entry):
        """Test deleting a non-existent preset."""
        manager = PresetManager(hass, config_entry)
        result = await manager.delete_preset("nonexistent")
        assert result is False


class TestPresetManagerLookup:
    """Tests for PresetManager lookup methods."""

    def test_get_preset_by_id(self, hass, config_entry_with_presets):
        """Test getting preset by ID."""
        manager = PresetManager(hass, config_entry_with_presets)
        preset = manager.get_preset("preset_1")
        assert preset is not None
        assert preset.name == "Test Preset"

    def test_get_preset_not_found(self, hass, config_entry_with_presets):
        """Test getting non-existent preset."""
        manager = PresetManager(hass, config_entry_with_presets)
        preset = manager.get_preset("nonexistent")
        assert preset is None

    def test_get_preset_by_name(self, hass, config_entry_with_presets):
        """Test getting preset by name."""
        manager = PresetManager(hass, config_entry_with_presets)
        preset = manager.get_preset_by_name("Test Preset")
        assert preset is not None
        assert preset.id == "preset_1"

    def test_get_preset_by_name_case_insensitive(self, hass, config_entry_with_presets):
        """Test getting preset by name is case-insensitive."""
        manager = PresetManager(hass, config_entry_with_presets)
        preset = manager.get_preset_by_name("TEST PRESET")
        assert preset is not None
        assert preset.id == "preset_1"

    def test_get_preset_by_name_not_found(self, hass, config_entry_with_presets):
        """Test getting non-existent preset by name."""
        manager = PresetManager(hass, config_entry_with_presets)
        preset = manager.get_preset_by_name("Nonexistent Preset")
        assert preset is None

    def test_presets_property_returns_copy(self, hass, config_entry_with_presets):
        """Test that presets property returns a copy."""
        manager = PresetManager(hass, config_entry_with_presets)
        presets_copy = manager.presets

        # Modifying the copy should not affect the original
        presets_copy["new_key"] = "test"
        assert "new_key" not in manager._presets


class TestPresetManagerStatus:
    """Tests for PresetManager status tracking."""

    def test_get_status_existing(self, hass, config_entry_with_presets):
        """Test getting status of existing preset."""
        manager = PresetManager(hass, config_entry_with_presets)
        status = manager.get_status("preset_1")
        assert status.status == PRESET_STATUS_IDLE

    def test_get_status_nonexistent(self, hass, config_entry):
        """Test getting status of non-existent preset."""
        manager = PresetManager(hass, config_entry)
        status = manager.get_status("nonexistent")
        assert status.status == PRESET_STATUS_IDLE

    @pytest.mark.asyncio
    async def test_set_status_activating(self, hass, config_entry_with_presets):
        """Test setting status to activating."""
        manager = PresetManager(hass, config_entry_with_presets)
        await manager.set_status("preset_1", PRESET_STATUS_ACTIVATING)

        status = manager.get_status("preset_1")
        assert status.status == PRESET_STATUS_ACTIVATING
        # Activating doesn't set last_activated
        assert status.last_activated is None

    @pytest.mark.asyncio
    async def test_set_status_success(self, hass, config_entry_with_presets):
        """Test setting status to success."""
        manager = PresetManager(hass, config_entry_with_presets)
        result = {"success": True, "message": "Done"}
        await manager.set_status("preset_1", PRESET_STATUS_SUCCESS, result)

        status = manager.get_status("preset_1")
        assert status.status == PRESET_STATUS_SUCCESS
        assert status.last_result == result
        assert status.last_activated is not None

    @pytest.mark.asyncio
    async def test_set_status_failed(self, hass, config_entry_with_presets):
        """Test setting status to failed."""
        manager = PresetManager(hass, config_entry_with_presets)
        result = {"success": False, "message": "Error"}
        await manager.set_status("preset_1", PRESET_STATUS_FAILED, result)

        status = manager.get_status("preset_1")
        assert status.status == PRESET_STATUS_FAILED
        assert status.last_result == result
        assert status.last_activated is not None

    @pytest.mark.asyncio
    async def test_set_status_creates_entry_if_missing(self, hass, config_entry):
        """Test that set_status creates status entry if missing."""
        manager = PresetManager(hass, config_entry)
        await manager.set_status("new_preset", PRESET_STATUS_ACTIVATING)

        status = manager.get_status("new_preset")
        assert status.status == PRESET_STATUS_ACTIVATING


class TestPresetManagerListeners:
    """Tests for PresetManager listener pattern."""

    def test_register_listener(self, hass, config_entry):
        """Test registering a listener."""
        manager = PresetManager(hass, config_entry)
        callback = MagicMock()

        unsubscribe = manager.register_listener(callback)

        assert callable(unsubscribe)
        assert callback in manager._listeners

    def test_unsubscribe_listener(self, hass, config_entry):
        """Test unsubscribing a listener."""
        manager = PresetManager(hass, config_entry)
        callback = MagicMock()

        unsubscribe = manager.register_listener(callback)
        unsubscribe()

        assert callback not in manager._listeners

    @pytest.mark.asyncio
    async def test_listeners_notified_on_create(self, hass, config_entry):
        """Test that listeners are notified when preset is created."""
        manager = PresetManager(hass, config_entry)
        callback = MagicMock()
        manager.register_listener(callback)

        await manager.create_preset(name="Test", entities=["light.test"])

        callback.assert_called()

    @pytest.mark.asyncio
    async def test_listeners_notified_on_delete(self, hass, config_entry_with_presets):
        """Test that listeners are notified when preset is deleted."""
        manager = PresetManager(hass, config_entry_with_presets)
        callback = MagicMock()
        manager.register_listener(callback)

        await manager.delete_preset("preset_1")

        callback.assert_called()

    @pytest.mark.asyncio
    async def test_listeners_notified_on_status_change(
        self, hass, config_entry_with_presets
    ):
        """Test that listeners are notified when status changes."""
        manager = PresetManager(hass, config_entry_with_presets)
        callback = MagicMock()
        manager.register_listener(callback)

        await manager.set_status("preset_1", PRESET_STATUS_SUCCESS)

        # set_status directly awaits _notify_listeners
        callback.assert_called()


class TestPresetManagerCreateFromCurrent:
    """Tests for create_preset_from_current method."""

    @pytest.mark.asyncio
    async def test_create_from_current_basic(self, hass, config_entry):
        """Test creating preset from current light states."""
        from tests.conftest import create_light_state

        states = {
            "light.test_1": create_light_state(
                "light.test_1",
                STATE_ON,
                brightness=191,  # 75%
                color_temp_kelvin=4000,
            ),
            "light.test_2": create_light_state(
                "light.test_2",
                STATE_ON,
                brightness=128,  # 50%
                rgb_color=(255, 0, 0),
            ),
        }
        hass.states.get = lambda e: states.get(e)

        manager = PresetManager(hass, config_entry)
        preset = await manager.create_preset_from_current(
            name="Current State",
            entities=["light.test_1", "light.test_2"],
        )

        assert preset is not None
        assert preset.name == "Current State"
        assert preset.state == "on"
        assert len(preset.targets) == 2

    @pytest.mark.asyncio
    async def test_create_from_current_all_off(self, hass, config_entry):
        """Test creating preset when all lights are off."""
        from tests.conftest import create_light_state

        states = {
            "light.test_1": create_light_state("light.test_1", STATE_OFF),
            "light.test_2": create_light_state("light.test_2", STATE_OFF),
        }
        hass.states.get = lambda e: states.get(e)

        manager = PresetManager(hass, config_entry)
        preset = await manager.create_preset_from_current(
            name="All Off",
            entities=["light.test_1", "light.test_2"],
        )

        assert preset is not None
        assert preset.state == "off"
        assert len(preset.targets) == 2
        assert all(target.get("state") == "off" for target in preset.targets)

    @pytest.mark.asyncio
    async def test_create_from_current_mixed_states(self, hass, config_entry):
        """Test creating preset with mixed on/off states."""
        from tests.conftest import create_light_state

        states = {
            "light.test_1": create_light_state(
                "light.test_1",
                STATE_ON,
                brightness=255,
            ),
            "light.test_2": create_light_state("light.test_2", STATE_OFF),
        }
        hass.states.get = lambda e: states.get(e)

        manager = PresetManager(hass, config_entry)
        preset = await manager.create_preset_from_current(
            name="Mixed",
            entities=["light.test_1", "light.test_2"],
        )

        assert preset is not None
        assert preset.state == "on"  # any_on = True
        assert len(preset.targets) == 2
        assert {target.get("state") for target in preset.targets} == {"on", "off"}

    @pytest.mark.asyncio
    async def test_create_from_current_no_entities(self, hass, config_entry):
        """Test creating preset with no entities returns None."""
        manager = PresetManager(hass, config_entry)
        preset = await manager.create_preset_from_current(
            name="Empty",
            entities=[],
        )

        assert preset is None

    @pytest.mark.asyncio
    async def test_create_from_current_captures_effect(self, hass, config_entry):
        """Test that effect is captured from current state."""
        from tests.conftest import create_light_state

        states = {
            "light.test_1": create_light_state(
                "light.test_1",
                STATE_ON,
                brightness=255,
                effect="rainbow",
            ),
        }
        hass.states.get = lambda e: states.get(e)

        manager = PresetManager(hass, config_entry)
        preset = await manager.create_preset_from_current(
            name="With Effect",
            entities=["light.test_1"],
        )

        assert preset is not None
        assert len(preset.targets) == 1
        assert preset.targets[0].get("effect") == "rainbow"

    @pytest.mark.asyncio
    async def test_create_from_current_ignores_none_effect(self, hass, config_entry):
        """Test that 'none' effect is not captured."""
        from tests.conftest import create_light_state

        states = {
            "light.test_1": create_light_state(
                "light.test_1",
                STATE_ON,
                brightness=255,
                effect="none",
            ),
        }
        hass.states.get = lambda e: states.get(e)

        manager = PresetManager(hass, config_entry)
        preset = await manager.create_preset_from_current(
            name="No Effect",
            entities=["light.test_1"],
        )

        assert preset is not None
        target = preset.targets[0]
        assert "effect" not in target

    @pytest.mark.asyncio
    async def test_create_from_current_entity_state_none(self, hass, config_entry):
        """Test creating preset when entity state is None."""
        from tests.conftest import create_light_state

        states = {
            "light.test_1": create_light_state(
                "light.test_1",
                STATE_ON,
                brightness=255,
            ),
            "light.test_2": None,  # Entity not found
        }
        hass.states.get = lambda e: states.get(e)

        manager = PresetManager(hass, config_entry)
        preset = await manager.create_preset_from_current(
            name="With Missing Entity",
            entities=["light.test_1", "light.test_2"],
        )

        assert preset is not None
        # Should only have target for existing entity
        assert len(preset.targets) == 1
        assert preset.targets[0]["entity_id"] == "light.test_1"
        assert preset.targets[0]["state"] == "on"

    @pytest.mark.asyncio
    async def test_create_from_current_color_temperature_kelvin_attr(
        self, hass, config_entry
    ):
        """Test that color_temperature_kelvin attribute is captured."""
        # Some lights use color_temperature_kelvin instead of color_temp_kelvin
        state = MagicMock()
        state.state = STATE_ON
        state.attributes = {
            "brightness": 255,
            "color_temperature_kelvin": 5000,  # Alternative attr name
        }

        hass.states.get = lambda e: state if e == "light.test_1" else None

        manager = PresetManager(hass, config_entry)
        preset = await manager.create_preset_from_current(
            name="Alt Kelvin Attr",
            entities=["light.test_1"],
        )

        assert preset is not None
        target = preset.targets[0]
        assert target.get("color_temp_kelvin") == 5000


class TestPresetManagerErrorHandling:
    """Tests for PresetManager error handling."""

    def test_load_preset_with_invalid_data(self, hass):
        """Test loading preset with invalid data logs error but doesn't crash."""
        entry = MagicMock()
        entry.entry_id = "test_entry"
        entry.data = {
            CONF_PRESETS: {
                "valid_preset": {
                    PRESET_ID: "valid_preset",
                    PRESET_NAME: "Valid",
                    PRESET_ENTITIES: ["light.test"],
                },
                "invalid_preset": "not_a_dict",  # Invalid data
            }
        }
        entry.options = {}

        # Should not raise, just log error
        manager = PresetManager(hass, entry)
        # Valid preset should still be loaded
        assert "valid_preset" in manager.presets

    @pytest.mark.asyncio
    async def test_notify_listener_exception(self, hass, config_entry):
        """Test that exception in listener doesn't crash notification."""
        manager = PresetManager(hass, config_entry)

        # Register a failing listener
        def failing_listener():
            raise Exception("Listener error")

        manager.register_listener(failing_listener)

        # Also register a working listener
        working_callback = MagicMock()
        manager.register_listener(working_callback)

        # Should not raise, should continue notifying
        await manager._notify_listeners()

        # Working listener should still be called
        working_callback.assert_called_once()

    def test_unsubscribe_listener_twice(self, hass, config_entry):
        """Test that unsubscribing twice doesn't crash."""
        manager = PresetManager(hass, config_entry)
        callback = MagicMock()

        unsubscribe = manager.register_listener(callback)
        unsubscribe()
        # Second unsubscribe should not raise
        unsubscribe()

        assert callback not in manager._listeners


class TestCoverageGaps:
    """Tests to close coverage gaps in preset_manager.py."""

    def test_find_preset_by_name(self, hass, config_entry_with_presets):
        """Test find_preset falls back to get_preset_by_name when ID lookup fails.

        Covers line 212: the 'or' short-circuit in find_preset().
        When given a name instead of ID, get_preset() returns None,
        so find_preset() falls through to get_preset_by_name().
        """
        manager = PresetManager(hass, config_entry_with_presets)
        # "Test Preset" is the name of preset_1 in config_entry_with_presets
        result = manager.find_preset("Test Preset")
        assert result is not None
        assert result.name == "Test Preset"
        assert result.id == "preset_1"

    @pytest.mark.asyncio
    async def test_activate_preset_with_options(self, hass, config_entry_with_presets):
        """Test activate_preset_with_options calls controller.ensure_state.

        Covers line 410: return await controller.ensure_state(...)
        """
        from unittest.mock import AsyncMock

        manager = PresetManager(hass, config_entry_with_presets)
        preset = manager.get_preset("preset_1")

        mock_controller = MagicMock()
        mock_controller.ensure_state = AsyncMock(
            return_value={"success": True, "result": "success"}
        )

        result = await manager.activate_preset_with_options(
            preset, mock_controller, config_entry_with_presets.options
        )

        assert result["success"] is True
        mock_controller.ensure_state.assert_called_once()
        call_kwargs = mock_controller.ensure_state.call_args[1]
        assert call_kwargs["entities"] == preset.entities
        assert call_kwargs["state_target"] == preset.state
        assert call_kwargs["default_brightness_pct"] == preset.brightness_pct

    @pytest.mark.asyncio
    async def test_create_preset_from_current_light_on_no_brightness(
        self, hass, config_entry
    ):
        """Test create_preset_from_current when light is ON but has no brightness.

        Covers branch 354→359: the False path when "brightness" not in attrs.
        Light is on but doesn't have a brightness attribute.
        """
        from tests.conftest import State

        manager = PresetManager(hass, config_entry)
        # Light is ON but has no brightness attribute
        state = State("light.test", STATE_ON, {})
        hass.states.get = MagicMock(return_value=state)

        preset = await manager.create_preset_from_current(
            "No Brightness", ["light.test"]
        )

        assert preset is not None
        # Verify no brightness_pct in target since source had none
        target = preset.targets[0]
        assert "brightness_pct" not in target
        assert target["entity_id"] == "light.test"


class TestPresetNameUniqueness:
    """Tests for case-insensitive preset name uniqueness (PLR-005)."""

    @pytest.mark.asyncio
    async def test_create_duplicate_name_raises(self, hass, config_entry):
        """Creating a preset with a name that already exists raises ValueError."""
        manager = PresetManager(hass, config_entry)
        await manager.create_preset(name="Living Room", entities=["light.a"])

        with pytest.raises(ValueError, match="already exists"):
            await manager.create_preset(name="living room", entities=["light.b"])

    @pytest.mark.asyncio
    async def test_create_different_name_succeeds(self, hass, config_entry):
        """Creating a preset with a unique name succeeds."""
        manager = PresetManager(hass, config_entry)
        p1 = await manager.create_preset(name="Living Room", entities=["light.a"])
        p2 = await manager.create_preset(name="Bedroom", entities=["light.b"])
        assert p1.name != p2.name

    @pytest.mark.asyncio
    async def test_update_same_name_succeeds(self, hass, config_entry):
        """Updating a preset to keep its own name succeeds."""
        manager = PresetManager(hass, config_entry)
        p = await manager.create_preset(name="Living Room", entities=["light.a"])
        updated = await manager.update_preset(
            p.id, name="Living Room", entities=["light.b"]
        )
        assert updated is not None
        assert updated.entities == ["light.b"]

    @pytest.mark.asyncio
    async def test_update_to_taken_name_raises(self, hass, config_entry):
        """Updating a preset to use another preset's name raises ValueError."""
        manager = PresetManager(hass, config_entry)
        await manager.create_preset(name="Living Room", entities=["light.a"])
        p2 = await manager.create_preset(name="Bedroom", entities=["light.b"])

        with pytest.raises(ValueError, match="already exists"):
            await manager.update_preset(p2.id, name="LIVING ROOM", entities=["light.b"])
