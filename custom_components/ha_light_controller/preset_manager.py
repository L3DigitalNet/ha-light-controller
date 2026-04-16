"""Preset manager for Light Controller integration."""

from __future__ import annotations

import logging
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er

if TYPE_CHECKING:
    from .controller import LightController

from .const import (
    CONF_BRIGHTNESS_TOLERANCE,
    CONF_DELAY_AFTER_SEND,
    CONF_KELVIN_TOLERANCE,
    CONF_LOG_SUCCESS,
    CONF_MAX_BACKOFF_SECONDS,
    CONF_MAX_RETRIES,
    CONF_MAX_RUNTIME_SECONDS,
    CONF_PRESETS,
    CONF_RGB_TOLERANCE,
    CONF_USE_EXPONENTIAL_BACKOFF,
    DEFAULT_BRIGHTNESS_TOLERANCE,
    DEFAULT_DELAY_AFTER_SEND,
    DEFAULT_KELVIN_TOLERANCE,
    DEFAULT_LOG_SUCCESS,
    DEFAULT_MAX_BACKOFF_SECONDS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_RUNTIME_SECONDS,
    DEFAULT_RGB_TOLERANCE,
    DEFAULT_USE_EXPONENTIAL_BACKOFF,
    PRESET_BRIGHTNESS_PCT,
    PRESET_COLOR_TEMP_KELVIN,
    PRESET_EFFECT,
    PRESET_ENTITIES,
    PRESET_ID,
    PRESET_NAME,
    PRESET_RGB_COLOR,
    PRESET_SKIP_VERIFICATION,
    PRESET_STATE,
    PRESET_STATUS_FAILED,
    PRESET_STATUS_IDLE,
    PRESET_STATUS_SUCCESS,
    PRESET_TARGETS,
    PRESET_TRANSITION,
)

_LOGGER = logging.getLogger(__name__)

type PresetListener = Callable[[], None]


@dataclass
class PresetConfig:
    """Configuration for a single preset."""

    id: str
    name: str
    entities: list[str]
    state: str = "on"
    brightness_pct: int = 100
    rgb_color: list[int] | None = None
    color_temp_kelvin: int | None = None
    effect: str | None = None
    targets: list[dict[str, Any]] = field(default_factory=list)
    transition: float = 0.0
    skip_verification: bool = False

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PresetConfig:
        """Create a PresetConfig from a dictionary."""
        return cls(
            id=data.get(PRESET_ID, str(uuid.uuid4())),
            name=data.get(PRESET_NAME, "Unnamed Preset"),
            entities=data.get(PRESET_ENTITIES, []),
            state=data.get(PRESET_STATE, "on"),
            brightness_pct=data.get(PRESET_BRIGHTNESS_PCT, 100),
            rgb_color=data.get(PRESET_RGB_COLOR),
            color_temp_kelvin=data.get(PRESET_COLOR_TEMP_KELVIN),
            effect=data.get(PRESET_EFFECT),
            targets=data.get(PRESET_TARGETS, []),
            transition=data.get(PRESET_TRANSITION, 0.0),
            skip_verification=data.get(PRESET_SKIP_VERIFICATION, False),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            PRESET_ID: self.id,
            PRESET_NAME: self.name,
            PRESET_ENTITIES: self.entities,
            PRESET_STATE: self.state,
            PRESET_BRIGHTNESS_PCT: self.brightness_pct,
            PRESET_RGB_COLOR: self.rgb_color,
            PRESET_COLOR_TEMP_KELVIN: self.color_temp_kelvin,
            PRESET_EFFECT: self.effect,
            PRESET_TARGETS: self.targets,
            PRESET_TRANSITION: self.transition,
            PRESET_SKIP_VERIFICATION: self.skip_verification,
        }


@dataclass
class PresetStatus:
    """Runtime status of a preset."""

    status: str = PRESET_STATUS_IDLE
    last_result: dict[str, Any] | None = None
    last_activated: str | None = None


