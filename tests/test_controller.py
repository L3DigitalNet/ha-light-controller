"""Tests for the Light Controller controller module."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE

from custom_components.ha_light_controller.const import (
    RESULT_CODE_ERROR,
    RESULT_CODE_FAILED,
    RESULT_CODE_NO_VALID_ENTITIES,
    RESULT_CODE_SUCCESS,
    RESULT_CODE_TIMEOUT,
)
from custom_components.ha_light_controller.controller import (
    ColorTolerance,
    LightController,
    LightGroup,
    LightTarget,
    OperationResult,
    RetryConfig,
    TargetState,
    VerificationResult,
)

# =============================================================================
# TargetState Enum Tests
# =============================================================================


class TestTargetState:
    """Tests for TargetState enum."""

    def test_from_string_on(self):
        """Test parsing 'on' string."""
        assert TargetState.from_string("on") == TargetState.ON
        assert TargetState.from_string("ON") == TargetState.ON
        assert TargetState.from_string("  on  ") == TargetState.ON

    def test_from_string_off(self):
        """Test parsing 'off' string."""
        assert TargetState.from_string("off") == TargetState.OFF
        assert TargetState.from_string("OFF") == TargetState.OFF
        assert TargetState.from_string("  off  ") == TargetState.OFF

    def test_from_string_invalid(self):
        """Test parsing invalid string raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            TargetState.from_string("invalid")
        assert "Invalid state" in str(exc_info.value)

    def test_from_string_empty(self):
        """Test parsing empty string raises ValueError."""
        with pytest.raises(ValueError):
            TargetState.from_string("")


# =============================================================================
# RetryConfig Tests
# =============================================================================


class TestRetryConfig:
    """Tests for RetryConfig dataclass."""

    def test_default_values(self):
        """Test default values."""
        config = RetryConfig()
        assert config.max_retries == 3
        assert config.delay_after_send == 2.0
        assert config.max_runtime_seconds == 60.0
        assert config.use_exponential_backoff is False
        assert config.max_backoff_seconds == 30.0

    def test_custom_values(self):
        """Test custom values."""
        config = RetryConfig(
            max_retries=5,
            delay_after_send=1.5,
            max_runtime_seconds=120.0,
            use_exponential_backoff=True,
            max_backoff_seconds=60.0,
        )
        assert config.max_retries == 5
        assert config.delay_after_send == 1.5
        assert config.max_runtime_seconds == 120.0
        assert config.use_exponential_backoff is True
        assert config.max_backoff_seconds == 60.0

    def test_calculate_delay_no_backoff(self):
        """Test delay calculation without exponential backoff."""
        config = RetryConfig(delay_after_send=2.0, use_exponential_backoff=False)
        assert config.calculate_delay(0) == 2.0
        assert config.calculate_delay(1) == 2.0
        assert config.calculate_delay(2) == 2.0
        assert config.calculate_delay(5) == 2.0

    def test_calculate_delay_with_backoff(self):
        """Test delay calculation with exponential backoff."""
        config = RetryConfig(
            delay_after_send=2.0,
            use_exponential_backoff=True,
            max_backoff_seconds=30.0,
        )
        # Attempt 0: no backoff applied
        assert config.calculate_delay(0) == 2.0
        # Attempt 1: 2.0 * 2^1 = 4.0
        assert config.calculate_delay(1) == 4.0
        # Attempt 2: 2.0 * 2^2 = 8.0
        assert config.calculate_delay(2) == 8.0
        # Attempt 3: 2.0 * 2^3 = 16.0
        assert config.calculate_delay(3) == 16.0

    def test_calculate_delay_backoff_capped(self):
        """Test delay is capped at max_backoff_seconds."""
        config = RetryConfig(
            delay_after_send=2.0,
            use_exponential_backoff=True,
            max_backoff_seconds=10.0,
        )
        # Attempt 3: would be 16.0, but capped at 10.0
        assert config.calculate_delay(3) == 10.0
        # Attempt 5: would be 64.0, but capped at 10.0
        assert config.calculate_delay(5) == 10.0


# =============================================================================
# LightTarget Tests
# =============================================================================


class TestLightTarget:
    """Tests for LightTarget dataclass."""

    def test_default_values(self):
        """Test default values."""
        target = LightTarget(entity_id="light.test")
        assert target.entity_id == "light.test"
        assert target.brightness_pct == 100
        assert target.rgb_color is None
        assert target.color_temp_kelvin is None
        assert target.effect is None

    def test_to_service_data_brightness_only(self):
        """Test service data with brightness only."""
        target = LightTarget(entity_id="light.test", brightness_pct=75)
        data = target.to_service_data()
        assert data == {"brightness_pct": 75}

    def test_to_service_data_with_rgb(self):
        """Test service data with RGB color."""
        target = LightTarget(
            entity_id="light.test",
            brightness_pct=80,
            rgb_color=[255, 128, 64],
        )
        data = target.to_service_data()
        assert data == {"brightness_pct": 80, "rgb_color": [255, 128, 64]}

    def test_to_service_data_with_kelvin(self):
        """Test service data with color temperature."""
        target = LightTarget(
            entity_id="light.test",
            brightness_pct=90,
            color_temp_kelvin=4000,
        )
        data = target.to_service_data()
        assert data == {"brightness_pct": 90, "color_temp_kelvin": 4000}

    def test_to_service_data_rgb_overrides_kelvin(self):
        """Test that RGB takes precedence over kelvin when both provided."""
        target = LightTarget(
            entity_id="light.test",
            brightness_pct=50,
            rgb_color=[255, 0, 0],
            color_temp_kelvin=4000,
        )
        data = target.to_service_data()
        assert "rgb_color" in data
        assert "color_temp_kelvin" not in data

    def test_to_service_data_with_effect(self):
        """Test service data with effect."""
        target = LightTarget(
            entity_id="light.test",
            brightness_pct=100,
            effect="rainbow",
        )
        data = target.to_service_data()
        assert data == {"brightness_pct": 100, "effect": "rainbow"}

    def test_to_service_data_with_transition(self):
        """Test service data with transition."""
        target = LightTarget(entity_id="light.test", brightness_pct=50)
        data = target.to_service_data(include_transition=2.5)
        assert data == {"brightness_pct": 50, "transition": 2.5}

    def test_to_service_data_zero_transition_excluded(self):
        """Test that zero transition is not included."""
        target = LightTarget(entity_id="light.test", brightness_pct=50)
        data = target.to_service_data(include_transition=0)
        assert "transition" not in data


class TestLightTargetStateAndTransition:
    """Tests for LightTarget state and transition fields."""

    def test_light_target_default_state_on(self):
        """Test LightTarget defaults to state='on'."""
        target = LightTarget(entity_id="light.test")
        assert target.state == "on"

    def test_light_target_custom_state_off(self):
        """Test LightTarget with state='off'."""
        target = LightTarget(entity_id="light.test", state="off")
        assert target.state == "off"

    def test_light_target_default_transition_none(self):
        """Test LightTarget defaults to transition=None."""
        target = LightTarget(entity_id="light.test")
        assert target.transition is None

    def test_light_target_custom_transition(self):
        """Test LightTarget with custom transition."""
        target = LightTarget(entity_id="light.test", transition=2.5)
        assert target.transition == 2.5


# =============================================================================
# LightGroup Tests
# =============================================================================


