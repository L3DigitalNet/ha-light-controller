"""Tests for the Light Controller config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.config_entries import ConfigEntry
from homeassistant.data_entry_flow import FlowResultType

from custom_components.ha_light_controller.config_flow import (
    LightControllerConfigFlow,
    LightControllerOptionsFlow,
)
from custom_components.ha_light_controller.const import (
    COLOR_MODE_COLOR_TEMP,
    COLOR_MODE_NONE,
    COLOR_MODE_RGB,
    CONF_BRIGHTNESS_TOLERANCE,
    CONF_DEFAULT_BRIGHTNESS_PCT,
    CONF_DEFAULT_TRANSITION,
    CONF_DELAY_AFTER_SEND,
    CONF_KELVIN_TOLERANCE,
    CONF_LOG_SUCCESS,
    CONF_MAX_BACKOFF_SECONDS,
    CONF_MAX_RETRIES,
    CONF_MAX_RUNTIME_SECONDS,
    CONF_RGB_TOLERANCE,
    CONF_USE_EXPONENTIAL_BACKOFF,
    DEFAULT_BRIGHTNESS_PCT,
    DEFAULT_TRANSITION,
    PRESET_BRIGHTNESS_PCT,
    PRESET_COLOR_MODE,
    PRESET_COLOR_TEMP_KELVIN,
    PRESET_ENTITIES,
    PRESET_NAME,
    PRESET_RGB_COLOR,
    PRESET_SKIP_VERIFICATION,
    PRESET_STATE,
    PRESET_TRANSITION,
)

# =============================================================================
# ConfigFlow Tests
# =============================================================================


class TestLightControllerConfigFlow:
    """Tests for the initial config flow."""

    @pytest.mark.asyncio
    async def test_step_user_form(self, hass):
        """Test that the user step shows a form."""
        flow = LightControllerConfigFlow()
        flow.hass = hass
        flow.context = {}

        result = await flow.async_step_user()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"
        assert result["errors"] == {}

    @pytest.mark.asyncio
    async def test_step_user_creates_entry(self, hass):
        """Test that submitting the form creates an entry."""
        flow = LightControllerConfigFlow()
        flow.hass = hass
        flow.context = {}

        # Mock the unique ID methods
        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        result = await flow.async_step_user(
            user_input={
                CONF_DEFAULT_BRIGHTNESS_PCT: 80,
                CONF_DEFAULT_TRANSITION: 1.5,
            }
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["title"] == "Light Controller"
        assert result["data"] == {}
        assert result["options"][CONF_DEFAULT_BRIGHTNESS_PCT] == 80
        assert result["options"][CONF_DEFAULT_TRANSITION] == 1.5

    @pytest.mark.asyncio
    async def test_step_user_uses_defaults(self, hass):
        """Test that missing values use defaults."""
        flow = LightControllerConfigFlow()
        flow.hass = hass
        flow.context = {}

        flow.async_set_unique_id = AsyncMock()
        flow._abort_if_unique_id_configured = MagicMock()

        result = await flow.async_step_user(user_input={})

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["options"][CONF_DEFAULT_BRIGHTNESS_PCT] == DEFAULT_BRIGHTNESS_PCT
        assert result["options"][CONF_DEFAULT_TRANSITION] == DEFAULT_TRANSITION

    def test_async_get_options_flow(self):
        """Test that options flow handler is returned."""
        entry = MagicMock(spec=ConfigEntry)
        flow = LightControllerConfigFlow.async_get_options_flow(entry)
        assert isinstance(flow, LightControllerOptionsFlow)


# =============================================================================
# OptionsFlow Tests
# =============================================================================


class TestLightControllerOptionsFlow:
    """Tests for the options flow."""

    @pytest.fixture
    def options_flow(self, config_entry):
        """Create an options flow instance."""
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        return flow

    @pytest.mark.asyncio
    async def test_step_init_shows_menu(self, options_flow, hass):
        """Test that init step shows menu."""
        options_flow.hass = hass

        result = await options_flow.async_step_init()

        assert result["type"] == FlowResultType.MENU
        assert "settings" in result["menu_options"]
        assert "add_preset" in result["menu_options"]
        assert "manage_presets" in result["menu_options"]

    @pytest.mark.asyncio
    async def test_step_settings_form(self, options_flow, hass):
        """Test settings step shows form with all configuration options."""
        options_flow.hass = hass

        result = await options_flow.async_step_settings()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "settings"

    @pytest.mark.asyncio
    async def test_step_settings_saves(self, options_flow, hass):
        """Test settings step saves all options."""
        options_flow.hass = hass

        result = await options_flow.async_step_settings(
            user_input={
                CONF_DEFAULT_BRIGHTNESS_PCT: 90,
                CONF_DEFAULT_TRANSITION: 2.0,
                CONF_BRIGHTNESS_TOLERANCE: 5,
                CONF_RGB_TOLERANCE: 15,
                CONF_KELVIN_TOLERANCE: 200,
                CONF_DELAY_AFTER_SEND: 3.0,
                CONF_MAX_RETRIES: 5,
                CONF_MAX_RUNTIME_SECONDS: 120.0,
                CONF_USE_EXPONENTIAL_BACKOFF: True,
                CONF_MAX_BACKOFF_SECONDS: 60.0,
                CONF_LOG_SUCCESS: True,
            }
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        assert result["data"][CONF_DEFAULT_BRIGHTNESS_PCT] == 90
        assert result["data"][CONF_DEFAULT_TRANSITION] == 2.0
        assert result["data"][CONF_BRIGHTNESS_TOLERANCE] == 5
        assert result["data"][CONF_RGB_TOLERANCE] == 15
        assert result["data"][CONF_KELVIN_TOLERANCE] == 200
        assert result["data"][CONF_DELAY_AFTER_SEND] == 3.0
        assert result["data"][CONF_MAX_RETRIES] == 5
        assert result["data"][CONF_USE_EXPONENTIAL_BACKOFF] is True
        assert result["data"][CONF_LOG_SUCCESS] is True


class TestOptionsFlowAddPreset:
    """Tests for the add_preset options flow steps (multi-step flow)."""

    @pytest.fixture
    def options_flow_with_manager(self, config_entry, hass):
        """Create options flow with mock preset manager."""
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        flow.hass = hass

        # Set up mock preset manager in runtime_data
        preset_manager = MagicMock()
        preset_manager.create_preset = AsyncMock()

        runtime_data = MagicMock()
        runtime_data.preset_manager = preset_manager
        config_entry.runtime_data = runtime_data

        # Mock hass.states.get for friendly name lookup
        mock_state = MagicMock()
        mock_state.attributes = {"friendly_name": "Test Light"}
        hass.states.get = MagicMock(return_value=mock_state)

        return flow, preset_manager

    @pytest.mark.asyncio
    async def test_step_add_preset_form(self, options_flow_with_manager):
        """Test add_preset step shows form with name, entities, and skip_verification."""
        flow, _ = options_flow_with_manager

        result = await flow.async_step_add_preset()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "add_preset"

    @pytest.mark.asyncio
    async def test_step_add_preset_goes_to_entity_menu(self, options_flow_with_manager):
        """Test add_preset step proceeds to preset_entity_menu after valid input."""
        flow, _ = options_flow_with_manager

        result = await flow.async_step_add_preset(
            user_input={
                PRESET_NAME: "New Preset",
                PRESET_ENTITIES: ["light.test"],
                PRESET_SKIP_VERIFICATION: False,
            }
        )

        # Should go to entity menu, not create entry directly
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "preset_entity_menu"
        # Verify preset data was stored
        assert flow._preset_data[PRESET_NAME] == "New Preset"
        assert flow._preset_data[PRESET_ENTITIES] == ["light.test"]

    @pytest.mark.asyncio
    async def test_step_add_preset_validates_name(self, options_flow_with_manager):
        """Test add_preset validates name is required."""
        flow, _ = options_flow_with_manager

        result = await flow.async_step_add_preset(
            user_input={
                PRESET_NAME: "",
                PRESET_ENTITIES: ["light.test"],
            }
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "name_required"

    @pytest.mark.asyncio
    async def test_step_add_preset_validates_entities(self, options_flow_with_manager):
        """Test add_preset validates entities are required."""
        flow, _ = options_flow_with_manager

        result = await flow.async_step_add_preset(
            user_input={
                PRESET_NAME: "Test",
                PRESET_ENTITIES: [],
            }
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "entities_required"

    @pytest.mark.asyncio
    async def test_step_preset_entity_menu_shows_actions(
        self, options_flow_with_manager
    ):
        """Test preset_entity_menu shows available actions."""
        flow, _ = options_flow_with_manager
        # Set up preset data as if we came from add_preset
        flow._preset_data = {
            PRESET_NAME: "Test Preset",
            PRESET_ENTITIES: ["light.test"],
            PRESET_SKIP_VERIFICATION: False,
            "targets": {},
        }

        result = await flow.async_step_preset_entity_menu()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "preset_entity_menu"
        assert "preset_name" in result["description_placeholders"]
        assert result["description_placeholders"]["preset_name"] == "Test Preset"

    @pytest.mark.asyncio
    async def test_step_preset_entity_menu_requires_configuration(
        self, options_flow_with_manager
    ):
        """Test preset_entity_menu requires at least one entity to be configured."""
        flow, _ = options_flow_with_manager
        flow._preset_data = {
            PRESET_NAME: "Test Preset",
            PRESET_ENTITIES: ["light.test"],
            PRESET_SKIP_VERIFICATION: False,
            "targets": {},  # No entities configured yet
        }

        result = await flow.async_step_preset_entity_menu(user_input={"action": "save"})

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "configure_at_least_one"

    @pytest.mark.asyncio
    async def test_step_select_entity_to_configure(self, options_flow_with_manager):
        """Test select_entity_to_configure shows entity list."""
        flow, _ = options_flow_with_manager
        flow._preset_data = {
            PRESET_NAME: "Test Preset",
            PRESET_ENTITIES: ["light.test1", "light.test2"],
            PRESET_SKIP_VERIFICATION: False,
            "targets": {},
        }

        result = await flow.async_step_select_entity_to_configure()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "select_entity_to_configure"

    @pytest.mark.asyncio
    async def test_step_configure_entity_form(self, options_flow_with_manager):
        """Test configure_entity shows form for entity settings."""
        flow, _ = options_flow_with_manager
        flow._preset_data = {
            PRESET_NAME: "Test Preset",
            PRESET_ENTITIES: ["light.test"],
            PRESET_SKIP_VERIFICATION: False,
            "targets": {},
        }
        flow._configuring_entity = "light.test"

        result = await flow.async_step_configure_entity()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "configure_entity"
        assert "entity_name" in result["description_placeholders"]

    @pytest.mark.asyncio
    async def test_step_configure_entity_saves_on_state(
        self, options_flow_with_manager
    ):
        """Test configure_entity saves 'on' state configuration."""
        flow, _ = options_flow_with_manager
        flow._preset_data = {
            PRESET_NAME: "Test Preset",
            PRESET_ENTITIES: ["light.test"],
            PRESET_SKIP_VERIFICATION: False,
            "targets": {},
        }
        flow._configuring_entity = "light.test"

        result = await flow.async_step_configure_entity(
            user_input={
                PRESET_STATE: "on",
                PRESET_TRANSITION: 1.5,
                PRESET_BRIGHTNESS_PCT: 75,
                PRESET_COLOR_MODE: COLOR_MODE_COLOR_TEMP,
                PRESET_COLOR_TEMP_KELVIN: 4000,
            }
        )

        # Should return to entity menu
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "preset_entity_menu"
        # Verify target was stored
        assert "light.test" in flow._preset_data["targets"]
        target = flow._preset_data["targets"]["light.test"]
        assert target["state"] == "on"
        assert target["brightness_pct"] == 75
        assert target["color_temp_kelvin"] == 4000
        assert target["transition"] == 1.5

    @pytest.mark.asyncio
    async def test_step_configure_entity_saves_off_state(
        self, options_flow_with_manager
    ):
        """Test configure_entity saves 'off' state without brightness/color."""
        flow, _ = options_flow_with_manager
        flow._preset_data = {
            PRESET_NAME: "Test Preset",
            PRESET_ENTITIES: ["light.test"],
            PRESET_SKIP_VERIFICATION: False,
            "targets": {},
        }
        flow._configuring_entity = "light.test"

        result = await flow.async_step_configure_entity(
            user_input={
                PRESET_STATE: "off",
                PRESET_TRANSITION: 2.0,
                PRESET_BRIGHTNESS_PCT: 100,  # Should be ignored for off state
                PRESET_COLOR_MODE: COLOR_MODE_NONE,
            }
        )

        assert result["type"] == FlowResultType.FORM
        target = flow._preset_data["targets"]["light.test"]
        assert target["state"] == "off"
        assert "brightness_pct" not in target  # Not saved for off state
        assert "color_temp_kelvin" not in target

    @pytest.mark.asyncio
    async def test_step_configure_entity_rgb_color(self, options_flow_with_manager):
        """Test configure_entity saves RGB color configuration."""
        flow, _ = options_flow_with_manager
        flow._preset_data = {
            PRESET_NAME: "Test Preset",
            PRESET_ENTITIES: ["light.test"],
            PRESET_SKIP_VERIFICATION: False,
            "targets": {},
        }
        flow._configuring_entity = "light.test"

        await flow.async_step_configure_entity(
            user_input={
                PRESET_STATE: "on",
                PRESET_TRANSITION: 0,
                PRESET_BRIGHTNESS_PCT: 80,
                PRESET_COLOR_MODE: COLOR_MODE_RGB,
                PRESET_RGB_COLOR: [255, 128, 64],
            }
        )

        target = flow._preset_data["targets"]["light.test"]
        assert target["rgb_color"] == [255, 128, 64]

    @pytest.mark.asyncio
    async def test_step_add_more_entities(self, options_flow_with_manager):
        """Test add_more_entities adds entities to preset."""
        flow, _ = options_flow_with_manager
        flow._preset_data = {
            PRESET_NAME: "Test Preset",
            PRESET_ENTITIES: ["light.test1"],
            PRESET_SKIP_VERIFICATION: False,
            "targets": {},
        }

        result = await flow.async_step_add_more_entities(
            user_input={"new_entities": ["light.test2", "light.test3"]}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "preset_entity_menu"
        assert "light.test2" in flow._preset_data[PRESET_ENTITIES]
        assert "light.test3" in flow._preset_data[PRESET_ENTITIES]

    @pytest.mark.asyncio
    async def test_step_add_more_entities_no_duplicates(
        self, options_flow_with_manager
    ):
        """Test add_more_entities doesn't add duplicate entities."""
        flow, _ = options_flow_with_manager
        flow._preset_data = {
            PRESET_NAME: "Test Preset",
            PRESET_ENTITIES: ["light.test1"],
            PRESET_SKIP_VERIFICATION: False,
            "targets": {},
        }

        await flow.async_step_add_more_entities(
            user_input={"new_entities": ["light.test1", "light.test2"]}
        )

        # light.test1 should only appear once
        assert flow._preset_data[PRESET_ENTITIES].count("light.test1") == 1
        assert "light.test2" in flow._preset_data[PRESET_ENTITIES]

    @pytest.mark.asyncio
    async def test_step_remove_entity(self, options_flow_with_manager):
        """Test remove_entity removes entity from preset."""
        flow, _ = options_flow_with_manager
        flow._preset_data = {
            PRESET_NAME: "Test Preset",
            PRESET_ENTITIES: ["light.test1", "light.test2"],
            PRESET_SKIP_VERIFICATION: False,
            "targets": {"light.test1": {"entity_id": "light.test1", "state": "on"}},
        }

        result = await flow.async_step_remove_entity(
            user_input={"entity_to_remove": "light.test1"}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "preset_entity_menu"
        assert "light.test1" not in flow._preset_data[PRESET_ENTITIES]
        assert "light.test1" not in flow._preset_data["targets"]

    @pytest.mark.asyncio
    async def test_step_remove_entity_prevents_last_removal(
        self, options_flow_with_manager
    ):
        """Test cannot remove last entity from preset."""
        flow, _ = options_flow_with_manager
        flow._preset_data = {
            PRESET_NAME: "Test Preset",
            PRESET_ENTITIES: ["light.test1"],  # Only one entity
            PRESET_SKIP_VERIFICATION: False,
            "targets": {},
        }

        result = await flow.async_step_preset_entity_menu(
            user_input={"action": "remove"}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "cannot_remove_last"

    @pytest.mark.asyncio
    async def test_create_preset_from_data(self, options_flow_with_manager):
        """Test _create_preset_from_data creates preset with configured targets."""
        flow, preset_manager = options_flow_with_manager
        flow._preset_data = {
            PRESET_NAME: "Test Preset",
            PRESET_ENTITIES: ["light.test1", "light.test2"],
            PRESET_SKIP_VERIFICATION: True,
            "targets": {
                "light.test1": {
                    "entity_id": "light.test1",
                    "state": "on",
                    "brightness_pct": 75,
                },
                "light.test2": {"entity_id": "light.test2", "state": "off"},
            },
        }

        result = await flow._create_preset_from_data()

        assert result["type"] == FlowResultType.CREATE_ENTRY
        preset_manager.create_preset.assert_called_once()
        call_kwargs = preset_manager.create_preset.call_args.kwargs
        assert call_kwargs["name"] == "Test Preset"
        assert len(call_kwargs["targets"]) == 2
        assert call_kwargs["skip_verification"] is True


class TestOptionsFlowManagePresets:
    """Tests for the manage_presets options flow step."""

    @pytest.fixture
    def options_flow_with_presets(self, config_entry_with_presets, hass):
        """Create options flow with mock preset manager containing presets."""
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry_with_presets
        flow.hass = hass

        # Create mock preset manager with actual presets
        from custom_components.ha_light_controller.preset_manager import PresetConfig

        preset_manager = MagicMock()
        preset_manager.presets = {
            "preset_1": PresetConfig(
                id="preset_1",
                name="Test Preset",
                entities=["light.test"],
            ),
            "preset_2": PresetConfig(
                id="preset_2",
                name="Another Preset",
                entities=["light.other"],
            ),
        }
        preset_manager.delete_preset = AsyncMock()

        runtime_data = MagicMock()
        runtime_data.preset_manager = preset_manager
        config_entry_with_presets.runtime_data = runtime_data

        return flow, preset_manager

    @pytest.fixture
    def options_flow_no_presets(self, config_entry, hass):
        """Create options flow with empty preset manager."""
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        flow.hass = hass

        preset_manager = MagicMock()
        preset_manager.presets = {}

        runtime_data = MagicMock()
        runtime_data.preset_manager = preset_manager
        config_entry.runtime_data = runtime_data

        return flow

    @pytest.mark.asyncio
    async def test_step_manage_presets_shows_menu(self, options_flow_with_presets):
        """Test manage_presets shows menu with edit/delete options."""
        flow, _ = options_flow_with_presets

        result = await flow.async_step_manage_presets()

        assert result["type"] == FlowResultType.MENU
        assert result["step_id"] == "manage_presets"
        assert "edit_preset" in result["menu_options"]
        assert "delete_preset" in result["menu_options"]
        assert "preset_count" in result["description_placeholders"]
        assert result["description_placeholders"]["preset_count"] == "2"

    @pytest.mark.asyncio
    async def test_step_manage_presets_no_presets(self, options_flow_no_presets):
        """Test manage_presets handles no presets."""
        flow = options_flow_no_presets

        result = await flow.async_step_manage_presets()

        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "no_presets"

    @pytest.mark.asyncio
    async def test_step_delete_preset_shows_selection(self, options_flow_with_presets):
        """Test delete_preset shows preset selection form."""
        flow, preset_manager = options_flow_with_presets

        result = await flow.async_step_delete_preset()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "delete_preset"

    @pytest.mark.asyncio
    async def test_step_delete_preset_goes_to_confirmation(
        self, options_flow_with_presets
    ):
        """Test delete_preset selection goes to confirm step."""
        flow, preset_manager = options_flow_with_presets

        result = await flow.async_step_delete_preset(
            user_input={"preset_to_delete": "preset_1"}
        )

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "confirm_delete"

    @pytest.mark.asyncio
    async def test_step_confirm_delete_deletes_preset(self, options_flow_with_presets):
        """Test confirm_delete actually deletes preset."""
        flow, preset_manager = options_flow_with_presets

        # First select preset to delete
        await flow.async_step_delete_preset(user_input={"preset_to_delete": "preset_1"})

        # Then confirm deletion
        result = await flow.async_step_confirm_delete(
            user_input={"confirm_delete": True}
        )

        assert result["type"] == FlowResultType.CREATE_ENTRY
        preset_manager.delete_preset.assert_called_once_with("preset_1")

    @pytest.mark.asyncio
    async def test_step_confirm_delete_cancelled(self, options_flow_with_presets):
        """Test confirm_delete cancellation returns to menu."""
        flow, preset_manager = options_flow_with_presets

        # First select preset to delete
        await flow.async_step_delete_preset(user_input={"preset_to_delete": "preset_1"})

        # Cancel the deletion
        result = await flow.async_step_confirm_delete(
            user_input={"confirm_delete": False}
        )

        # Should return to menu
        assert result["type"] == FlowResultType.MENU
        preset_manager.delete_preset.assert_not_called()


class TestOptionsFlowEditPreset:
    """Tests for edit_preset flow."""

    @pytest.fixture
    def options_flow_with_presets(self, config_entry, hass):
        """Create options flow with preset manager containing presets."""
        from custom_components.ha_light_controller.preset_manager import PresetConfig

        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        flow.hass = hass

        preset_1 = PresetConfig(
            id="preset_1",
            name="Preset One",
            entities=["light.test_1"],
            brightness_pct=75,
            targets=[{"entity_id": "light.test_1", "brightness_pct": 80}],
        )

        preset_manager = MagicMock()
        preset_manager.presets = {"preset_1": preset_1}
        preset_manager.delete_preset = AsyncMock()
        preset_manager.create_preset = AsyncMock()

        runtime_data = MagicMock()
        runtime_data.preset_manager = preset_manager
        config_entry.runtime_data = runtime_data

        return flow, preset_manager

    @pytest.mark.asyncio
    async def test_step_edit_preset_shows_form(self, options_flow_with_presets):
        """Test edit_preset shows selection form."""
        flow, _ = options_flow_with_presets

        result = await flow.async_step_edit_preset()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "edit_preset"

    @pytest.mark.asyncio
    async def test_step_edit_preset_selects_preset(self, options_flow_with_presets):
        """Test selecting a preset to edit loads its data."""
        flow, _ = options_flow_with_presets

        result = await flow.async_step_edit_preset(
            user_input={"preset_to_edit": "preset_1"}
        )

        # Should go to entity menu (shown as form with action selector)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "preset_entity_menu"

        # Check that preset data was loaded
        assert flow._editing_preset_id == "preset_1"
        assert flow._preset_data["name"] == "Preset One"

    @pytest.mark.asyncio
    async def test_step_edit_preset_invalid_selection(self, options_flow_with_presets):
        """Test invalid preset selection returns to menu."""
        flow, _ = options_flow_with_presets

        result = await flow.async_step_edit_preset(
            user_input={"preset_to_edit": "nonexistent"}
        )

        # Should return to manage presets menu
        assert result["type"] == FlowResultType.MENU
        assert result["step_id"] == "manage_presets"

    @pytest.mark.asyncio
    async def test_step_edit_preset_no_presets(self, config_entry, hass):
        """Test edit_preset with no presets returns to manage_presets."""
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        flow.hass = hass

        preset_manager = MagicMock()
        preset_manager.presets = {}

        runtime_data = MagicMock()
        runtime_data.preset_manager = preset_manager
        config_entry.runtime_data = runtime_data

        result = await flow.async_step_edit_preset()

        # Should return to manage presets (which shows "no_presets" error form when empty)
        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "no_presets"


class TestOptionsFlowConfirmDeleteEdgeCases:
    """Tests for confirm_delete edge cases."""

    @pytest.mark.asyncio
    async def test_step_confirm_delete_no_preset_id(self, config_entry, hass):
        """Test confirm_delete returns to menu when no preset_id set."""

        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        flow.hass = hass
        # Don't set _deleting_preset_id

        preset_manager = MagicMock()
        preset_manager.presets = {"preset_1": MagicMock()}

        runtime_data = MagicMock()
        runtime_data.preset_manager = preset_manager
        config_entry.runtime_data = runtime_data

        result = await flow.async_step_confirm_delete()

        assert result["type"] == FlowResultType.MENU
        assert result["step_id"] == "manage_presets"

    @pytest.mark.asyncio
    async def test_step_confirm_delete_preset_not_found(self, config_entry, hass):
        """Test confirm_delete returns to manage_presets when preset no longer exists."""
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        flow.hass = hass
        flow._deleting_preset_id = "nonexistent"

        preset_manager = MagicMock()
        preset_manager.presets = {}  # Preset doesn't exist

        runtime_data = MagicMock()
        runtime_data.preset_manager = preset_manager
        config_entry.runtime_data = runtime_data

        result = await flow.async_step_confirm_delete()

        # With no presets, manage_presets shows "no_presets" error form
        assert result["type"] == FlowResultType.FORM
        assert result["errors"]["base"] == "no_presets"


class TestOptionsFlowRemoveEntity:
    """Tests for remove_entity flow."""

    @pytest.fixture
    def flow_with_preset_data(self, config_entry, hass):
        """Create flow with preset data."""
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        flow.hass = hass
        flow._preset_data = {
            "name": "Test Preset",
            "entities": ["light.test_1", "light.test_2"],
            "targets": {
                "light.test_1": {"entity_id": "light.test_1", "brightness_pct": 50},
                "light.test_2": {"entity_id": "light.test_2", "brightness_pct": 75},
            },
        }
        return flow

    @pytest.mark.asyncio
    async def test_step_remove_entity_shows_form(self, flow_with_preset_data, hass):
        """Test remove_entity shows selection form."""
        flow = flow_with_preset_data
        # Mock entity state for friendly name lookup
        hass.states.get = MagicMock(return_value=None)

        result = await flow.async_step_remove_entity()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "remove_entity"

    @pytest.mark.asyncio
    async def test_step_remove_entity_removes_entity(self, flow_with_preset_data):
        """Test removing an entity updates preset data."""
        flow = flow_with_preset_data

        result = await flow.async_step_remove_entity(
            user_input={"entity_to_remove": "light.test_1"}
        )

        # Should go back to entity menu (shown as form)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "preset_entity_menu"

        # Entity should be removed from list and targets
        assert "light.test_1" not in flow._preset_data["entities"]
        assert "light.test_1" not in flow._preset_data["targets"]
        assert "light.test_2" in flow._preset_data["entities"]


class TestOptionsFlowAddMoreEntities:
    """Tests for add_more_entities flow."""

    @pytest.fixture
    def flow_with_preset_data(self, config_entry, hass):
        """Create flow with preset data."""
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        flow.hass = hass
        flow._preset_data = {
            "name": "Test Preset",
            "entities": ["light.test_1"],
            "targets": {},
        }
        return flow

    @pytest.mark.asyncio
    async def test_step_add_more_entities_shows_form(self, flow_with_preset_data):
        """Test add_more_entities shows form."""
        flow = flow_with_preset_data

        result = await flow.async_step_add_more_entities()

        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "add_more_entities"
        assert result["description_placeholders"]["current_count"] == "1"

    @pytest.mark.asyncio
    async def test_step_add_more_entities_adds_entities(self, flow_with_preset_data):
        """Test adding entities updates preset data."""
        flow = flow_with_preset_data

        result = await flow.async_step_add_more_entities(
            user_input={"new_entities": ["light.test_2", "light.test_3"]}
        )

        # Should go to entity menu (shown as form)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "preset_entity_menu"

        # New entities should be added
        assert "light.test_2" in flow._preset_data["entities"]
        assert "light.test_3" in flow._preset_data["entities"]

    @pytest.mark.asyncio
    async def test_step_add_more_entities_empty_returns_to_menu(
        self, flow_with_preset_data
    ):
        """Test submitting empty selection returns to entity menu."""
        flow = flow_with_preset_data

        result = await flow.async_step_add_more_entities(user_input={})

        # Returns to entity menu (shown as form)
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "preset_entity_menu"


class TestPresetCreationStateDerivation:
    """Tests for preset state/transition derivation from per-entity configs."""

    @pytest.mark.asyncio
    async def test_preset_state_derived_from_targets_all_off(
        self, hass, config_entry_with_presets
    ):
        """Test preset state is 'off' when all targets are off."""
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry_with_presets
        flow.hass = hass

        # Set up preset data with all targets "off"
        flow._preset_data = {
            "name": "All Off Preset",
            "entities": ["light.test1", "light.test2"],
            "skip_verification": False,
            "targets": {
                "light.test1": {"entity_id": "light.test1", "state": "off"},
                "light.test2": {"entity_id": "light.test2", "state": "off"},
            },
        }

        # Mock preset_manager
        mock_preset_manager = MagicMock()
        mock_preset_manager.presets = {}
        mock_preset_manager.create_preset = AsyncMock()

        config_entry_with_presets.runtime_data = MagicMock()
        config_entry_with_presets.runtime_data.preset_manager = mock_preset_manager

        await flow._create_preset_from_data()

        # Verify create_preset was called with state="off"
        call_args = mock_preset_manager.create_preset.call_args
        assert call_args.kwargs.get("state") == "off"

    @pytest.mark.asyncio
    async def test_preset_state_derived_mixed_uses_on(
        self, hass, config_entry_with_presets
    ):
        """Test preset state is 'on' when targets are mixed."""
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry_with_presets
        flow.hass = hass

        # Set up preset data with mixed targets
        flow._preset_data = {
            "name": "Mixed Preset",
            "entities": ["light.test1", "light.test2"],
            "skip_verification": False,
            "targets": {
                "light.test1": {"entity_id": "light.test1", "state": "on"},
                "light.test2": {"entity_id": "light.test2", "state": "off"},
            },
        }

        mock_preset_manager = MagicMock()
        mock_preset_manager.presets = {}
        mock_preset_manager.create_preset = AsyncMock()

        config_entry_with_presets.runtime_data = MagicMock()
        config_entry_with_presets.runtime_data.preset_manager = mock_preset_manager

        await flow._create_preset_from_data()

        # Mixed state defaults to "on"
        call_args = mock_preset_manager.create_preset.call_args
        assert call_args.kwargs.get("state") == "on"

    @pytest.mark.asyncio
    async def test_preset_transition_derived_from_max(
        self, hass, config_entry_with_presets
    ):
        """Test preset transition is max of all per-entity transitions."""
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry_with_presets
        flow.hass = hass

        # Set up preset data with varying transitions
        flow._preset_data = {
            "name": "Transition Preset",
            "entities": ["light.test1", "light.test2", "light.test3"],
            "skip_verification": False,
            "targets": {
                "light.test1": {"entity_id": "light.test1", "transition": 1.0},
                "light.test2": {"entity_id": "light.test2", "transition": 5.0},
                "light.test3": {"entity_id": "light.test3"},  # No transition
            },
        }

        mock_preset_manager = MagicMock()
        mock_preset_manager.presets = {}
        mock_preset_manager.create_preset = AsyncMock()

        config_entry_with_presets.runtime_data = MagicMock()
        config_entry_with_presets.runtime_data.preset_manager = mock_preset_manager

        await flow._create_preset_from_data()

        # Transition should be max (5.0)
        call_args = mock_preset_manager.create_preset.call_args
        assert call_args.kwargs.get("transition") == 5.0

    @pytest.mark.asyncio
    async def test_preset_state_all_on_uses_on(self, hass, config_entry_with_presets):
        """Test preset state is 'on' when all targets are on."""
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry_with_presets
        flow.hass = hass

        flow._preset_data = {
            "name": "All On Preset",
            "entities": ["light.test1", "light.test2"],
            "skip_verification": False,
            "targets": {
                "light.test1": {"entity_id": "light.test1", "state": "on"},
                "light.test2": {"entity_id": "light.test2", "state": "on"},
            },
        }

        mock_preset_manager = MagicMock()
        mock_preset_manager.presets = {}
        mock_preset_manager.create_preset = AsyncMock()

        config_entry_with_presets.runtime_data = MagicMock()
        config_entry_with_presets.runtime_data.preset_manager = mock_preset_manager

        await flow._create_preset_from_data()

        call_args = mock_preset_manager.create_preset.call_args
        assert call_args.kwargs.get("state") == "on"

    @pytest.mark.asyncio
    async def test_preset_transition_defaults_to_zero(
        self, hass, config_entry_with_presets
    ):
        """Test preset transition defaults to 0.0 when no targets have transition."""
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry_with_presets
        flow.hass = hass

        flow._preset_data = {
            "name": "No Transition Preset",
            "entities": ["light.test1"],
            "skip_verification": False,
            "targets": {
                "light.test1": {"entity_id": "light.test1", "state": "on"},
            },
        }

        mock_preset_manager = MagicMock()
        mock_preset_manager.presets = {}
        mock_preset_manager.create_preset = AsyncMock()

        config_entry_with_presets.runtime_data = MagicMock()
        config_entry_with_presets.runtime_data.preset_manager = mock_preset_manager

        await flow._create_preset_from_data()

        call_args = mock_preset_manager.create_preset.call_args
        assert call_args.kwargs.get("transition") == 0.0


class TestCoverageGaps:
    """Tests for coverage gaps identified in config_flow.py."""

    @pytest.fixture
    def _create_options_flow(self, config_entry, hass):
        """Create an options flow instance."""
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        flow.hass = hass
        # Initialize state
        flow._preset_data = {}
        flow._configuring_entity = None
        flow._editing_preset_id = None
        flow._deleting_preset_id = None

        # Mock entity state for friendly name lookup
        mock_state = MagicMock()
        mock_state.attributes = {"friendly_name": "Test Light"}
        hass.states.get = MagicMock(return_value=mock_state)

        return flow

    # =============================================================================
    # Settings Tests
    # =============================================================================

    @pytest.mark.asyncio
    async def test_settings_with_non_section_input(self, config_entry):
        """Test settings step with non-dict (non-section) values in user_input."""
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        result = await flow.async_step_settings({"some_key": "some_value"})
        assert result["type"] == FlowResultType.CREATE_ENTRY

    # =============================================================================
    # Preset Entity Menu Actions
    # =============================================================================

    @pytest.mark.asyncio
    async def test_preset_entity_menu_configure(self, _create_options_flow):
        """Test preset entity menu configure action."""
        flow = _create_options_flow
        flow._preset_data = {
            PRESET_ENTITIES: ["light.test"],
            "targets": {},
        }
        result = await flow.async_step_preset_entity_menu({"action": "configure"})
        # Should redirect to select_entity_to_configure step
        assert result["step_id"] == "select_entity_to_configure"

    @pytest.mark.asyncio
    async def test_preset_entity_menu_add(self, _create_options_flow):
        """Test preset entity menu add action."""
        flow = _create_options_flow
        flow._preset_data = {
            PRESET_ENTITIES: ["light.test"],
            "targets": {},
        }
        result = await flow.async_step_preset_entity_menu({"action": "add"})
        assert result["step_id"] == "add_more_entities"

    @pytest.mark.asyncio
    async def test_preset_entity_menu_remove(self, _create_options_flow, hass):
        """Test preset entity menu remove action."""
        flow = _create_options_flow
        flow.hass = hass
        flow._preset_data = {
            PRESET_ENTITIES: ["light.a", "light.b"],
            "targets": {},
        }
        result = await flow.async_step_preset_entity_menu({"action": "remove"})
        assert result["step_id"] == "remove_entity"

    @pytest.mark.asyncio
    async def test_preset_entity_menu_save(self, config_entry, hass):
        """Test preset entity menu save action with configured targets."""
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        flow.hass = hass
        flow._preset_data = {
            PRESET_NAME: "Test",
            PRESET_ENTITIES: ["light.test"],
            "targets": {
                "light.test": {
                    "entity_id": "light.test",
                    "state": "on",
                    "brightness_pct": 80,
                }
            },
            PRESET_SKIP_VERIFICATION: False,
        }

        # Mock preset manager
        mock_pm = MagicMock()
        mock_pm.create_preset = AsyncMock()
        runtime_data = MagicMock()
        runtime_data.preset_manager = mock_pm
        config_entry.runtime_data = runtime_data

        result = await flow.async_step_preset_entity_menu({"action": "save"})
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_preset_entity_menu_save_no_targets(self, _create_options_flow):
        """Test preset entity menu save with no configured targets shows error."""
        flow = _create_options_flow
        flow._preset_data = {
            PRESET_NAME: "Test",
            PRESET_ENTITIES: ["light.test"],
            "targets": {},
        }
        result = await flow.async_step_preset_entity_menu({"action": "save"})
        assert result["type"] == FlowResultType.FORM
        assert result.get("errors", {}).get("base") == "configure_at_least_one"

    # =============================================================================
    # Select Entity to Configure
    # =============================================================================

    @pytest.mark.asyncio
    async def test_select_entity_to_configure_with_entity(self, _create_options_flow):
        """Test selecting an entity to configure."""
        flow = _create_options_flow
        flow._preset_data = {
            PRESET_ENTITIES: ["light.test"],
            "targets": {},
        }
        result = await flow.async_step_select_entity_to_configure(
            {"entity_to_configure": "light.test"}
        )
        assert flow._configuring_entity == "light.test"
        assert result["step_id"] == "configure_entity"

    # =============================================================================
    # Configure Entity Edge Cases
    # =============================================================================

    @pytest.mark.asyncio
    async def test_configure_entity_no_configuring_entity(self, _create_options_flow):
        """Test configure_entity without _configuring_entity set."""
        flow = _create_options_flow
        flow._configuring_entity = None
        flow._preset_data = {
            PRESET_ENTITIES: ["light.test"],
            "targets": {},
        }
        result = await flow.async_step_configure_entity()
        # Should redirect to menu
        assert result["step_id"] == "preset_entity_menu"

    @pytest.mark.asyncio
    async def test_configure_entity_with_color_temp_default(
        self, _create_options_flow, hass
    ):
        """Test configure_entity with color_temp_kelvin in existing config."""
        flow = _create_options_flow
        flow.hass = hass
        flow._configuring_entity = "light.test"
        flow._preset_data = {
            PRESET_ENTITIES: ["light.test"],
            "targets": {
                "light.test": {"entity_id": "light.test", "color_temp_kelvin": 4000}
            },
        }

        # Mock entity state for friendly name
        mock_state = MagicMock()
        mock_state.attributes = {"friendly_name": "Test Light"}
        hass.states.get = MagicMock(return_value=mock_state)

        result = await flow.async_step_configure_entity()
        assert result["step_id"] == "configure_entity"
        assert result["type"] == FlowResultType.FORM

    @pytest.mark.asyncio
    async def test_configure_entity_with_rgb_default(self, _create_options_flow, hass):
        """Test configure_entity with rgb_color in existing config."""
        flow = _create_options_flow
        flow.hass = hass
        flow._configuring_entity = "light.test"
        flow._preset_data = {
            PRESET_ENTITIES: ["light.test"],
            "targets": {
                "light.test": {"entity_id": "light.test", "rgb_color": [255, 0, 0]}
            },
        }

        # Mock entity state
        mock_state = MagicMock()
        mock_state.attributes = {"friendly_name": "Test Light"}
        hass.states.get = MagicMock(return_value=mock_state)

        result = await flow.async_step_configure_entity()
        assert result["step_id"] == "configure_entity"
        assert result["type"] == FlowResultType.FORM

    @pytest.mark.asyncio
    async def test_configure_entity_state_on_with_brightness_and_color_temp(
        self, _create_options_flow
    ):
        """Test configuring entity with state=on, brightness, and color_temp."""
        flow = _create_options_flow
        flow._configuring_entity = "light.test"
        flow._preset_data = {
            PRESET_ENTITIES: ["light.test"],
            "targets": {},
        }
        await flow.async_step_configure_entity(
            {
                PRESET_STATE: "on",
                PRESET_TRANSITION: 0,
                PRESET_BRIGHTNESS_PCT: 80,
                PRESET_COLOR_MODE: COLOR_MODE_COLOR_TEMP,
                PRESET_COLOR_TEMP_KELVIN: 4000,
            }
        )
        assert "light.test" in flow._preset_data["targets"]
        target = flow._preset_data["targets"]["light.test"]
        assert target["brightness_pct"] == 80
        assert target["color_temp_kelvin"] == 4000

    @pytest.mark.asyncio
    async def test_configure_entity_state_on_with_rgb(self, _create_options_flow):
        """Test configuring entity with state=on and RGB color."""
        flow = _create_options_flow
        flow._configuring_entity = "light.test"
        flow._preset_data = {
            PRESET_ENTITIES: ["light.test"],
            "targets": {},
        }
        await flow.async_step_configure_entity(
            {
                PRESET_STATE: "on",
                PRESET_TRANSITION: 0,
                PRESET_BRIGHTNESS_PCT: 80,
                PRESET_COLOR_MODE: COLOR_MODE_RGB,
                PRESET_RGB_COLOR: [255, 0, 0],
            }
        )
        target = flow._preset_data["targets"]["light.test"]
        assert target["rgb_color"] == [255, 0, 0]

    @pytest.mark.asyncio
    async def test_configure_entity_state_off(self, _create_options_flow):
        """Test configuring entity with state=off - no brightness/color should be set."""
        flow = _create_options_flow
        flow._configuring_entity = "light.test"
        flow._preset_data = {
            PRESET_ENTITIES: ["light.test"],
            "targets": {},
        }
        await flow.async_step_configure_entity(
            {
                PRESET_STATE: "off",
                PRESET_TRANSITION: 2.0,
            }
        )
        target = flow._preset_data["targets"]["light.test"]
        assert target["state"] == "off"
        assert "brightness_pct" not in target
        assert target["transition"] == 2.0

    @pytest.mark.asyncio
    async def test_configure_entity_no_brightness(self, _create_options_flow):
        """Test state=on but brightness_pct is None."""
        flow = _create_options_flow
        flow._configuring_entity = "light.test"
        flow._preset_data = {
            PRESET_ENTITIES: ["light.test"],
            "targets": {},
        }
        await flow.async_step_configure_entity(
            {
                PRESET_STATE: "on",
                PRESET_TRANSITION: 0,
                PRESET_COLOR_MODE: COLOR_MODE_NONE,
            }
        )
        target = flow._preset_data["targets"]["light.test"]
        assert "brightness_pct" not in target

    @pytest.mark.asyncio
    async def test_configure_entity_color_mode_none(self, _create_options_flow):
        """Test color mode = none, no color settings."""
        flow = _create_options_flow
        flow._configuring_entity = "light.test"
        flow._preset_data = {
            PRESET_ENTITIES: ["light.test"],
            "targets": {},
        }
        await flow.async_step_configure_entity(
            {
                PRESET_STATE: "on",
                PRESET_TRANSITION: 0,
                PRESET_BRIGHTNESS_PCT: 100,
                PRESET_COLOR_MODE: COLOR_MODE_NONE,
            }
        )
        target = flow._preset_data["targets"]["light.test"]
        assert "color_temp_kelvin" not in target
        assert "rgb_color" not in target

    # =============================================================================
    # Remove Entity
    # =============================================================================

    @pytest.mark.asyncio
    async def test_remove_entity_invalid(self, _create_options_flow):
        """Test removing an invalid entity."""
        flow = _create_options_flow
        flow._preset_data = {
            PRESET_ENTITIES: ["light.a", "light.b"],
            "targets": {},
        }
        await flow.async_step_remove_entity({"entity_to_remove": "light.nonexistent"})
        # Should go back to menu without removing anything
        assert "light.a" in flow._preset_data[PRESET_ENTITIES]
        assert "light.b" in flow._preset_data[PRESET_ENTITIES]

    @pytest.mark.asyncio
    async def test_remove_entity_none(self, _create_options_flow):
        """Test removing None entity."""
        flow = _create_options_flow
        flow._preset_data = {
            PRESET_ENTITIES: ["light.a", "light.b"],
            "targets": {},
        }
        await flow.async_step_remove_entity({"entity_to_remove": None})
        assert len(flow._preset_data[PRESET_ENTITIES]) == 2

    # =============================================================================
    # Create Preset From Data
    # =============================================================================

    @pytest.mark.asyncio
    async def test_create_preset_from_data_no_runtime_data(self, config_entry):
        """Test creating preset when runtime_data is None."""
        config_entry.runtime_data = None
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        flow._preset_data = {
            PRESET_NAME: "Test",
            PRESET_ENTITIES: ["light.test"],
            "targets": {"light.test": {"entity_id": "light.test", "state": "on"}},
        }
        result = await flow._create_preset_from_data()
        assert result["type"] == FlowResultType.CREATE_ENTRY

    @pytest.mark.asyncio
    async def test_create_preset_from_data_editing_existing(self, config_entry):
        """Test editing an existing preset uses update_preset (preserves preset_id)."""
        mock_pm = MagicMock()
        mock_pm.presets = {"old_id": MagicMock()}
        mock_pm.update_preset = AsyncMock()

        runtime_data = MagicMock()
        runtime_data.preset_manager = mock_pm
        config_entry.runtime_data = runtime_data

        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        flow._editing_preset_id = "old_id"
        flow._preset_data = {
            PRESET_NAME: "Updated",
            PRESET_ENTITIES: ["light.test"],
            "targets": {
                "light.test": {
                    "entity_id": "light.test",
                    "state": "on",
                    "brightness_pct": 80,
                }
            },
            PRESET_SKIP_VERIFICATION: False,
        }
        await flow._create_preset_from_data()
        mock_pm.update_preset.assert_called_once()
        call_args = mock_pm.update_preset.call_args
        assert call_args[0][0] == "old_id"  # preset_id preserved

    # =============================================================================
    # Manage/Edit/Delete with no preset_manager
    # =============================================================================

    @pytest.mark.asyncio
    async def test_manage_presets_no_runtime_data(self, config_entry):
        """Test manage_presets when runtime_data is None."""
        config_entry.runtime_data = None
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        result = await flow.async_step_manage_presets()
        assert result.get("errors", {}).get("base") == "no_presets"

    @pytest.mark.asyncio
    async def test_edit_preset_no_runtime_data(self, config_entry):
        """Test edit_preset when runtime_data is None."""
        config_entry.runtime_data = None
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        result = await flow.async_step_edit_preset()
        assert result.get("errors", {}).get("base") == "no_presets"

    @pytest.mark.asyncio
    async def test_edit_preset_with_target_without_entity_id(self, config_entry, hass):
        """Test editing preset where targets have missing entity_id."""
        mock_pm = MagicMock()
        preset = MagicMock()
        preset.name = "Test"
        preset.entities = ["light.test"]
        preset.skip_verification = False
        preset.targets = [{"brightness_pct": 80}]  # No entity_id!
        mock_pm.presets = {"p1": preset}

        runtime_data = MagicMock()
        runtime_data.preset_manager = mock_pm
        config_entry.runtime_data = runtime_data

        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        flow.hass = hass

        # Mock entity state for friendly name lookup
        mock_state = MagicMock()
        mock_state.attributes = {"friendly_name": "Test Light"}
        hass.states.get = MagicMock(return_value=mock_state)

        await flow.async_step_edit_preset({"preset_to_edit": "p1"})
        # Should still work but targets dict should be empty (no entity_id to key on)
        assert flow._preset_data["targets"] == {}

    @pytest.mark.asyncio
    async def test_delete_preset_no_runtime_data(self, config_entry):
        """Test delete_preset when runtime_data is None."""
        config_entry.runtime_data = None
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        result = await flow.async_step_delete_preset()
        # Should redirect to manage_presets which shows no_presets error
        assert result.get("errors", {}).get("base") == "no_presets"

    @pytest.mark.asyncio
    async def test_delete_preset_invalid_selection(self, config_entry):
        """Test delete_preset with invalid preset selection."""
        mock_pm = MagicMock()
        mock_pm.presets = {"p1": MagicMock()}
        runtime_data = MagicMock()
        runtime_data.preset_manager = mock_pm
        config_entry.runtime_data = runtime_data

        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        result = await flow.async_step_delete_preset(
            {"preset_to_delete": "nonexistent"}
        )
        # Should go back to manage_presets menu
        # Since preset_manager exists and has presets, it shows the menu
        assert result["type"] == FlowResultType.MENU

    @pytest.mark.asyncio
    async def test_confirm_delete_no_preset_manager(self, config_entry):
        """Test confirm_delete when preset_manager is None."""
        config_entry.runtime_data = None
        flow = LightControllerOptionsFlow()
        flow._config_entry = config_entry
        flow._deleting_preset_id = "p1"
        result = await flow.async_step_confirm_delete()
        assert result.get("errors", {}).get("base") == "no_presets"
