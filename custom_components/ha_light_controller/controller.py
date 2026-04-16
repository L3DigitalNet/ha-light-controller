"""Core light controller logic."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from enum import Enum
from time import monotonic
from typing import Any

from homeassistant.const import STATE_OFF, STATE_ON, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, State

from .const import (
    COLOR_MODE_COLOR_TEMP,
    COLOR_MODE_HS,
    COLOR_MODE_RGB,
    RESULT_ATTEMPTS,
    RESULT_CODE,
    RESULT_CODE_ERROR,
    RESULT_CODE_FAILED,
    RESULT_CODE_NO_VALID_ENTITIES,
    RESULT_CODE_SUCCESS,
    RESULT_CODE_TIMEOUT,
    RESULT_ELAPSED_SECONDS,
    RESULT_FAILED_LIGHTS,
    RESULT_MESSAGE,
    RESULT_SKIPPED_LIGHTS,
    RESULT_SUCCESS,
    RESULT_TOTAL_LIGHTS,
)

_LOGGER = logging.getLogger(__name__)
LIGHT_DOMAIN = "light"

type GroupTransitionKey = tuple[
    int,
    tuple[int, ...] | None,
    int | None,
    str | None,
    float | None,
]


# =============================================================================
# ENUMS
# =============================================================================


class TargetState(Enum):
    """Target state for lights."""

    ON = "on"
    OFF = "off"

    @classmethod
    def from_string(cls, value: str) -> TargetState:
        """Parse a string into a TargetState enum value."""
        normalized = value.lower().strip()
        for state in cls:
            if state.value == normalized:
                return state
        raise ValueError(f"Invalid state '{value}'. Must be 'on' or 'off'.")


class VerificationResult(Enum):
    """Result of verifying a light's state."""

    SUCCESS = "success"
    WRONG_STATE = "wrong_state"
    WRONG_BRIGHTNESS = "brightness"
    WRONG_COLOR = "color"
    UNAVAILABLE = "unavailable"
    ERROR = "error"


# =============================================================================
# DATACLASSES
# =============================================================================


@dataclass
class ColorTolerance:
    """Tolerance configuration for color verification."""

    brightness: int = 3
    rgb: int = 10
    kelvin: int = 150


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""

    max_retries: int = 3
    delay_after_send: float = 2.0
    max_runtime_seconds: float = 60.0
    use_exponential_backoff: bool = False
    max_backoff_seconds: float = 30.0

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt with optional exponential backoff."""
        if self.use_exponential_backoff and attempt > 0:
            delay = self.delay_after_send * (2**attempt)
            return float(min(delay, self.max_backoff_seconds))
        return self.delay_after_send


class LightSettingsMixin:
    """Mixin providing shared to_service_data() for light settings."""

    brightness_pct: int
    rgb_color: list[int] | None
    color_temp_kelvin: int | None
    effect: str | None

    def to_service_data(
        self, include_transition: float | None = None
    ) -> dict[str, Any]:
        """Convert to service call data."""
        data: dict[str, Any] = {"brightness_pct": self.brightness_pct}

        if self.rgb_color is not None:
            data["rgb_color"] = self.rgb_color
        elif self.color_temp_kelvin is not None:
            data["color_temp_kelvin"] = self.color_temp_kelvin

        if self.effect is not None:
            data["effect"] = self.effect

        if include_transition is not None and include_transition > 0:
            data["transition"] = include_transition

        return data


@dataclass
class LightTarget(LightSettingsMixin):
    """Target settings for a single light."""

    entity_id: str
    brightness_pct: int = 100
    rgb_color: list[int] | None = None
    color_temp_kelvin: int | None = None
    effect: str | None = None
    state: str = "on"
    transition: float | None = None


@dataclass
class LightGroup(LightSettingsMixin):
    """A group of lights with identical settings for batched commands."""

    entities: list[str]
    brightness_pct: int
    rgb_color: list[int] | None = None
    color_temp_kelvin: int | None = None
    effect: str | None = None


@dataclass
class OperationResult:
    """Result of the ensure state operation."""

    success: bool
    result_code: str
    message: str
    attempts: int = 0
    total_lights: int = 0
    failed_lights: list[str] = field(default_factory=list)
    failed_light_details: dict[str, str] = field(default_factory=dict)
    skipped_lights: list[str] = field(default_factory=list)
    elapsed_seconds: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for service response."""
        result: dict[str, Any] = {
            RESULT_SUCCESS: self.success,
            RESULT_CODE: self.result_code,
            RESULT_MESSAGE: self.message,
            RESULT_ATTEMPTS: self.attempts,
            RESULT_TOTAL_LIGHTS: self.total_lights,
            RESULT_FAILED_LIGHTS: self.failed_lights,
            RESULT_SKIPPED_LIGHTS: self.skipped_lights,
            RESULT_ELAPSED_SECONDS: round(self.elapsed_seconds, 2),
        }
        if self.failed_light_details:
            result["failed_light_details"] = self.failed_light_details
        return result