class TestLightGroup:
    """Tests for LightGroup dataclass."""

    def test_creation(self):
        """Test creating a light group."""
        group = LightGroup(
            entities=["light.a", "light.b"],
            brightness_pct=75,
        )
        assert group.entities == ["light.a", "light.b"]
        assert group.brightness_pct == 75

    def test_to_service_data(self):
        """Test service data conversion."""
        group = LightGroup(
            entities=["light.a", "light.b"],
            brightness_pct=80,
            rgb_color=[255, 0, 0],
        )
        data = group.to_service_data()
        assert data == {"brightness_pct": 80, "rgb_color": [255, 0, 0]}

    def test_to_service_data_with_transition(self):
        """Test service data with transition."""
        group = LightGroup(
            entities=["light.a"],
            brightness_pct=50,
            color_temp_kelvin=3500,
        )
        data = group.to_service_data(include_transition=1.5)
        assert data == {
            "brightness_pct": 50,
            "color_temp_kelvin": 3500,
            "transition": 1.5,
        }


# =============================================================================
# OperationResult Tests
# =============================================================================


class TestOperationResult:
    """Tests for OperationResult dataclass."""

    def test_success_result(self):
        """Test successful operation result."""
        result = OperationResult(
            success=True,
            result_code=RESULT_CODE_SUCCESS,
            message="All lights set",
            attempts=2,
            total_lights=5,
            elapsed_seconds=3.456,
        )
        assert result.success is True
        assert result.result_code == RESULT_CODE_SUCCESS

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = OperationResult(
            success=False,
            result_code=RESULT_CODE_FAILED,
            message="Failed to set lights",
            attempts=3,
            total_lights=5,
            failed_lights=["light.a", "light.b"],
            skipped_lights=["light.c"],
            elapsed_seconds=10.123,
        )
        data = result.to_dict()
        assert data["success"] is False
        assert data["result"] == RESULT_CODE_FAILED
        assert data["message"] == "Failed to set lights"
        assert data["attempts"] == 3
        assert data["total_lights"] == 5
        assert data["failed_lights"] == ["light.a", "light.b"]
        assert data["skipped_lights"] == ["light.c"]
        assert data["elapsed_seconds"] == 10.12  # Rounded to 2 decimal places


# =============================================================================
# ColorTolerance Tests
# =============================================================================


class TestColorTolerance:
    """Tests for ColorTolerance dataclass."""

    def test_default_values(self):
        """Test default tolerance values."""
        tolerance = ColorTolerance()
        assert tolerance.brightness == 3
        assert tolerance.rgb == 10
        assert tolerance.kelvin == 150

    def test_custom_values(self):
        """Test custom tolerance values."""
        tolerance = ColorTolerance(brightness=5, rgb=20, kelvin=200)
        assert tolerance.brightness == 5
        assert tolerance.rgb == 20
        assert tolerance.kelvin == 200


# =============================================================================
# LightController Tests
# =============================================================================


class TestLightControllerHelpers:
    """Tests for LightController helper methods."""

    def test_get_state(self, hass, mock_light_states):
        """Test getting entity state."""
        controller = LightController(hass)
        state = controller._get_state("light.test_light_1")
        assert state is not None
        assert state.state == STATE_ON

    def test_get_state_not_found(self, hass, mock_light_states):
        """Test getting non-existent entity state."""
        controller = LightController(hass)
        state = controller._get_state("light.nonexistent")
        assert state is None

    def test_is_available_true(self, hass, mock_light_states):
        """Test checking if entity is available."""
        controller = LightController(hass)
        assert controller._is_available("light.test_light_1") is True
        assert controller._is_available("light.test_light_3") is True

    def test_is_available_false(self, hass, mock_light_states):
        """Test checking if unavailable entity."""
        controller = LightController(hass)
        assert controller._is_available("light.unavailable_light") is False
        assert controller._is_available("light.nonexistent") is False


class TestLightControllerEntityExpansion:
    """Tests for entity expansion methods."""

    def test_expand_single_light(self, hass, mock_light_states):
        """Test expanding a single light entity."""
        controller = LightController(hass)
        valid, skipped = controller._expand_entity("light.test_light_1")
        assert valid == ["light.test_light_1"]
        assert skipped == []

    def test_expand_unavailable_light(self, hass, mock_light_states):
        """Test expanding an unavailable light."""
        controller = LightController(hass)
        valid, skipped = controller._expand_entity("light.unavailable_light")
        assert valid == []
        assert skipped == ["light.unavailable_light"]

    def test_expand_light_group(self, hass, mock_light_states):
        """Test expanding a light group."""
        controller = LightController(hass)
        valid, skipped = controller._expand_entity("light.test_group")
        assert "light.test_light_1" in valid
        assert "light.test_light_2" in valid
        assert skipped == []

    def test_expand_entities_multiple(self, hass, mock_light_states):
        """Test expanding multiple entities."""
        controller = LightController(hass)
        valid, skipped = controller._expand_entities(
            [
                "light.test_light_1",
                "light.test_light_2",
                "light.unavailable_light",
            ]
        )
        assert "light.test_light_1" in valid
        assert "light.test_light_2" in valid
        assert "light.unavailable_light" in skipped

    def test_expand_entities_deduplication(self, hass, mock_light_states):
        """Test that duplicate entities are deduplicated."""
        controller = LightController(hass)
        valid, skipped = controller._expand_entities(
            [
                "light.test_light_1",
                "light.test_light_1",  # Duplicate
                "light.test_group",  # Contains test_light_1
            ]
        )
        # Should only have unique entries
        assert valid.count("light.test_light_1") == 1

    def test_expand_invalid_entity_type(self, hass, mock_light_states):
        """Test expanding non-light entity."""
        controller = LightController(hass)
        valid, skipped = controller._expand_entity("sensor.temperature")
        assert valid == []
        assert skipped == []


class TestLightControllerTargetBuilding:
    """Tests for target building methods."""

    def test_build_targets_basic(self, hass, mock_light_states):
        """Test building basic targets."""
        controller = LightController(hass)
        targets = controller._build_targets(
            members=["light.test_light_1", "light.test_light_2"],
            overrides={},
            default_brightness_pct=75,
            default_rgb_color=None,
            default_color_temp_kelvin=4000,
            default_effect=None,
        )
        assert len(targets) == 2
        assert targets[0].entity_id == "light.test_light_1"
        assert targets[0].brightness_pct == 75
        assert targets[0].color_temp_kelvin == 4000

    def test_build_targets_with_overrides(self, hass, mock_light_states):
        """Test building targets with per-entity overrides."""
        controller = LightController(hass)
        overrides = {
            "light.test_light_1": {
                "entity_id": "light.test_light_1",
                "brightness_pct": 50,
                "rgb_color": [255, 0, 0],
            }
        }
        targets = controller._build_targets(
            members=["light.test_light_1", "light.test_light_2"],
            overrides=overrides,
            default_brightness_pct=100,
            default_rgb_color=None,
            default_color_temp_kelvin=None,
            default_effect=None,
        )
        # First light has override
        assert targets[0].brightness_pct == 50
        assert targets[0].rgb_color == [255, 0, 0]
        # Second light uses defaults
        assert targets[1].brightness_pct == 100
        assert targets[1].rgb_color is None

    def test_build_targets_with_state_override(self, hass, mock_light_states):
        """Test building targets with per-entity state override."""
        controller = LightController(hass)
        overrides = {
            "light.test_light_1": {
                "entity_id": "light.test_light_1",
                "state": "off",
            }
        }
        targets = controller._build_targets(
            members=["light.test_light_1", "light.test_light_2"],
            overrides=overrides,
            default_brightness_pct=100,
            default_rgb_color=None,
            default_color_temp_kelvin=None,
            default_effect=None,
        )
        # First light has state override
        assert targets[0].state == "off"
        # Second light uses default
        assert targets[1].state == "on"

    def test_build_targets_with_transition_override(self, hass, mock_light_states):
        """Test building targets with per-entity transition override."""
        controller = LightController(hass)
        overrides = {
            "light.test_light_1": {
                "entity_id": "light.test_light_1",
                "transition": 3.0,
            }
        }
        targets = controller._build_targets(
            members=["light.test_light_1", "light.test_light_2"],
            overrides=overrides,
            default_brightness_pct=100,
            default_rgb_color=None,
            default_color_temp_kelvin=None,
            default_effect=None,
        )
        # First light has transition override
        assert targets[0].transition == 3.0
        # Second light uses default
        assert targets[1].transition is None