class PresetManager:
    """Manages preset storage and operations."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the preset manager."""
        self.hass = hass
        self.entry = entry
        self._presets: dict[str, PresetConfig] = {}
        self._status: dict[str, PresetStatus] = {}
        self._listeners: list[PresetListener] = []

        # Load presets from config entry
        self._load_presets()

    def _load_presets(self) -> None:
        """Load presets from config entry data."""
        presets_data = self.entry.data.get(CONF_PRESETS, {})

        for preset_id, preset_data in presets_data.items():
            try:
                preset = PresetConfig.from_dict(preset_data)
                self._presets[preset_id] = preset
                self._status[preset_id] = PresetStatus()
                _LOGGER.debug("Loaded preset: %s (%s)", preset.name, preset_id)
            except Exception as e:
                _LOGGER.error("Error loading preset %s: %s", preset_id, e)

        _LOGGER.info("Loaded %d presets", len(self._presets))

    async def _save_presets(self) -> None:
        """Save presets to config entry data."""
        presets_data = {
            preset_id: preset.to_dict() for preset_id, preset in self._presets.items()
        }

        # Update config entry data
        new_data = {**self.entry.data, CONF_PRESETS: presets_data}
        self.hass.config_entries.async_update_entry(self.entry, data=new_data)

        _LOGGER.debug("Saved %d presets", len(presets_data))

        # Notify listeners
        await self._notify_listeners()

    async def _notify_listeners(self) -> None:
        """Notify all registered listeners of preset changes."""
        # Create a snapshot to avoid issues if listeners modify the list during iteration
        listeners_snapshot = list(self._listeners)
        for listener in listeners_snapshot:
            try:
                listener()
            except Exception as e:
                _LOGGER.error("Error notifying listener: %s", e)

    @callback
    def register_listener(self, listener: PresetListener) -> Callable[[], None]:
        """Register a listener for preset changes. Returns unsubscribe function."""
        self._listeners.append(listener)

        def unsubscribe() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return unsubscribe

    @property
    def presets(self) -> dict[str, PresetConfig]:
        """Get all presets."""
        return self._presets.copy()

    def get_preset(self, preset_id: str) -> PresetConfig | None:
        """Get a preset by ID."""
        return self._presets.get(preset_id)

    def get_preset_by_name(self, name: str) -> PresetConfig | None:
        """Get a preset by name (case-insensitive)."""
        name_lower = name.lower()
        for preset in self._presets.values():
            if preset.name.lower() == name_lower:
                return preset
        return None

    def find_preset(self, name_or_id: str) -> PresetConfig | None:
        """Find preset by ID or name."""
        return self.get_preset(name_or_id) or self.get_preset_by_name(name_or_id)

    def get_status(self, preset_id: str) -> PresetStatus:
        """Get the status of a preset."""
        return self._status.get(preset_id, PresetStatus())

    async def set_status(
        self,
        preset_id: str,
        status: str,
        result: dict[str, Any] | None = None,
    ) -> None:
        """Update the status of a preset."""
        if preset_id not in self._status:
            self._status[preset_id] = PresetStatus()

        self._status[preset_id].status = status
        if result is not None:
            self._status[preset_id].last_result = result

        if status in [PRESET_STATUS_SUCCESS, PRESET_STATUS_FAILED]:
            self._status[preset_id].last_activated = datetime.now(tz=UTC).isoformat()

        # Trigger entity updates
        await self._notify_listeners()

    def _is_name_taken(self, name: str, exclude_id: str | None = None) -> bool:
        """Check if a preset name is already in use (case-insensitive)."""
        name_lower = name.lower()
        for pid, preset in self._presets.items():
            if pid != exclude_id and preset.name.lower() == name_lower:
                return True
        return False

    async def create_preset(
        self,
        name: str,
        entities: list[str],
        state: str = "on",
        brightness_pct: int = 100,
        rgb_color: list[int] | None = None,
        color_temp_kelvin: int | None = None,
        effect: str | None = None,
        targets: list[dict[str, Any]] | None = None,
        transition: float = 0.0,
        skip_verification: bool = False,
    ) -> PresetConfig:
        """Create a new preset. Raises ValueError if name is already taken."""
        if self._is_name_taken(name):
            raise ValueError(f"A preset named '{name}' already exists")

        preset_id = str(uuid.uuid4())

        preset = PresetConfig(
            id=preset_id,
            name=name,
            entities=entities,
            state=state,
            brightness_pct=brightness_pct,
            rgb_color=rgb_color,
            color_temp_kelvin=color_temp_kelvin,
            effect=effect,
            targets=targets or [],
            transition=transition,
            skip_verification=skip_verification,
        )

        self._presets[preset_id] = preset
        self._status[preset_id] = PresetStatus()

        await self._save_presets()

        _LOGGER.info("Created preset: %s (%s)", name, preset_id)
        return preset

    async def update_preset(
        self,
        preset_id: str,
        name: str,
        entities: list[str],
        state: str = "on",
        brightness_pct: int = 100,
        rgb_color: list[int] | None = None,
        color_temp_kelvin: int | None = None,
        effect: str | None = None,
        targets: list[dict[str, Any]] | None = None,
        transition: float = 0.0,
        skip_verification: bool = False,
    ) -> PresetConfig | None:
        """Update an existing preset in-place, preserving its ID.

        Raises ValueError if name collides with another preset (not itself).
        """
        if preset_id not in self._presets:
            _LOGGER.warning("Preset not found for update: %s", preset_id)
            return None

        if self._is_name_taken(name, exclude_id=preset_id):
            raise ValueError(f"A preset named '{name}' already exists")

        preset = PresetConfig(
            id=preset_id,
            name=name,
            entities=entities,
            state=state,
            brightness_pct=brightness_pct,
            rgb_color=rgb_color,
            color_temp_kelvin=color_temp_kelvin,
            effect=effect,
            targets=targets or [],
            transition=transition,
            skip_verification=skip_verification,
        )

        self._presets[preset_id] = preset
        await self._save_presets()

        _LOGGER.info("Updated preset: %s (%s)", name, preset_id)
        return preset

    async def delete_preset(self, preset_id: str) -> bool:
        """Delete a preset and its associated entities."""
        if preset_id not in self._presets:
            _LOGGER.warning("Preset not found: %s", preset_id)
            return False

        preset = self._presets.pop(preset_id)
        self._status.pop(preset_id, None)

        await self._save_presets()

        # Remove entity registry entries. The config entry reload (triggered by
        # _save_presets → async_update_entry) unsubscribes entity listeners before
        # _notify_listeners fires, so entity self-removal via _handle_preset_update
        # cannot run. Manual registry cleanup is required here.
        try:
            ent_reg = er.async_get(self.hass)
            entry_id = self.entry.entry_id

            for suffix in ("_button", "_status"):
                unique_id = f"{entry_id}_preset_{preset_id}{suffix}"
                domain = "button" if suffix == "_button" else "sensor"
                entity_id = ent_reg.async_get_entity_id(
                    domain, "ha_light_controller", unique_id
                )
                if entity_id:
                    ent_reg.async_remove(entity_id)
                    _LOGGER.debug("Removed %s entity: %s", domain, entity_id)
        except Exception as e:
            _LOGGER.warning("Error removing entities for preset %s: %s", preset_id, e)

        _LOGGER.info("Deleted preset: %s (%s)", preset.name, preset_id)
        return True

    async def create_preset_from_current(
        self, name: str, entities: list[str]
    ) -> PresetConfig | None:
        """Create a preset from the current state of entities."""
        if not entities:
            _LOGGER.warning("No entities provided for preset creation")
            return None

        targets: list[dict[str, Any]] = []

        for entity_id in entities:
            state = self.hass.states.get(entity_id)
            if not state:
                continue

            is_on = state.state == "on"
            target: dict[str, Any] = {
                "entity_id": entity_id,
                "state": "on" if is_on else "off",
            }

            if is_on:
                attrs = state.attributes

                # Brightness
                if "brightness" in attrs:
                    brightness = attrs["brightness"]
                    target["brightness_pct"] = round((brightness / 255) * 100)

                # RGB color
                if "rgb_color" in attrs:
                    target["rgb_color"] = list(attrs["rgb_color"])

                # Color temperature
                if "color_temp_kelvin" in attrs:
                    target["color_temp_kelvin"] = attrs["color_temp_kelvin"]
                elif "color_temperature_kelvin" in attrs:
                    target["color_temp_kelvin"] = attrs["color_temperature_kelvin"]

                # Effect
                if "effect" in attrs and attrs["effect"] not in [None, "none", "None"]:
                    target["effect"] = attrs["effect"]

            targets.append(target)

        # Determine overall state
        states = [self.hass.states.get(e) for e in entities]
        any_on = any(s and s.state == "on" for s in states)

        # Create preset
        preset = await self.create_preset(
            name=name,
            entities=entities,
            state="on" if any_on else "off",
            targets=targets,
        )

        _LOGGER.info(
            "Created preset from current state: %s with %d entities",
            name,
            len(entities),
        )

        return preset

    async def activate_preset_with_options(
        self,
        preset: PresetConfig,
        controller: LightController,
        options: Mapping[str, Any],
    ) -> dict[str, Any]:
        """Activate a preset using configured options.

        Args:
            preset: The preset to activate
            controller: LightController instance
            options: ConfigEntry options dict for tolerance/retry defaults

        Returns:
            Result dict from controller.ensure_state()
        """
        return await controller.ensure_state(
            entities=preset.entities,
            state_target=preset.state,
            default_brightness_pct=preset.brightness_pct,
            default_rgb_color=preset.rgb_color,
            default_color_temp_kelvin=preset.color_temp_kelvin,
            default_effect=preset.effect,
            targets=preset.targets if preset.targets else None,
            transition=preset.transition,
            skip_verification=preset.skip_verification,
            brightness_tolerance=options.get(
                CONF_BRIGHTNESS_TOLERANCE, DEFAULT_BRIGHTNESS_TOLERANCE
            ),
            rgb_tolerance=options.get(CONF_RGB_TOLERANCE, DEFAULT_RGB_TOLERANCE),
            kelvin_tolerance=options.get(
                CONF_KELVIN_TOLERANCE, DEFAULT_KELVIN_TOLERANCE
            ),
            delay_after_send=options.get(
                CONF_DELAY_AFTER_SEND, DEFAULT_DELAY_AFTER_SEND
            ),
            max_retries=options.get(CONF_MAX_RETRIES, DEFAULT_MAX_RETRIES),
            max_runtime_seconds=options.get(
                CONF_MAX_RUNTIME_SECONDS, DEFAULT_MAX_RUNTIME_SECONDS
            ),
            use_exponential_backoff=options.get(
                CONF_USE_EXPONENTIAL_BACKOFF, DEFAULT_USE_EXPONENTIAL_BACKOFF
            ),
            max_backoff_seconds=options.get(
                CONF_MAX_BACKOFF_SECONDS, DEFAULT_MAX_BACKOFF_SECONDS
            ),
            log_success=options.get(CONF_LOG_SUCCESS, DEFAULT_LOG_SUCCESS),
        )