# =============================================================================
# LIGHT CONTROLLER CLASS
# =============================================================================


class LightController:
    """Main controller class for ensuring light states."""

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the controller."""
        self.hass = hass

    # =========================================================================
    # Entity State Helpers
    # =========================================================================

    def _get_state(self, entity_id: str) -> State | None:
        """Get entity state object."""
        return self.hass.states.get(entity_id)

    def _is_available(self, entity_id: str) -> bool:
        """Check if entity is available."""
        state = self._get_state(entity_id)
        return state is not None and state.state not in [
            STATE_UNAVAILABLE,
            STATE_UNKNOWN,
        ]

    # =========================================================================
    # Entity Expansion
    # =========================================================================

    def _expand_entity(self, entity_id: object) -> tuple[list[str], list[str]]:
        """
        Expand a single entity into member lights.

        Returns: (valid_lights, skipped_lights)
        """
        valid: list[str] = []
        skipped: list[str] = []

        if not isinstance(entity_id, str):
            _LOGGER.warning("Invalid entity_id type: %s", type(entity_id).__name__)
            return valid, skipped

        state = self._get_state(entity_id)
        attrs = dict(state.attributes) if state else {}
        members = attrs.get("entity_id", [])

        # Case 1: Entity has member entities (light group or group.* helper)
        if isinstance(members, (list, tuple)) and members:
            _LOGGER.debug("Expanding group %s with %d members", entity_id, len(members))
            for member in members:
                if not isinstance(member, str):
                    continue
                if not member.startswith(f"{LIGHT_DOMAIN}."):
                    continue
                if self._is_available(member):
                    valid.append(member)
                else:
                    skipped.append(member)

        # Case 2: Individual light
        elif entity_id.startswith(f"{LIGHT_DOMAIN}."):
            if self._is_available(entity_id):
                valid.append(entity_id)
            else:
                skipped.append(entity_id)

        else:
            _LOGGER.warning("Entity %s is not a light or group", entity_id)

        return valid, skipped

    def _expand_entities(self, entities: list[str]) -> tuple[list[str], list[str]]:
        """
        Expand a list of entities into deduplicated light entity IDs.

        Returns: (members, skipped)
        """
        all_valid: list[str] = []
        all_skipped: list[str] = []

        for entity_id in entities:
            valid, skipped = self._expand_entity(entity_id)
            all_valid.extend(valid)
            all_skipped.extend(skipped)

        # Deduplicate while preserving order
        unique_valid = list(dict.fromkeys(all_valid))
        unique_skipped = list(dict.fromkeys(all_skipped))

        _LOGGER.debug(
            "Expanded to %d valid lights, %d skipped",
            len(unique_valid),
            len(unique_skipped),
        )

        return unique_valid, unique_skipped

    # =========================================================================
    # Target Building
    # =========================================================================

    def _build_targets(
        self,
        members: list[str],
        overrides: dict[str, dict[str, Any]],
        default_brightness_pct: int,
        default_rgb_color: list[int] | None,
        default_color_temp_kelvin: int | None,
        default_effect: str | None,
        default_state: str = "on",
        default_transition: float | None = None,
    ) -> list[LightTarget]:
        """Build LightTarget objects for each member."""
        targets: list[LightTarget] = []

        for entity_id in members:
            override = overrides.get(entity_id, {})

            target = LightTarget(
                entity_id=entity_id,
                brightness_pct=override.get("brightness_pct", default_brightness_pct),
                rgb_color=override.get("rgb_color", default_rgb_color),
                color_temp_kelvin=override.get(
                    "color_temp_kelvin",
                    override.get("color_temperature_kelvin", default_color_temp_kelvin),
                ),
                effect=override.get("effect", default_effect),
                state=override.get("state", default_state),
                transition=override.get("transition", default_transition),
            )
            targets.append(target)

        return targets

    # =========================================================================
    # Verification
    # =========================================================================

    def _verify_brightness(
        self, entity_id: str, expected_pct: int, tolerance: int
    ) -> bool:
        """Verify brightness is within tolerance."""
        state = self._get_state(entity_id)
        attrs = dict(state.attributes) if state else {}
        raw_brightness = attrs.get("brightness") or 0
        actual_pct = round((raw_brightness / 255) * 100)

        within_tolerance = (
            (expected_pct - tolerance) <= actual_pct <= (expected_pct + tolerance)
        )

        _LOGGER.debug(
            "%s brightness: expected=%d%%, actual=%d%%, tolerance=±%d%%, match=%s",
            entity_id,
            expected_pct,
            actual_pct,
            tolerance,
            within_tolerance,
        )

        return within_tolerance

    def _verify_rgb(
        self, entity_id: str, expected_rgb: list[int] | None, tolerance: int
    ) -> bool | None:
        """Verify RGB color is within tolerance."""
        if expected_rgb is None:
            return None

        state = self._get_state(entity_id)
        attrs = dict(state.attributes) if state else {}
        supported_modes = attrs.get("supported_color_modes", []) or []
        supports_rgb = (
            COLOR_MODE_RGB in supported_modes or COLOR_MODE_HS in supported_modes
        )

        if not supports_rgb:
            return None

        actual_rgb = attrs.get("rgb_color")
        if (
            not actual_rgb
            or not isinstance(actual_rgb, (list, tuple))
            or len(actual_rgb) != 3
        ):
            return False

        for i, (expected, actual) in enumerate(
            zip(expected_rgb, actual_rgb, strict=False)
        ):
            if not ((expected - tolerance) <= actual <= (expected + tolerance)):
                _LOGGER.debug(
                    "%s RGB channel %d: expected=%d, actual=%d, MISMATCH",
                    entity_id,
                    i,
                    expected,
                    actual,
                )
                return False

        return True

    def _verify_kelvin(
        self, entity_id: str, expected_kelvin: int | None, tolerance: int
    ) -> bool | None:
        """Verify color temperature is within tolerance."""
        if expected_kelvin is None:
            return None

        state = self._get_state(entity_id)
        attrs = dict(state.attributes) if state else {}
        supported_modes = attrs.get("supported_color_modes", []) or []

        if COLOR_MODE_COLOR_TEMP not in supported_modes:
            return None

        actual_kelvin = attrs.get("color_temp_kelvin") or attrs.get(
            "color_temperature_kelvin"
        )

        if not isinstance(actual_kelvin, (int, float)):
            return False

        actual_kelvin_int = int(actual_kelvin)
        within_tolerance = (
            (expected_kelvin - tolerance)
            <= actual_kelvin_int
            <= (expected_kelvin + tolerance)
        )

        return within_tolerance

    def _verify_light(
        self,
        target: LightTarget,
        target_state: TargetState,
        tolerances: ColorTolerance,
    ) -> VerificationResult:
        """Verify if a light has reached its target state."""
        entity_id = target.entity_id

        try:
            state = self._get_state(entity_id)
            current_state = state.state if state else None

            if current_state in [None, STATE_UNAVAILABLE, STATE_UNKNOWN]:
                return VerificationResult.UNAVAILABLE

            if target_state == TargetState.OFF:
                return (
                    VerificationResult.SUCCESS
                    if current_state == STATE_OFF
                    else VerificationResult.WRONG_STATE
                )

            # For ON state
            if current_state != STATE_ON:
                return VerificationResult.WRONG_STATE

            if not self._verify_brightness(
                entity_id, target.brightness_pct, tolerances.brightness
            ):
                return VerificationResult.WRONG_BRIGHTNESS

            # Verify color - success if either specified color matches or is unsupported
            has_rgb = target.rgb_color is not None
            has_kelvin = target.color_temp_kelvin is not None

            if not has_rgb and not has_kelvin:
                return VerificationResult.SUCCESS

            rgb_result = self._verify_rgb(entity_id, target.rgb_color, tolerances.rgb)
            kelvin_result = self._verify_kelvin(
                entity_id, target.color_temp_kelvin, tolerances.kelvin
            )

            # OK if matches (True) or unsupported (None); only False is a failure
            rgb_ok = rgb_result is not False if has_rgb else True
            kelvin_ok = kelvin_result is not False if has_kelvin else True

            # Every requested color mode must match
            if rgb_ok and kelvin_ok:
                return VerificationResult.SUCCESS
            return VerificationResult.WRONG_COLOR

        except Exception:
            _LOGGER.exception("Error verifying %s", entity_id)
            return VerificationResult.ERROR

    # =========================================================================
    # Command Execution
    # =========================================================================

    async def _send_turn_off(self, entity_ids: list[str]) -> None:
        """Send turn_off command."""
        _LOGGER.debug("Sending turn_off to %d lights", len(entity_ids))
        try:
            await self.hass.services.async_call(
                LIGHT_DOMAIN,
                "turn_off",
                {"entity_id": entity_ids},
                blocking=True,
            )
        except Exception:
            _LOGGER.exception("Error sending turn_off")

    async def _send_turn_on(
        self, group: LightGroup, transition: float | None = None
    ) -> None:
        """Send turn_on command to a light group."""
        _LOGGER.debug("Sending turn_on to %d lights", len(group.entities))
        try:
            service_data = group.to_service_data(include_transition=transition)
            service_data["entity_id"] = group.entities
            await self.hass.services.async_call(
                LIGHT_DOMAIN,
                "turn_on",
                service_data,
                blocking=True,
            )
        except Exception:
            _LOGGER.exception("Error sending turn_on")

    async def _send_commands_per_target(
        self,
        targets: list[LightTarget],
        global_transition: float | None = None,
        use_target_transitions: bool = True,
    ) -> None:
        """Send commands to targets, respecting per-entity state and transition.

        This method splits targets by state (on/off) and sends appropriate commands.
        Per-entity transition takes precedence over global_transition.
        """
        on_targets = [t for t in targets if t.state == "on"]
        off_targets = [t for t in targets if t.state == "off"]

        if off_targets:
            off_entities = [t.entity_id for t in off_targets]
            await self._send_turn_off(off_entities)

        if on_targets:
            groups = self._group_by_settings_with_transition(
                on_targets,
                global_transition,
                use_target_transitions=use_target_transitions,
            )
            tasks = [
                self._send_turn_on(group, transition) for group, transition, _ in groups
            ]
            await asyncio.gather(*tasks)

    def _group_by_settings_with_transition(
        self,
        targets: list[LightTarget],
        global_transition: float | None,
        use_target_transitions: bool = True,
    ) -> list[tuple[LightGroup, float | None, list[LightTarget]]]:
        """Group targets by settings, returning groups with transition and members."""
        groups: dict[
            GroupTransitionKey, tuple[LightGroup, float | None, list[LightTarget]]
        ] = {}

        for target in targets:
            transition = (
                target.transition
                if use_target_transitions and target.transition is not None
                else global_transition
            )

            rgb_key = tuple(target.rgb_color) if target.rgb_color else None
            key = (
                target.brightness_pct,
                rgb_key,
                target.color_temp_kelvin,
                target.effect,
                transition,
            )

            if key not in groups:
                group = LightGroup(
                    entities=[target.entity_id],
                    brightness_pct=target.brightness_pct,
                    rgb_color=target.rgb_color,
                    color_temp_kelvin=target.color_temp_kelvin,
                    effect=target.effect,
                )
                groups[key] = (group, transition, [target])
            else:
                groups[key][0].entities.append(target.entity_id)
                groups[key][2].append(target)

        return list(groups.values())

    def _build_dispatch_batches(
        self,
        targets: list[LightTarget],
        global_transition: float | None = None,
        use_target_transitions: bool = True,
    ) -> list[list[LightTarget]]:
        """Build command batches matching the current dispatch strategy."""
        batches: list[list[LightTarget]] = []
        off_targets = [t for t in targets if t.state == "off"]
        on_targets = [t for t in targets if t.state == "on"]

        if off_targets:
            # OFF targets are always sent as a single batched turn_off call.
            batches.append(off_targets)

        if on_targets:
            grouped_on = self._group_by_settings_with_transition(
                on_targets,
                global_transition,
                use_target_transitions=use_target_transitions,
            )
            for _, _, group_targets in grouped_on:
                batches.append(group_targets)

        return batches

    # =========================================================================
    # Logging and Notifications
    # =========================================================================

    async def _log_to_logbook(self, name: str, message: str) -> None:
        """Write to Home Assistant logbook."""
        try:
            await self.hass.services.async_call(
                "logbook",
                "log",
                {"name": name, "message": message},
                blocking=False,
            )
        except Exception:
            _LOGGER.exception("Error writing to logbook")

    # =========================================================================
    # Main Entry Point
    # =========================================================================

    async def ensure_state(  # noqa: C901
        self,
        entities: list[str],
        state_target: str = "on",
        default_brightness_pct: int = 100,
        default_rgb_color: list[int] | None = None,
        default_color_temp_kelvin: int | None = None,
        default_effect: str | None = None,
        targets: list[dict[str, Any]] | None = None,
        brightness_tolerance: int = 3,
        rgb_tolerance: int = 10,
        kelvin_tolerance: int = 150,
        transition: float = 0,
        delay_after_send: float = 2,
        max_retries: int = 3,
        max_runtime_seconds: float = 60,
        use_exponential_backoff: bool = False,
        max_backoff_seconds: float = 30,
        skip_verification: bool = False,
        log_success: bool = False,
    ) -> dict[str, Any]:
        """
        Ensure lights reach target state with verification and retries.

        This is the main entry point for the controller.
        """
        script_start = monotonic()

        _LOGGER.info(
            "Starting ensure_state with %d entities", len(entities) if entities else 0
        )

        # Input validation
        if (
            not entities
            or not isinstance(entities, (list, tuple))
            or len(entities) == 0
        ):
            message = "No entities provided"
            _LOGGER.warning(message)
            await self._log_to_logbook("Light Controller", f"{message}; exiting.")
            return OperationResult(
                success=False, result_code=RESULT_CODE_ERROR, message=message
            ).to_dict()

        try:
            target_state = TargetState.from_string(state_target)
        except ValueError as e:
            message = str(e)
            _LOGGER.error(message)
            return OperationResult(
                success=False, result_code=RESULT_CODE_ERROR, message=message
            ).to_dict()

        tolerances = ColorTolerance(
            brightness=brightness_tolerance,
            rgb=rgb_tolerance,
            kelvin=kelvin_tolerance,
        )

        retry_config = RetryConfig(
            max_retries=max_retries,
            delay_after_send=float(delay_after_send),
            max_runtime_seconds=float(max_runtime_seconds),
            use_exponential_backoff=use_exponential_backoff,
            max_backoff_seconds=float(max_backoff_seconds),
        )

        # Expand entities
        members, skipped_entities = self._expand_entities(list(entities))

        if len(members) == 0:
            message = "No valid light entities found"
            if skipped_entities:
                message += f". Skipped: {', '.join(skipped_entities)}"
            _LOGGER.warning(message)
            await self._log_to_logbook("Light Controller", message)
            return OperationResult(
                success=False,
                result_code=RESULT_CODE_NO_VALID_ENTITIES,
                message=message,
                skipped_lights=skipped_entities,
            ).to_dict()

        if skipped_entities:
            _LOGGER.info(
                "Skipped %d unavailable entities: %s",
                len(skipped_entities),
                ", ".join(skipped_entities),
            )

        # Build overrides dict, expanding group entities to their members
        overrides: dict[str, dict[str, Any]] = {}
        if targets:
            for t in targets:
                if not isinstance(t, dict) or "entity_id" not in t:
                    continue
                eid = t["entity_id"]
                if eid in members:
                    overrides[eid] = t
                else:
                    # Entity may be a group that was expanded; remap to members
                    group_members, _ = self._expand_entity(eid)
                    for gm in group_members:
                        if gm in members and gm not in overrides:
                            overrides[gm] = {**t, "entity_id": gm}

        # Build targets
        pending_targets = self._build_targets(
            members,
            overrides,
            default_brightness_pct,
            default_rgb_color,
            default_color_temp_kelvin,
            default_effect,
            default_state=state_target,
            default_transition=None,
        )

        # Fire-and-forget mode
        if skip_verification:
            _LOGGER.info("Fire-and-forget mode")
            await self._send_commands_per_target(
                pending_targets,
                global_transition=transition if transition > 0 else None,
                use_target_transitions=True,
            )

            elapsed = monotonic() - script_start

            if log_success:
                await self._log_to_logbook(
                    "Light Controller",
                    f"Fire-and-forget: Sent {target_state.value} to {len(members)} lights",
                )

            return OperationResult(
                success=True,
                result_code=RESULT_CODE_SUCCESS,
                message=f"Fire-and-forget: sent {target_state.value} to {len(members)} lights",
                total_lights=len(members),
                skipped_lights=skipped_entities,
                elapsed_seconds=elapsed,
            ).to_dict()

        # Main retry loop
        attempt = 0
        verification_results: dict[str, VerificationResult] = {}

        while pending_targets and attempt < retry_config.max_retries:
            elapsed = monotonic() - script_start
            if elapsed >= retry_config.max_runtime_seconds:
                _LOGGER.warning("Timeout reached after %.1fs", elapsed)
                break

            current_delay = retry_config.calculate_delay(attempt)

            _LOGGER.info(
                "Attempt %d/%d: %d lights pending",
                attempt + 1,
                retry_config.max_retries,
                len(pending_targets),
            )

            # Transition only on first attempt - retries should be instant for quick recovery
            use_transition = None
            use_target_transitions = attempt == 0
            if target_state == TargetState.ON and attempt == 0 and transition > 0:
                use_transition = transition

            await self._send_commands_per_target(
                pending_targets,
                global_transition=use_transition,
                use_target_transitions=use_target_transitions,
            )

            await asyncio.sleep(current_delay)

            # Verify and filter at dispatch-batch granularity.
            # If any target in a batch fails verification, the full batch is retried.
            dispatch_batches = self._build_dispatch_batches(
                pending_targets,
                global_transition=use_transition,
                use_target_transitions=use_target_transitions,
            )
            verification_results.clear()
            for target in pending_targets:
                verification_results[target.entity_id] = self._verify_light(
                    target,
                    TargetState.from_string(target.state),
                    tolerances,
                )

            still_pending: list[LightTarget] = []
            for batch in dispatch_batches:
                if any(
                    verification_results[t.entity_id]
                    not in [VerificationResult.SUCCESS, VerificationResult.UNAVAILABLE]
                    for t in batch
                ):
                    # Don't retry entities that are unavailable.
                    still_pending.extend(
                        [
                            t
                            for t in batch
                            if verification_results[t.entity_id]
                            != VerificationResult.UNAVAILABLE
                        ]
                    )

            resolved_count = sum(
                1
                for result in verification_results.values()
                if result
                in [VerificationResult.SUCCESS, VerificationResult.UNAVAILABLE]
            )

            _LOGGER.debug(
                "Verification: %d resolved, %d pending",
                resolved_count,
                len(still_pending),
            )

            pending_targets = still_pending
            attempt += 1

        # Handle results
        elapsed = monotonic() - script_start
        failed_entities = [t.entity_id for t in pending_targets]
        failed_details = {
            eid: verification_results[eid].value
            for eid in failed_entities
            if eid in verification_results
        }

        # Timeout
        if elapsed >= retry_config.max_runtime_seconds and pending_targets:
            message = (
                f"Timeout after {retry_config.max_runtime_seconds}s. "
                f"Failed: {', '.join(failed_entities)}"
            )
            _LOGGER.error(message)
            await self._log_to_logbook("Light Controller", message)

            return OperationResult(
                success=False,
                result_code=RESULT_CODE_TIMEOUT,
                message=message,
                attempts=attempt,
                total_lights=len(members),
                failed_lights=failed_entities,
                failed_light_details=failed_details,
                skipped_lights=skipped_entities,
                elapsed_seconds=elapsed,
            ).to_dict()

        # Failure after retries
        if pending_targets:
            message = f"Failed after {attempt} attempts. Remaining: {', '.join(failed_entities)}"
            _LOGGER.error(message)
            await self._log_to_logbook("Light Controller", message)

            return OperationResult(
                success=False,
                result_code=RESULT_CODE_FAILED,
                message=message,
                attempts=attempt,
                total_lights=len(members),
                failed_lights=failed_entities,
                failed_light_details=failed_details,
                skipped_lights=skipped_entities,
                elapsed_seconds=elapsed,
            ).to_dict()

        # Success
        message = (
            f"Set {len(members)} lights to {target_state.value} in {attempt} attempts"
        )
        if skipped_entities:
            message += f". Skipped {len(skipped_entities)} unavailable."

        _LOGGER.info(message)

        if log_success:
            await self._log_to_logbook("Light Controller", message)

        return OperationResult(
            success=True,
            result_code=RESULT_CODE_SUCCESS,
            message=message,
            attempts=attempt,
            total_lights=len(members),
            skipped_lights=skipped_entities,
            elapsed_seconds=elapsed,
        ).to_dict()