class TestLightControllerVerification:
    """Tests for verification methods."""

    def test_verify_brightness_within_tolerance(self, hass):
        """Test brightness verification within tolerance."""
        from tests.conftest import create_light_state

        state = create_light_state("light.test", STATE_ON, brightness=191)  # ~75%
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        # 75% ± 3% should pass
        assert controller._verify_brightness("light.test", 75, 3) is True

    def test_verify_brightness_outside_tolerance(self, hass):
        """Test brightness verification outside tolerance."""
        from tests.conftest import create_light_state

        state = create_light_state("light.test", STATE_ON, brightness=128)  # ~50%
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        # Target 75%, actual 50%, tolerance 3% - should fail
        assert controller._verify_brightness("light.test", 75, 3) is False

    def test_verify_rgb_within_tolerance(self, hass):
        """Test RGB verification within tolerance."""
        from tests.conftest import create_light_state

        state = create_light_state(
            "light.test",
            STATE_ON,
            rgb_color=(250, 5, 10),
            supported_color_modes=["rgb"],
        )
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        # Target [255, 0, 5], actual [250, 5, 10], tolerance 10 - should pass
        assert controller._verify_rgb("light.test", [255, 0, 5], 10) is True

    def test_verify_rgb_outside_tolerance(self, hass):
        """Test RGB verification outside tolerance."""
        from tests.conftest import create_light_state

        state = create_light_state(
            "light.test",
            STATE_ON,
            rgb_color=(200, 50, 50),
            supported_color_modes=["rgb"],
        )
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        # Target [255, 0, 0], actual [200, 50, 50] - should fail
        assert controller._verify_rgb("light.test", [255, 0, 0], 10) is False

    def test_verify_rgb_none_expected(self, hass):
        """Test RGB verification when no RGB expected."""
        controller = LightController(hass)
        result = controller._verify_rgb("light.test", None, 10)
        assert result is None

    def test_verify_rgb_not_supported(self, hass):
        """Test RGB verification when RGB not supported."""
        from tests.conftest import create_light_state

        state = create_light_state(
            "light.test",
            STATE_ON,
            supported_color_modes=["brightness"],
        )
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        result = controller._verify_rgb("light.test", [255, 0, 0], 10)
        assert result is None

    def test_verify_kelvin_within_tolerance(self, hass):
        """Test kelvin verification within tolerance."""
        from tests.conftest import create_light_state

        state = create_light_state(
            "light.test",
            STATE_ON,
            color_temp_kelvin=4050,
            supported_color_modes=["color_temp"],
        )
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        # Target 4000K, actual 4050K, tolerance 150K - should pass
        assert controller._verify_kelvin("light.test", 4000, 150) is True

    def test_verify_kelvin_outside_tolerance(self, hass):
        """Test kelvin verification outside tolerance."""
        from tests.conftest import create_light_state

        state = create_light_state(
            "light.test",
            STATE_ON,
            color_temp_kelvin=5000,
            supported_color_modes=["color_temp"],
        )
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        # Target 4000K, actual 5000K, tolerance 150K - should fail
        assert controller._verify_kelvin("light.test", 4000, 150) is False

    def test_verify_light_off_target_off(self, hass, mock_light_off):
        """Test verifying light off when target is off."""
        controller = LightController(hass)
        target = LightTarget("light.single_light", brightness_pct=0)
        tolerances = ColorTolerance()

        result = controller._verify_light(target, TargetState.OFF, tolerances)
        assert result == VerificationResult.SUCCESS

    def test_verify_light_on_target_off(self, hass, mock_light_on):
        """Test verifying light on when target is off."""
        controller = LightController(hass)
        target = LightTarget("light.single_light", brightness_pct=0)
        tolerances = ColorTolerance()

        result = controller._verify_light(target, TargetState.OFF, tolerances)
        assert result == VerificationResult.WRONG_STATE

    def test_verify_light_unavailable(self, hass):
        """Test verifying unavailable light."""
        from tests.conftest import create_light_state

        state = create_light_state("light.test", STATE_UNAVAILABLE)
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        target = LightTarget("light.test", brightness_pct=100)
        tolerances = ColorTolerance()

        result = controller._verify_light(target, TargetState.ON, tolerances)
        assert result == VerificationResult.UNAVAILABLE


class TestLightControllerEnsureState:
    """Tests for the main ensure_state method."""

    @pytest.mark.asyncio
    async def test_ensure_state_no_entities(self, hass):
        """Test ensure_state with no entities."""
        controller = LightController(hass)
        result = await controller.ensure_state(entities=[])

        assert result["success"] is False
        assert result["result"] == RESULT_CODE_ERROR
        assert "No entities" in result["message"]

    @pytest.mark.asyncio
    async def test_ensure_state_invalid_state(self, hass, mock_light_states):
        """Test ensure_state with invalid state target."""
        controller = LightController(hass)
        result = await controller.ensure_state(
            entities=["light.test_light_1"],
            state_target="invalid",
        )

        assert result["success"] is False
        assert result["result"] == RESULT_CODE_ERROR
        assert "Invalid state" in result["message"]

    @pytest.mark.asyncio
    async def test_ensure_state_no_valid_entities(self, hass, mock_light_states):
        """Test ensure_state when all entities are unavailable."""
        controller = LightController(hass)
        result = await controller.ensure_state(
            entities=["light.unavailable_light"],
        )

        assert result["success"] is False
        assert result["result"] == RESULT_CODE_NO_VALID_ENTITIES

    @pytest.mark.asyncio
    async def test_ensure_state_fire_and_forget(self, hass, mock_light_states):
        """Test ensure_state in fire-and-forget mode."""
        controller = LightController(hass)
        result = await controller.ensure_state(
            entities=["light.test_light_1"],
            state_target="on",
            default_brightness_pct=100,
            skip_verification=True,
        )

        assert result["success"] is True
        assert result["result"] == RESULT_CODE_SUCCESS
        assert "Fire-and-forget" in result["message"]

        # Verify service was called
        hass.services.async_call.assert_called()

    @pytest.mark.asyncio
    async def test_ensure_state_turn_off(self, hass, mock_light_states):
        """Test ensure_state for turning lights off."""
        # Make lights appear off after command
        from tests.conftest import create_light_state

        call_count = [0]

        def get_state_after_call(entity_id):
            if call_count[0] > 0:
                return create_light_state(entity_id, STATE_OFF)
            return mock_light_states.get(entity_id)

        original_get = hass.states.get

        def mock_get(entity_id):
            result = get_state_after_call(entity_id)
            return result if result else original_get(entity_id)

        async def mark_called(*args, **kwargs):
            call_count[0] += 1

        hass.services.async_call = mark_called
        hass.states.get = mock_get

        controller = LightController(hass)
        result = await controller.ensure_state(
            entities=["light.test_light_1"],
            state_target="off",
            max_retries=1,
            delay_after_send=0.01,
        )

        assert result["success"] is True

    @pytest.mark.asyncio
    async def test_ensure_state_with_transition(self, hass, mock_light_states):
        """Test ensure_state with transition."""
        controller = LightController(hass)
        await controller.ensure_state(
            entities=["light.test_light_1"],
            state_target="on",
            default_brightness_pct=100,
            transition=2.5,
            skip_verification=True,
        )

        # Check that service was called with transition
        call_args = hass.services.async_call.call_args
        assert call_args is not None
        service_data = call_args[0][2]  # Third positional arg is service data
        assert service_data.get("transition") == 2.5

    @pytest.mark.asyncio
    async def test_ensure_state_with_targets(self, hass, mock_light_states):
        """Test ensure_state with per-entity targets."""
        controller = LightController(hass)
        targets = [
            {"entity_id": "light.test_light_1", "brightness_pct": 50},
            {"entity_id": "light.test_light_2", "brightness_pct": 75},
        ]

        result = await controller.ensure_state(
            entities=["light.test_light_1", "light.test_light_2"],
            state_target="on",
            default_brightness_pct=100,
            targets=targets,
            skip_verification=True,
        )

        assert result["success"] is True
        assert result["total_lights"] == 2

    @pytest.mark.asyncio
    async def test_ensure_state_reports_skipped(self, hass, mock_light_states):
        """Test that skipped entities are reported."""
        controller = LightController(hass)
        result = await controller.ensure_state(
            entities=["light.test_light_1", "light.unavailable_light"],
            state_target="on",
            skip_verification=True,
        )

        assert result["success"] is True
        assert "light.unavailable_light" in result["skipped_lights"]


class TestLightControllerCommands:
    """Tests for command execution methods."""

    @pytest.mark.asyncio
    async def test_send_turn_off(self, hass):
        """Test sending turn_off command."""
        controller = LightController(hass)
        await controller._send_turn_off(["light.a", "light.b"])

        hass.services.async_call.assert_called_once_with(
            "light",
            "turn_off",
            {"entity_id": ["light.a", "light.b"]},
            blocking=True,
        )

    @pytest.mark.asyncio
    async def test_send_turn_on(self, hass):
        """Test sending turn_on command."""
        controller = LightController(hass)
        group = LightGroup(
            entities=["light.a", "light.b"],
            brightness_pct=75,
            rgb_color=[255, 0, 0],
        )
        await controller._send_turn_on(group, transition=1.5)

        call_args = hass.services.async_call.call_args
        assert call_args[0][0] == "light"
        assert call_args[0][1] == "turn_on"
        service_data = call_args[0][2]
        assert service_data["entity_id"] == ["light.a", "light.b"]
        assert service_data["brightness_pct"] == 75
        assert service_data["rgb_color"] == [255, 0, 0]
        assert service_data["transition"] == 1.5

    @pytest.mark.asyncio
    async def test_send_turn_off_exception(self, hass):
        """Test that turn_off exception is logged but doesn't crash."""
        hass.services.async_call = AsyncMock(side_effect=Exception("Service error"))
        controller = LightController(hass)
        # Should not raise exception
        await controller._send_turn_off(["light.a"])
        hass.services.async_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_turn_on_exception(self, hass):
        """Test that turn_on exception is logged but doesn't crash."""
        hass.services.async_call = AsyncMock(side_effect=Exception("Service error"))
        controller = LightController(hass)
        group = LightGroup(entities=["light.a"], brightness_pct=75)
        # Should not raise exception
        await controller._send_turn_on(group)
        hass.services.async_call.assert_called_once()


class TestLightControllerLogging:
    """Tests for logging and notification methods."""

    @pytest.mark.asyncio
    async def test_log_to_logbook(self, hass):
        """Test logging to logbook."""
        controller = LightController(hass)
        await controller._log_to_logbook("Test Name", "Test message")

        hass.services.async_call.assert_called_once_with(
            "logbook",
            "log",
            {"name": "Test Name", "message": "Test message"},
            blocking=False,
        )

    @pytest.mark.asyncio
    async def test_log_to_logbook_exception(self, hass):
        """Test that logbook exception doesn't crash."""
        hass.services.async_call = AsyncMock(side_effect=Exception("Logbook error"))
        controller = LightController(hass)
        # Should not raise
        await controller._log_to_logbook("Test", "Message")


class TestLightGroupWithEffect:
    """Tests for LightGroup with effect."""

    def test_to_service_data_with_effect(self):
        """Test service data includes effect."""
        group = LightGroup(
            entities=["light.a"],
            brightness_pct=75,
            effect="rainbow",
        )
        data = group.to_service_data()
        assert data == {"brightness_pct": 75, "effect": "rainbow"}


class TestLightControllerEntityExpansionEdgeCases:
    """Tests for entity expansion edge cases."""

    def test_expand_invalid_entity_type(self, hass):
        """Test expanding non-string entity_id."""
        controller = LightController(hass)
        valid, skipped = controller._expand_entity(12345)  # Not a string
        assert valid == []
        assert skipped == []

    def test_expand_group_domain_entity(self, hass):
        """Test expanding traditional group.* domain entity."""
        from tests.conftest import create_light_state

        # Create a group.* entity with member lights
        group_state = MagicMock()
        group_state.state = "on"
        group_state.attributes = {
            "entity_id": ["light.member_1", "light.member_2", "sensor.not_a_light"]
        }

        # Create member light states
        member_1 = create_light_state("light.member_1", STATE_ON)
        member_2 = create_light_state("light.member_2", STATE_ON)

        def get_state(entity_id):
            if entity_id == "group.test_group":
                return group_state
            elif entity_id == "light.member_1":
                return member_1
            elif entity_id == "light.member_2":
                return member_2
            return None

        hass.states.get = MagicMock(side_effect=get_state)

        controller = LightController(hass)
        valid, skipped = controller._expand_entity("group.test_group")

        assert "light.member_1" in valid
        assert "light.member_2" in valid
        # sensor.not_a_light should be ignored (not a light)
        assert "sensor.not_a_light" not in valid
        assert "sensor.not_a_light" not in skipped

    def test_expand_group_with_unavailable_member(self, hass):
        """Test expanding group with unavailable member lights."""
        from tests.conftest import create_light_state

        # Create light group with member entities
        group_state = MagicMock()
        group_state.state = "on"
        group_state.attributes = {"entity_id": ["light.available", "light.unavailable"]}

        available = create_light_state("light.available", STATE_ON)
        unavailable = create_light_state("light.unavailable", STATE_UNAVAILABLE)

        def get_state(entity_id):
            if entity_id == "light.test_group":
                return group_state
            elif entity_id == "light.available":
                return available
            elif entity_id == "light.unavailable":
                return unavailable
            return None

        hass.states.get = MagicMock(side_effect=get_state)

        controller = LightController(hass)
        valid, skipped = controller._expand_entity("light.test_group")

        assert "light.available" in valid
        assert "light.unavailable" in skipped

    def test_expand_group_domain_empty(self, hass):
        """Test expanding group.* domain entity with no members."""
        # Create a group.* entity with no entity_id members
        group_state = MagicMock()
        group_state.state = "on"
        group_state.attributes = {}  # No entity_id attribute

        def get_state(entity_id):
            if entity_id == "group.empty":
                return group_state
            return None

        hass.states.get = MagicMock(side_effect=get_state)

        controller = LightController(hass)
        valid, skipped = controller._expand_entity("group.empty")

        # With no members, nothing to expand
        assert valid == []
        assert skipped == []

    def test_expand_non_light_non_group_entity(self, hass):
        """Test expanding a non-light, non-group entity logs warning.

        Entities that don't start with 'light.' and don't have member entities
        should be logged as warnings and return empty results.
        """
        # Create a sensor entity (not a light or group)
        sensor_state = MagicMock()
        sensor_state.state = "50"
        sensor_state.attributes = {}  # No entity_id members

        hass.states.get = MagicMock(return_value=sensor_state)

        controller = LightController(hass)
        valid, skipped = controller._expand_entity("sensor.test")

        # Neither valid nor skipped - just ignored
        assert valid == []
        assert skipped == []


class TestLightControllerVerificationEdgeCases:
    """Tests for verification edge cases."""

    def test_verify_rgb_invalid_actual(self, hass):
        """Test RGB verification with invalid actual RGB value."""
        from tests.conftest import create_light_state

        state = create_light_state(
            "light.test",
            STATE_ON,
            rgb_color=None,  # No RGB color set
            supported_color_modes=["rgb"],
        )
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        result = controller._verify_rgb("light.test", [255, 0, 0], 10)
        assert result is False

    def test_verify_kelvin_none_expected(self, hass):
        """Test kelvin verification when no kelvin expected."""
        controller = LightController(hass)
        result = controller._verify_kelvin("light.test", None, 150)
        assert result is None

    def test_verify_kelvin_not_supported(self, hass):
        """Test kelvin verification when color_temp not supported."""
        from tests.conftest import create_light_state

        state = create_light_state(
            "light.test",
            STATE_ON,
            supported_color_modes=["brightness"],  # No color_temp
        )
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        result = controller._verify_kelvin("light.test", 4000, 150)
        assert result is None

    def test_verify_kelvin_no_actual_value(self, hass):
        """Test kelvin verification when no actual kelvin value."""
        from tests.conftest import create_light_state

        state = create_light_state(
            "light.test",
            STATE_ON,
            color_temp_kelvin=None,
            supported_color_modes=["color_temp"],
        )
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        result = controller._verify_kelvin("light.test", 4000, 150)
        assert result is False

    def test_verify_light_wrong_state_on(self, hass):
        """Test verifying light off when target is on."""
        from tests.conftest import create_light_state

        state = create_light_state("light.test", STATE_OFF)
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        target = LightTarget("light.test", brightness_pct=100)
        tolerances = ColorTolerance()

        result = controller._verify_light(target, TargetState.ON, tolerances)
        assert result == VerificationResult.WRONG_STATE

    def test_verify_light_wrong_brightness(self, hass):
        """Test verifying light with wrong brightness."""
        from tests.conftest import create_light_state

        state = create_light_state("light.test", STATE_ON, brightness=50)  # ~20%
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        target = LightTarget("light.test", brightness_pct=100)
        tolerances = ColorTolerance(brightness=3)

        result = controller._verify_light(target, TargetState.ON, tolerances)
        assert result == VerificationResult.WRONG_BRIGHTNESS

    def test_verify_light_rgb_only_wrong_color_fails(self, hass):
        """Test verifying light with RGB target but wrong color returns WRONG_COLOR."""
        from tests.conftest import create_light_state

        state = create_light_state(
            "light.test",
            STATE_ON,
            brightness=255,
            rgb_color=(0, 0, 255),  # Blue
            supported_color_modes=["rgb"],
        )
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        target = LightTarget(
            "light.test", brightness_pct=100, rgb_color=[255, 0, 0]
        )  # Red
        tolerances = ColorTolerance()

        result = controller._verify_light(target, TargetState.ON, tolerances)
        assert result == VerificationResult.WRONG_COLOR

    def test_verify_light_rgb_only_correct_color_succeeds(self, hass):
        """Regression: RGB-only target with matching color returns SUCCESS."""
        from tests.conftest import create_light_state

        state = create_light_state(
            "light.test",
            STATE_ON,
            brightness=255,
            rgb_color=(255, 0, 0),
            supported_color_modes=["rgb"],
        )
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        target = LightTarget(
            "light.test", brightness_pct=100, rgb_color=[255, 0, 0]
        )
        tolerances = ColorTolerance()

        result = controller._verify_light(target, TargetState.ON, tolerances)
        assert result == VerificationResult.SUCCESS

    def test_verify_light_kelvin_only_correct_color_succeeds(self, hass):
        """Regression: kelvin-only target with matching temp returns SUCCESS."""
        from tests.conftest import create_light_state

        state = create_light_state(
            "light.test",
            STATE_ON,
            brightness=255,
            color_temp_kelvin=2700,
            supported_color_modes=["color_temp"],
        )
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        target = LightTarget(
            "light.test", brightness_pct=100, color_temp_kelvin=2700
        )
        tolerances = ColorTolerance(kelvin=150)

        result = controller._verify_light(target, TargetState.ON, tolerances)
        assert result == VerificationResult.SUCCESS

    def test_verify_light_kelvin_only_wrong_color_fails(self, hass):
        """Test verifying light with kelvin target but wrong temp returns WRONG_COLOR."""
        from tests.conftest import create_light_state

        state = create_light_state(
            "light.test",
            STATE_ON,
            brightness=255,
            color_temp_kelvin=6500,  # Cool white
            supported_color_modes=["color_temp"],
        )
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        target = LightTarget(
            "light.test", brightness_pct=100, color_temp_kelvin=2700
        )  # Warm
        tolerances = ColorTolerance(kelvin=150)

        result = controller._verify_light(target, TargetState.ON, tolerances)
        assert result == VerificationResult.WRONG_COLOR

    def test_verify_light_both_wrong_fails(self, hass):
        """Test that verification fails when both RGB and kelvin are specified and wrong."""
        from tests.conftest import create_light_state

        state = create_light_state(
            "light.test",
            STATE_ON,
            brightness=255,
            rgb_color=(0, 0, 255),  # Blue
            color_temp_kelvin=6500,  # Cool white
            supported_color_modes=["rgb", "color_temp"],
        )
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        target = LightTarget(
            "light.test",
            brightness_pct=100,
            rgb_color=[255, 0, 0],  # Red (wrong)
            color_temp_kelvin=2700,  # Warm (wrong)
        )
        tolerances = ColorTolerance(kelvin=150)

        result = controller._verify_light(target, TargetState.ON, tolerances)
        # Both specified and both wrong = WRONG_COLOR
        assert result == VerificationResult.WRONG_COLOR

    def test_verify_light_both_rgb_and_kelvin_rgb_matches_kelvin_missing(self, hass):
        """When both modes targeted, RGB matches but kelvin not active → WRONG_COLOR.

        A light can only be in one color mode at a time. If both are requested
        and the light is in RGB mode, kelvin verification fails because the
        attribute is absent (supported but not active). Both requested modes
        must match per PLR-001 fix.
        """
        from tests.conftest import create_light_state

        state = create_light_state(
            "light.test",
            STATE_ON,
            brightness=255,
            rgb_color=(255, 0, 0),
            supported_color_modes=["rgb", "color_temp"],
        )
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        target = LightTarget(
            "light.test",
            brightness_pct=100,
            rgb_color=[255, 0, 0],
            color_temp_kelvin=4000,
        )
        tolerances = ColorTolerance()

        result = controller._verify_light(target, TargetState.ON, tolerances)
        assert result == VerificationResult.WRONG_COLOR

    def test_verify_light_both_unsupported(self, hass):
        """Test verifying light with both RGB and kelvin but neither supported."""
        from tests.conftest import create_light_state

        state = create_light_state(
            "light.test",
            STATE_ON,
            brightness=255,
            supported_color_modes=["brightness"],
        )
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        target = LightTarget(
            "light.test",
            brightness_pct=100,
            rgb_color=[255, 0, 0],
            color_temp_kelvin=4000,
        )
        tolerances = ColorTolerance()

        result = controller._verify_light(target, TargetState.ON, tolerances)
        assert result == VerificationResult.SUCCESS

    def test_verify_light_exception(self, hass):
        """Test verifying light when exception occurs."""
        hass.states.get = MagicMock(side_effect=Exception("State error"))

        controller = LightController(hass)
        target = LightTarget("light.test", brightness_pct=100)
        tolerances = ColorTolerance()

        result = controller._verify_light(target, TargetState.ON, tolerances)
        assert result == VerificationResult.ERROR

    def test_verify_light_both_rgb_and_kelvin_both_wrong(self, hass):
        """Test verifying light when both RGB and kelvin are set but both are wrong."""
        from tests.conftest import create_light_state

        # Light supports both RGB and color_temp, but actual values don't match
        state = create_light_state(
            "light.test",
            STATE_ON,
            brightness=255,
            rgb_color=(0, 0, 255),  # Blue (wrong)
            color_temp_kelvin=6500,  # Cold (wrong)
            supported_color_modes=["rgb", "color_temp"],
        )
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        target = LightTarget(
            "light.test",
            brightness_pct=100,
            rgb_color=[255, 0, 0],  # Red (target)
            color_temp_kelvin=2700,  # Warm (target)
        )
        tolerances = ColorTolerance(rgb=5, kelvin=100)

        result = controller._verify_light(target, TargetState.ON, tolerances)
        assert result == VerificationResult.WRONG_COLOR

    def test_verify_light_no_color_targets(self, hass):
        """Test verifying light with no color targets (brightness only)."""
        from tests.conftest import create_light_state

        state = create_light_state(
            "light.test",
            STATE_ON,
            brightness=255,
        )
        hass.states.get = MagicMock(return_value=state)

        controller = LightController(hass)
        target = LightTarget("light.test", brightness_pct=100)
        tolerances = ColorTolerance()

        result = controller._verify_light(target, TargetState.ON, tolerances)
        assert result == VerificationResult.SUCCESS


class TestLightControllerEnsureStateAdvanced:
    """Advanced tests for ensure_state."""

    @pytest.mark.asyncio
    async def test_ensure_state_fire_and_forget_with_log_success(
        self, hass, mock_light_states
    ):
        """Test fire-and-forget mode with log_success=True."""
        controller = LightController(hass)
        result = await controller.ensure_state(
            entities=["light.test_light_1"],
            state_target="on",
            skip_verification=True,
            log_success=True,
        )

        assert result["success"] is True
        # Verify logbook was called
        assert hass.services.async_call.call_count >= 2  # turn_on + logbook

    @pytest.mark.asyncio
    async def test_ensure_state_timeout(self, hass, mock_light_states):
        """Test ensure_state timeout."""
        # Make verification always fail
        from tests.conftest import create_light_state

        wrong_state = create_light_state("light.test_light_1", STATE_OFF)
        hass.states.get = MagicMock(return_value=wrong_state)

        controller = LightController(hass)
        result = await controller.ensure_state(
            entities=["light.test_light_1"],
            state_target="on",
            max_retries=10,  # High retries so we hit timeout first
            max_runtime_seconds=0.001,  # Very short timeout
            delay_after_send=0.1,  # Long enough to exceed timeout
        )

        assert result["success"] is False
        assert result["result"] == RESULT_CODE_TIMEOUT

    @pytest.mark.asyncio
    async def test_ensure_state_timeout_with_notification(
        self, hass, mock_light_states
    ):
        """Test ensure_state timeout with notification."""
        from tests.conftest import create_light_state

        wrong_state = create_light_state("light.test_light_1", STATE_OFF)
        hass.states.get = MagicMock(return_value=wrong_state)

        controller = LightController(hass)
        result = await controller.ensure_state(
            entities=["light.test_light_1"],
            state_target="on",
            max_retries=10,  # High retries so we hit timeout first
            max_runtime_seconds=0.001,  # Very short timeout
            delay_after_send=0.1,  # Long enough to exceed timeout
        )

        assert result["success"] is False
        assert result["result"] == RESULT_CODE_TIMEOUT

    @pytest.mark.asyncio
    async def test_ensure_state_failed_with_notification(self, hass, mock_light_states):
        """Test ensure_state failure with notification."""
        from tests.conftest import create_light_state

        wrong_state = create_light_state("light.test_light_1", STATE_OFF)
        hass.states.get = MagicMock(return_value=wrong_state)

        controller = LightController(hass)
        result = await controller.ensure_state(
            entities=["light.test_light_1"],
            state_target="on",
            max_retries=1,
            max_runtime_seconds=60,  # Enough time to not timeout
            delay_after_send=0.001,
        )

        assert result["success"] is False
        assert result["result"] == RESULT_CODE_FAILED

    @pytest.mark.asyncio
    async def test_ensure_state_success_with_skipped_and_log(
        self, hass, mock_light_states
    ):
        """Test success with skipped entities and log_success (fire-and-forget)."""
        controller = LightController(hass)
        result = await controller.ensure_state(
            entities=["light.test_light_1", "light.unavailable_light"],
            state_target="on",
            skip_verification=True,
            log_success=True,
        )

        assert result["success"] is True
        assert "light.unavailable_light" in result["skipped_lights"]

    @pytest.mark.asyncio
    async def test_ensure_state_verified_success_with_skipped_and_log(
        self, hass, mock_light_states
    ):
        """Test verified success with skipped entities and log_success."""
        from tests.conftest import create_light_state

        # Light starts on and stays on - verification passes immediately
        success_state = create_light_state(
            "light.test_light_1", STATE_ON, brightness=255
        )
        unavail_state = create_light_state("light.unavailable_light", STATE_UNAVAILABLE)

        def get_state(entity_id):
            if entity_id == "light.test_light_1":
                return success_state
            elif entity_id == "light.unavailable_light":
                return unavail_state
            return mock_light_states.get(entity_id)

        hass.states.get = MagicMock(side_effect=get_state)

        controller = LightController(hass)
        result = await controller.ensure_state(
            entities=["light.test_light_1", "light.unavailable_light"],
            state_target="on",
            default_brightness_pct=100,
            skip_verification=False,
            log_success=True,
            max_retries=1,
            delay_after_send=0.001,
        )

        assert result["success"] is True
        assert "light.unavailable_light" in result["skipped_lights"]
        # Message should include info about skipped entities
        assert "Skipped" in result["message"] or "skipped" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_ensure_state_with_transition_first_attempt(
        self, hass, mock_light_states
    ):
        """Test that transition is only used on first attempt."""
        from tests.conftest import create_light_state

        # First call fails verification, second succeeds
        call_count = [0]
        transitions_used: list[float | None] = []

        def get_state(entity_id):
            if entity_id == "light.test_light_1":
                if call_count[0] < 2:
                    return create_light_state("light.test_light_1", STATE_OFF)
                return create_light_state(
                    "light.test_light_1", STATE_ON, brightness=255
                )
            return mock_light_states.get(entity_id)

        async def mark_call(*args, **kwargs):
            if args[1] == "turn_on":
                call_count[0] += 1
                service_data = args[2]
                transitions_used.append(service_data.get("transition"))

        hass.states.get = MagicMock(side_effect=get_state)
        hass.services.async_call = AsyncMock(side_effect=mark_call)

        controller = LightController(hass)
        result = await controller.ensure_state(
            entities=["light.test_light_1"],
            state_target="on",
            default_brightness_pct=100,
            transition=2.5,
            max_retries=2,
            delay_after_send=0.001,
        )

        assert result["success"] is True
        assert transitions_used == [2.5, None]

    @pytest.mark.asyncio
    async def test_ensure_state_retries_entire_failed_batch(
        self, hass, mock_light_states
    ):
        """Test retry behavior re-sends the full batch if one light fails."""
        from tests.conftest import create_light_state

        turn_on_calls = 0
        sent_batches: list[list[str]] = []

        def get_state(entity_id):
            nonlocal turn_on_calls
            if entity_id == "light.group_ok":
                return create_light_state(entity_id, STATE_ON, brightness=255)
            if entity_id == "light.group_flaky":
                if turn_on_calls < 2:
                    return create_light_state(entity_id, STATE_OFF)
                return create_light_state(entity_id, STATE_ON, brightness=255)
            return mock_light_states.get(entity_id)

        async def mock_call(domain, service, data, **kwargs):
            nonlocal turn_on_calls
            if service == "turn_on":
                turn_on_calls += 1
                entities = data.get("entity_id", [])
                if not isinstance(entities, list):
                    entities = [entities]
                sent_batches.append(entities)

        hass.states.get = MagicMock(side_effect=get_state)
        hass.services.async_call = AsyncMock(side_effect=mock_call)

        controller = LightController(hass)
        result = await controller.ensure_state(
            entities=["light.group_ok", "light.group_flaky"],
            state_target="on",
            default_brightness_pct=100,
            max_retries=3,
            delay_after_send=0.001,
        )

        assert result["success"] is True
        assert len(sent_batches) == 2
        assert set(sent_batches[0]) == {"light.group_ok", "light.group_flaky"}
        assert set(sent_batches[1]) == {"light.group_ok", "light.group_flaky"}


class TestGroupOverrideExpansion:
    """Tests that group entity overrides are remapped to individual members (PLR-002)."""

    @pytest.mark.asyncio
    async def test_group_override_applied_to_members(self, hass):
        """Override keyed to a group entity should apply to each member light."""
        from tests.conftest import create_light_state

        # Group with two members
        group_state = MagicMock()
        group_state.state = "on"
        group_state.attributes = {
            "entity_id": ["light.lamp1", "light.lamp2"],
        }
        lamp_state = create_light_state(
            "light.lamp1", STATE_ON, brightness=255
        )

        def get_state(entity_id):
            if entity_id == "light.living_room":
                return group_state
            return lamp_state

        hass.states.get = MagicMock(side_effect=get_state)

        controller = LightController(hass)
        result = await controller.ensure_state(
            entities=["light.living_room"],
            state_target="on",
            default_brightness_pct=100,
            targets=[
                {
                    "entity_id": "light.living_room",
                    "brightness_pct": 50,
                    "rgb_color": [255, 0, 0],
                }
            ],
            skip_verification=True,
        )

        assert result["success"] is True
        # Verify the group override was applied
        call_args = hass.services.async_call.call_args_list
        assert len(call_args) > 0
        for call in call_args:
            sdata = call[1].get("service_data") or call[0][2]
            if "brightness_pct" in sdata:
                assert sdata["brightness_pct"] == 50


class TestMixedStateHandling:
    """Tests for handling presets with mixed on/off states."""

    @pytest.mark.asyncio
    async def test_send_commands_splits_by_state(self, hass, mock_light_states):
        """Test that _send_commands_per_target handles mixed per-entity states."""
        controller = LightController(hass)

        # Create targets with mixed states
        targets = [
            LightTarget("light.on_1", brightness_pct=100, state="on"),
            LightTarget("light.on_2", brightness_pct=100, state="on"),
            LightTarget("light.off_1", brightness_pct=100, state="off"),
        ]

        # Track which entities get which commands
        turn_on_calls = []
        turn_off_calls = []

        async def mock_call(domain, service, data, **kwargs):
            if service == "turn_on":
                turn_on_calls.append(data.get("entity_id", []))
            elif service == "turn_off":
                turn_off_calls.append(data.get("entity_id", []))

        hass.services.async_call = AsyncMock(side_effect=mock_call)

        # Call the method that handles state splitting
        await controller._send_commands_per_target(targets)

        # Verify on commands went to on lights
        all_on_entities = [
            e
            for call in turn_on_calls
            for e in (call if isinstance(call, list) else [call])
        ]
        assert "light.on_1" in all_on_entities
        assert "light.on_2" in all_on_entities
        assert "light.off_1" not in all_on_entities

        # Verify off command went to off light
        all_off_entities = [
            e
            for call in turn_off_calls
            for e in (call if isinstance(call, list) else [call])
        ]
        assert "light.off_1" in all_off_entities

    @pytest.mark.asyncio
    async def test_send_commands_groups_on_targets_by_settings(
        self, hass, mock_light_states
    ):
        """Test that on targets are grouped by settings for efficient batching."""
        controller = LightController(hass)

        # Create targets with same settings (should be batched) and different settings
        targets = [
            LightTarget(
                "light.same_1", brightness_pct=75, color_temp_kelvin=4000, state="on"
            ),
            LightTarget(
                "light.same_2", brightness_pct=75, color_temp_kelvin=4000, state="on"
            ),
            LightTarget(
                "light.different", brightness_pct=50, color_temp_kelvin=3000, state="on"
            ),
        ]

        turn_on_calls = []

        async def mock_call(domain, service, data, **kwargs):
            if service == "turn_on":
                turn_on_calls.append(data.copy())

        hass.services.async_call = AsyncMock(side_effect=mock_call)

        await controller._send_commands_per_target(targets)

        # Should have 2 turn_on calls: one for batched lights, one for different light
        assert len(turn_on_calls) == 2

    @pytest.mark.asyncio
    async def test_send_commands_respects_per_entity_transition(
        self, hass, mock_light_states
    ):
        """Test that per-entity transition overrides global transition."""
        controller = LightController(hass)

        # Create targets with different transitions
        targets = [
            LightTarget(
                "light.custom_trans", brightness_pct=100, state="on", transition=5.0
            ),
            LightTarget(
                "light.global_trans", brightness_pct=100, state="on", transition=None
            ),
        ]

        turn_on_calls = []

        async def mock_call(domain, service, data, **kwargs):
            if service == "turn_on":
                turn_on_calls.append(data.copy())

        hass.services.async_call = AsyncMock(side_effect=mock_call)

        # Call with global transition of 2.0
        await controller._send_commands_per_target(targets, global_transition=2.0)

        # Should have 2 calls since transitions differ
        assert len(turn_on_calls) == 2

        # Find the call with custom transition
        custom_call = next(
            c for c in turn_on_calls if "light.custom_trans" in c.get("entity_id", [])
        )
        global_call = next(
            c for c in turn_on_calls if "light.global_trans" in c.get("entity_id", [])
        )

        assert custom_call.get("transition") == 5.0
        assert global_call.get("transition") == 2.0

    @pytest.mark.asyncio
    async def test_send_commands_all_off(self, hass, mock_light_states):
        """Test that all-off targets only send turn_off commands."""
        controller = LightController(hass)

        targets = [
            LightTarget("light.off_1", brightness_pct=100, state="off"),
            LightTarget("light.off_2", brightness_pct=100, state="off"),
        ]

        turn_on_calls = []
        turn_off_calls = []

        async def mock_call(domain, service, data, **kwargs):
            if service == "turn_on":
                turn_on_calls.append(data.get("entity_id", []))
            elif service == "turn_off":
                turn_off_calls.append(data.get("entity_id", []))

        hass.services.async_call = AsyncMock(side_effect=mock_call)

        await controller._send_commands_per_target(targets)

        # No turn_on calls
        assert len(turn_on_calls) == 0

        # All entities in turn_off calls
        all_off_entities = [
            e
            for call in turn_off_calls
            for e in (call if isinstance(call, list) else [call])
        ]
        assert "light.off_1" in all_off_entities
        assert "light.off_2" in all_off_entities

    @pytest.mark.asyncio
    async def test_send_commands_all_on(self, hass, mock_light_states):
        """Test that all-on targets only send turn_on commands."""
        controller = LightController(hass)

        targets = [
            LightTarget("light.on_1", brightness_pct=100, state="on"),
            LightTarget("light.on_2", brightness_pct=100, state="on"),
        ]

        turn_on_calls = []
        turn_off_calls = []

        async def mock_call(domain, service, data, **kwargs):
            if service == "turn_on":
                turn_on_calls.append(data.get("entity_id", []))
            elif service == "turn_off":
                turn_off_calls.append(data.get("entity_id", []))

        hass.services.async_call = AsyncMock(side_effect=mock_call)

        await controller._send_commands_per_target(targets)

        # No turn_off calls
        assert len(turn_off_calls) == 0

        # All entities in turn_on calls
        all_on_entities = [
            e
            for call in turn_on_calls
            for e in (call if isinstance(call, list) else [call])
        ]
        assert "light.on_1" in all_on_entities
        assert "light.on_2" in all_on_entities


class TestEnsureStateMixedTargets:
    """Tests for ensure_state with mixed per-entity states."""

    @pytest.mark.asyncio
    async def test_ensure_state_mixed_states(self, hass, mock_light_states):
        """Test ensure_state handles targets with mixed on/off states."""
        from tests.conftest import create_light_state

        # Set up state tracking
        entity_states = {
            "light.turn_on": "off",  # Currently off, target on
            "light.turn_off": "on",  # Currently on, target off
        }

        def get_state(entity_id):
            state_value = entity_states.get(entity_id, "unavailable")
            return create_light_state(entity_id, state_value, brightness=255)

        async def mock_call(domain, service, data, **kwargs):
            entities = data.get("entity_id", [])
            if not isinstance(entities, list):
                entities = [entities]
            for entity_id in entities:
                if service == "turn_on":
                    entity_states[entity_id] = "on"
                elif service == "turn_off":
                    entity_states[entity_id] = "off"

        hass.states.get = MagicMock(side_effect=get_state)
        hass.services.async_call = AsyncMock(side_effect=mock_call)

        controller = LightController(hass)

        result = await controller.ensure_state(
            entities=["light.turn_on", "light.turn_off"],
            state_target="on",  # Global default
            targets=[
                {"entity_id": "light.turn_on", "state": "on", "brightness_pct": 100},
                {"entity_id": "light.turn_off", "state": "off"},
            ],
        )

        assert result["success"] is True
        # Verify final states
        assert entity_states["light.turn_on"] == "on"
        assert entity_states["light.turn_off"] == "off"


class TestPerEntityTransition:
    """Tests for per-entity transition handling."""

    @pytest.mark.asyncio
    async def test_ensure_state_per_entity_transition(self, hass, mock_light_states):
        """Test that per-entity transitions are respected."""
        from tests.conftest import create_light_state

        transitions_used = {}

        async def mock_call(domain, service, data, **kwargs):
            if service == "turn_on":
                entities = data.get("entity_id", [])
                transition = data.get("transition")
                if not isinstance(entities, list):
                    entities = [entities]
                for entity_id in entities:
                    transitions_used[entity_id] = transition

        hass.services.async_call = AsyncMock(side_effect=mock_call)

        # Set up states that will verify on first attempt
        def get_state(entity_id):
            return create_light_state(entity_id, "on", brightness=255)

        hass.states.get = MagicMock(side_effect=get_state)

        controller = LightController(hass)

        await controller.ensure_state(
            entities=["light.fast", "light.slow"],
            state_target="on",
            transition=1.0,  # Global fallback
            targets=[
                {"entity_id": "light.fast", "transition": 0.5},
                {"entity_id": "light.slow", "transition": 3.0},
            ],
            skip_verification=True,
        )

        # Verify per-entity transitions were used
        assert transitions_used.get("light.fast") == 0.5
        assert transitions_used.get("light.slow") == 3.0


class TestCoverageGaps:
    """Tests to cover remaining coverage gaps."""

    def test_expand_entity_non_string_member(self, hass):
        """Test that non-string members in a group are skipped during expansion.

        Covers: line 244 (continue when member is not a string)
        """
        from tests.conftest import create_light_state

        # Create a group that has a non-string member in its entity_id list
        states = {
            "light.test_group": create_light_state(
                "light.test_group",
                STATE_ON,
                entity_ids=[123, "light.valid", None, 456.789],
            ),
            "light.valid": create_light_state("light.valid", STATE_ON, brightness=255),
        }
        hass.states.get = lambda eid: states.get(eid)
        controller = LightController(hass)
        valid, skipped = controller._expand_entity("light.test_group")
        assert "light.valid" in valid
        # Non-string members should be skipped silently
        assert 123 not in valid
        assert None not in valid
        assert 456.789 not in valid

    @pytest.mark.asyncio
    async def test_ensure_state_turn_off(self, hass, mock_light_states):
        """Test ensure_state for turning lights off.

        Covers: turn_off path through _send_commands_per_target
        """
        from tests.conftest import create_light_state

        controller = LightController(hass)
        # After turn_off command, light becomes off
        call_count = [0]
        original_get = hass.states.get

        def dynamic_get(entity_id):
            if entity_id == "light.test_light_1" and call_count[0] > 0:
                return create_light_state(entity_id, STATE_OFF)
            return original_get(entity_id)

        hass.states.get = dynamic_get

        async def track_call(*args, **kwargs):
            call_count[0] += 1

        hass.services.async_call = AsyncMock(side_effect=track_call)

        await controller.ensure_state(
            entities=["light.test_light_1"],
            state_target="off",
            delay_after_send=0.001,
            max_retries=2,
            max_runtime_seconds=5,
        )
        # Verify turn_off was called
        assert any(
            c[0][1] == "turn_off" for c in hass.services.async_call.call_args_list
        )

    @pytest.mark.asyncio
    async def test_ensure_state_no_valid_entities_no_skipped(self, hass):
        """Test ensure_state when no valid entities and none skipped.

        Covers: branch 713→715 (no skipped_entities when no valid entities found)
        """
        # sensor.temp has no state and is not a light entity
        hass.states.get = MagicMock(return_value=None)
        controller = LightController(hass)
        result = await controller.ensure_state(
            entities=["sensor.temp"],
            state_target="on",
            delay_after_send=0.001,
        )
        assert result["success"] is False
        assert "No valid light entities found" in result["message"]
        # No "Skipped:" in message because nothing was skipped
        assert "Skipped" not in result["message"]

    @pytest.mark.asyncio
    async def test_ensure_state_targets_none(self, hass, mock_light_states):
        """Test ensure_state with targets=None (default).

        Covers: branch 735→734 (targets parameter is None/falsy)
        """
        controller = LightController(hass)
        # Just verify it works without targets
        result = await controller.ensure_state(
            entities=["light.test_light_1"],
            state_target="on",
            targets=None,
            skip_verification=True,
            delay_after_send=0.001,
        )
        assert result["success"] is True
