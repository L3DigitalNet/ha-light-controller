"""Config flow for Light Controller integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.core import callback
from homeassistant.data_entry_flow import section
from homeassistant.helpers import selector

from .const import (
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
    DEFAULT_BRIGHTNESS_TOLERANCE,
    DEFAULT_DELAY_AFTER_SEND,
    DEFAULT_KELVIN_TOLERANCE,
    DEFAULT_LOG_SUCCESS,
    DEFAULT_MAX_BACKOFF_SECONDS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_RUNTIME_SECONDS,
    DEFAULT_RGB_TOLERANCE,
    DEFAULT_TRANSITION,
    DEFAULT_USE_EXPONENTIAL_BACKOFF,
    DOMAIN,
    PRESET_BRIGHTNESS_PCT,
    PRESET_COLOR_MODE,
    PRESET_COLOR_TEMP_KELVIN,
    PRESET_EFFECT,
    PRESET_ENTITIES,
    PRESET_NAME,
    PRESET_RGB_COLOR,
    PRESET_SKIP_VERIFICATION,
    PRESET_STATE,
    PRESET_TRANSITION,
)

_LOGGER = logging.getLogger(__name__)


class LightControllerConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Light Controller."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Check if already configured
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title="Light Controller",
                data={},
                options={
                    CONF_DEFAULT_BRIGHTNESS_PCT: user_input.get(
                        CONF_DEFAULT_BRIGHTNESS_PCT, DEFAULT_BRIGHTNESS_PCT
                    ),
                    CONF_DEFAULT_TRANSITION: user_input.get(
                        CONF_DEFAULT_TRANSITION, DEFAULT_TRANSITION
                    ),
                    CONF_BRIGHTNESS_TOLERANCE: user_input.get(
                        CONF_BRIGHTNESS_TOLERANCE, DEFAULT_BRIGHTNESS_TOLERANCE
                    ),
                    CONF_RGB_TOLERANCE: user_input.get(
                        CONF_RGB_TOLERANCE, DEFAULT_RGB_TOLERANCE
                    ),
                    CONF_KELVIN_TOLERANCE: user_input.get(
                        CONF_KELVIN_TOLERANCE, DEFAULT_KELVIN_TOLERANCE
                    ),
                    CONF_DELAY_AFTER_SEND: user_input.get(
                        CONF_DELAY_AFTER_SEND, DEFAULT_DELAY_AFTER_SEND
                    ),
                    CONF_MAX_RETRIES: user_input.get(
                        CONF_MAX_RETRIES, DEFAULT_MAX_RETRIES
                    ),
                    CONF_MAX_RUNTIME_SECONDS: user_input.get(
                        CONF_MAX_RUNTIME_SECONDS, DEFAULT_MAX_RUNTIME_SECONDS
                    ),
                    CONF_USE_EXPONENTIAL_BACKOFF: user_input.get(
                        CONF_USE_EXPONENTIAL_BACKOFF, DEFAULT_USE_EXPONENTIAL_BACKOFF
                    ),
                    CONF_MAX_BACKOFF_SECONDS: user_input.get(
                        CONF_MAX_BACKOFF_SECONDS, DEFAULT_MAX_BACKOFF_SECONDS
                    ),
                    CONF_LOG_SUCCESS: user_input.get(
                        CONF_LOG_SUCCESS, DEFAULT_LOG_SUCCESS
                    ),
                },
            )

        # Show the setup form
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_DEFAULT_BRIGHTNESS_PCT,
                        default=DEFAULT_BRIGHTNESS_PCT,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=100,
                            step=1,
                            unit_of_measurement="%",
                            mode=selector.NumberSelectorMode.SLIDER,
                        )
                    ),
                    vol.Optional(
                        CONF_DEFAULT_TRANSITION,
                        default=DEFAULT_TRANSITION,
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=60,
                            step=0.5,
                            unit_of_measurement="s",
                            mode=selector.NumberSelectorMode.SLIDER,
                        )
                    ),
                }
            ),
            errors=errors,
            description_placeholders={},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return LightControllerOptionsFlow()


class LightControllerOptionsFlow(OptionsFlow):
    """Handle options flow for Light Controller."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options - show menu."""
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "settings",
                "add_preset",
                "manage_presets",
            ],
        )

    async def async_step_settings(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle all configuration settings with collapsible sections."""
        if user_input is not None:
            # Flatten nested section data into a single dict
            flat_options = {}
            for key, value in user_input.items():
                if isinstance(value, dict):
                    # This is a section - merge its contents
                    flat_options.update(value)
                else:
                    flat_options[key] = value

            new_options = {**self.config_entry.options, **flat_options}
            return self.async_create_entry(title="", data=new_options)

        options = self.config_entry.options

        return self.async_show_form(
            step_id="settings",
            data_schema=vol.Schema(
                {
                    # Defaults section - expanded by default (most common settings)
                    vol.Required("defaults"): section(
                        vol.Schema(
                            {
                                vol.Optional(
                                    CONF_DEFAULT_BRIGHTNESS_PCT,
                                    default=options.get(
                                        CONF_DEFAULT_BRIGHTNESS_PCT,
                                        DEFAULT_BRIGHTNESS_PCT,
                                    ),
                                ): selector.NumberSelector(
                                    selector.NumberSelectorConfig(
                                        min=1,
                                        max=100,
                                        step=1,
                                        unit_of_measurement="%",
                                        mode=selector.NumberSelectorMode.SLIDER,
                                    )
                                ),
                                vol.Optional(
                                    CONF_DEFAULT_TRANSITION,
                                    default=options.get(
                                        CONF_DEFAULT_TRANSITION, DEFAULT_TRANSITION
                                    ),
                                ): selector.NumberSelector(
                                    selector.NumberSelectorConfig(
                                        min=0,
                                        max=60,
                                        step=0.5,
                                        unit_of_measurement="s",
                                        mode=selector.NumberSelectorMode.SLIDER,
                                    )
                                ),
                            }
                        ),
                        {"collapsed": False},
                    ),
                    # Tolerances section - collapsed (advanced)
                    vol.Required("tolerances"): section(
                        vol.Schema(
                            {
                                vol.Optional(
                                    CONF_BRIGHTNESS_TOLERANCE,
                                    default=options.get(
                                        CONF_BRIGHTNESS_TOLERANCE,
                                        DEFAULT_BRIGHTNESS_TOLERANCE,
                                    ),
                                ): selector.NumberSelector(
                                    selector.NumberSelectorConfig(
                                        min=0,
                                        max=20,
                                        step=1,
                                        unit_of_measurement="%",
                                        mode=selector.NumberSelectorMode.SLIDER,
                                    )
                                ),
                                vol.Optional(
                                    CONF_RGB_TOLERANCE,
                                    default=options.get(
                                        CONF_RGB_TOLERANCE, DEFAULT_RGB_TOLERANCE
                                    ),
                                ): selector.NumberSelector(
                                    selector.NumberSelectorConfig(
                                        min=0,
                                        max=50,
                                        step=1,
                                        mode=selector.NumberSelectorMode.SLIDER,
                                    )
                                ),
                                vol.Optional(
                                    CONF_KELVIN_TOLERANCE,
                                    default=options.get(
                                        CONF_KELVIN_TOLERANCE, DEFAULT_KELVIN_TOLERANCE
                                    ),
                                ): selector.NumberSelector(
                                    selector.NumberSelectorConfig(
                                        min=0,
                                        max=500,
                                        step=10,
                                        unit_of_measurement="K",
                                        mode=selector.NumberSelectorMode.SLIDER,
                                    )
                                ),
                            }
                        ),
                        {"collapsed": True},
                    ),
                    # Retry settings section - collapsed (advanced)
                    vol.Required("retry_settings"): section(
                        vol.Schema(
                            {
                                vol.Optional(
                                    CONF_DELAY_AFTER_SEND,
                                    default=options.get(
                                        CONF_DELAY_AFTER_SEND, DEFAULT_DELAY_AFTER_SEND
                                    ),
                                ): selector.NumberSelector(
                                    selector.NumberSelectorConfig(
                                        min=0.5,
                                        max=30,
                                        step=0.5,
                                        unit_of_measurement="s",
                                        mode=selector.NumberSelectorMode.SLIDER,
                                    )
                                ),
                                vol.Optional(
                                    CONF_MAX_RETRIES,
                                    default=options.get(
                                        CONF_MAX_RETRIES, DEFAULT_MAX_RETRIES
                                    ),
                                ): selector.NumberSelector(
                                    selector.NumberSelectorConfig(
                                        min=1,
                                        max=10,
                                        step=1,
                                        mode=selector.NumberSelectorMode.SLIDER,
                                    )
                                ),
                                vol.Optional(
                                    CONF_MAX_RUNTIME_SECONDS,
                                    default=options.get(
                                        CONF_MAX_RUNTIME_SECONDS,
                                        DEFAULT_MAX_RUNTIME_SECONDS,
                                    ),
                                ): selector.NumberSelector(
                                    selector.NumberSelectorConfig(
                                        min=10,
                                        max=300,
                                        step=10,
                                        unit_of_measurement="s",
                                        mode=selector.NumberSelectorMode.SLIDER,
                                    )
                                ),
                                vol.Optional(
                                    CONF_USE_EXPONENTIAL_BACKOFF,
                                    default=options.get(
                                        CONF_USE_EXPONENTIAL_BACKOFF,
                                        DEFAULT_USE_EXPONENTIAL_BACKOFF,
                                    ),
                                ): selector.BooleanSelector(),
                                vol.Optional(
                                    CONF_MAX_BACKOFF_SECONDS,
                                    default=options.get(
                                        CONF_MAX_BACKOFF_SECONDS,
                                        DEFAULT_MAX_BACKOFF_SECONDS,
                                    ),
                                ): selector.NumberSelector(
                                    selector.NumberSelectorConfig(
                                        min=5,
                                        max=120,
                                        step=5,
                                        unit_of_measurement="s",
                                        mode=selector.NumberSelectorMode.SLIDER,
                                    )
                                ),
                            }
                        ),
                        {"collapsed": True},
                    ),
                    # Notifications section - collapsed (advanced)
                    vol.Required("notifications"): section(
                        vol.Schema(
                            {
                                vol.Optional(
                                    CONF_LOG_SUCCESS,
                                    default=options.get(
                                        CONF_LOG_SUCCESS, DEFAULT_LOG_SUCCESS
                                    ),
                                ): selector.BooleanSelector(),
                            }
                        ),
                        {"collapsed": True},
                    ),
                }
            ),
        )

    async def async_step_add_preset(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle adding a new preset - step 1: basic settings and initial entities."""
        errors: dict[str, str] = {}

        if user_input is not None:
            # Validate input
            name = user_input.get(PRESET_NAME, "").strip()
            entities = user_input.get(PRESET_ENTITIES, [])

            if not name:
                errors["base"] = "name_required"
            elif not entities:
                errors["base"] = "entities_required"
            else:
                # Store data for the hub - initialize per-entity configuration as dict
                self._preset_data = {
                    PRESET_NAME: name,
                    PRESET_ENTITIES: list(entities),
                    PRESET_SKIP_VERIFICATION: user_input.get(
                        PRESET_SKIP_VERIFICATION, False
                    ),
                    "targets": {},  # Dict keyed by entity_id for easy lookup/update
                }

                # Go to entity management hub
                return await self.async_step_preset_entity_menu()

        return self.async_show_form(
            step_id="add_preset",
            data_schema=vol.Schema(
                {
                    vol.Required(PRESET_NAME): selector.TextSelector(
                        selector.TextSelectorConfig(type=selector.TextSelectorType.TEXT)
                    ),
                    vol.Required(PRESET_ENTITIES): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["light", "group"],
                            multiple=True,
                        )
                    ),
                    vol.Optional(
                        PRESET_SKIP_VERIFICATION, default=False
                    ): selector.BooleanSelector(),
                }
            ),
            errors=errors,
        )

    def _get_entity_friendly_name(self, entity_id: str) -> str:
        """Get friendly name for an entity."""
        entity_state = self.hass.states.get(entity_id)
        if entity_state:
            friendly_name = entity_state.attributes.get("friendly_name")
            if isinstance(friendly_name, str) and friendly_name:
                return friendly_name
        return entity_id

    def _build_entity_status_summary(self) -> str:
        """Build a summary of entities and their configuration status."""
        entities = self._preset_data.get(PRESET_ENTITIES, [])
        targets = self._preset_data.get("targets", {})

        lines = []
        for entity_id in entities:
            friendly_name = self._get_entity_friendly_name(entity_id)
            if entity_id in targets:
                config = targets[entity_id]
                # Build config summary
                parts = []
                # State
                state = config.get("state", "on")
                parts.append(state.upper())
                # Brightness (only if on)
                if state == "on" and "brightness_pct" in config:
                    parts.append(f"{config['brightness_pct']}%")
                # Color
                if state == "on":
                    if "color_temp_kelvin" in config:
                        parts.append(f"{config['color_temp_kelvin']}K")
                    if "rgb_color" in config:
                        rgb = config["rgb_color"]
                        parts.append(f"RGB({rgb[0]},{rgb[1]},{rgb[2]})")
                # Transition
                if "transition" in config and config["transition"] > 0:
                    parts.append(f"{config['transition']}s")
                config_str = ", ".join(parts)
                lines.append(f"• {friendly_name}: {config_str}")
            else:
                lines.append(f"• {friendly_name}: (not configured)")

        return "\n".join(lines) if lines else "No entities selected"

    async def async_step_preset_entity_menu(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Hub step for managing preset entities - configure, add, remove, or save."""
        entities = self._preset_data.get(PRESET_ENTITIES, [])
        errors: dict[str, str] = {}

        if user_input is not None:
            action = user_input.get("action", "")

            if action == "configure":
                # Go to entity selection for configuration
                return await self.async_step_select_entity_to_configure()
            elif action == "add":
                # Go to add more entities
                return await self.async_step_add_more_entities()
            elif action == "remove":
                if len(entities) <= 1:
                    errors["base"] = "cannot_remove_last"
                else:
                    return await self.async_step_remove_entity()
            elif action == "save":
                # Check if at least one entity is configured
                targets = self._preset_data.get("targets", {})
                if not targets:
                    errors["base"] = "configure_at_least_one"
                else:
                    return await self._create_preset_from_data()

        # Build action options
        action_options = [
            selector.SelectOptionDict(value="configure", label="Configure an entity"),
            selector.SelectOptionDict(value="add", label="Add more entities"),
            selector.SelectOptionDict(value="remove", label="Remove an entity"),
            selector.SelectOptionDict(value="save", label="Save preset"),
        ]

        return self.async_show_form(
            step_id="preset_entity_menu",
            data_schema=vol.Schema(
                {
                    vol.Required("action"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=action_options,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
            description_placeholders={
                "preset_name": self._preset_data.get(PRESET_NAME, ""),
                "entity_count": str(len(entities)),
                "entity_summary": self._build_entity_status_summary(),
            },
            errors=errors,
        )

    async def async_step_select_entity_to_configure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select which entity to configure."""
        entities = self._preset_data.get(PRESET_ENTITIES, [])
        targets = self._preset_data.get("targets", {})

        if user_input is not None:
            entity_id = user_input.get("entity_to_configure")
            if entity_id:
                self._configuring_entity = entity_id
                return await self.async_step_configure_entity()
            # If no entity selected, return to menu
            return await self.async_step_preset_entity_menu()

        # Build entity options with status
        entity_options = []
        for entity_id in entities:
            friendly_name = self._get_entity_friendly_name(entity_id)
            status = "✓" if entity_id in targets else "○"
            entity_options.append(
                selector.SelectOptionDict(
                    value=entity_id, label=f"{status} {friendly_name}"
                )
            )

        return self.async_show_form(
            step_id="select_entity_to_configure",
            data_schema=vol.Schema(
                {
                    vol.Required("entity_to_configure"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=entity_options,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
        )

    async def async_step_configure_entity(  # noqa: C901
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Configure a specific entity's settings."""
        entity_id = getattr(self, "_configuring_entity", None)
        if not entity_id:
            return await self.async_step_preset_entity_menu()

        friendly_name = self._get_entity_friendly_name(entity_id)
        targets = self._preset_data.get("targets", {})

        # Get existing config for defaults
        existing = targets.get(entity_id, {})

        if user_input is not None:
            # Store this entity's configuration
            target: dict[str, Any] = {"entity_id": entity_id}

            # Add state
            state = user_input.get(PRESET_STATE, "on")
            target["state"] = state

            # Add transition
            transition = user_input.get(PRESET_TRANSITION, 0)
            if transition > 0:
                target["transition"] = float(transition)

            # Only add brightness and color settings if state is "on"
            if state == "on":
                # Add brightness
                brightness = user_input.get(PRESET_BRIGHTNESS_PCT)
                if brightness is not None:
                    target["brightness_pct"] = int(brightness)

                # Add color based on mode
                color_mode = user_input.get(PRESET_COLOR_MODE, COLOR_MODE_NONE)
                if color_mode == COLOR_MODE_COLOR_TEMP:
                    color_temp = user_input.get(PRESET_COLOR_TEMP_KELVIN)
                    if color_temp is not None:
                        target["color_temp_kelvin"] = int(color_temp)
                elif color_mode == COLOR_MODE_RGB:
                    rgb_color = user_input.get(PRESET_RGB_COLOR)
                    if rgb_color:
                        target["rgb_color"] = list(rgb_color)

            # Store the target configuration
            self._preset_data["targets"][entity_id] = target

            # Clear configuring entity and return to menu
            self._configuring_entity = None
            return await self.async_step_preset_entity_menu()

        # Determine defaults from existing config
        default_state = existing.get("state", "on")
        default_transition = existing.get("transition", 0)
        default_brightness = existing.get("brightness_pct", 100)
        default_color_mode = COLOR_MODE_NONE
        default_color_temp = existing.get("color_temp_kelvin", 4000)

        if "color_temp_kelvin" in existing:
            default_color_mode = COLOR_MODE_COLOR_TEMP
        elif "rgb_color" in existing:
            default_color_mode = COLOR_MODE_RGB

        # Show form for this entity
        return self.async_show_form(
            step_id="configure_entity",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        PRESET_STATE, default=default_state
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value="on", label="On"),
                                selector.SelectOptionDict(value="off", label="Off"),
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(
                        PRESET_TRANSITION, default=default_transition
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=0,
                            max=60,
                            step=0.5,
                            unit_of_measurement="s",
                            mode=selector.NumberSelectorMode.SLIDER,
                        )
                    ),
                    vol.Optional(
                        PRESET_BRIGHTNESS_PCT, default=default_brightness
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=1,
                            max=100,
                            step=1,
                            unit_of_measurement="%",
                            mode=selector.NumberSelectorMode.SLIDER,
                        )
                    ),
                    vol.Optional(
                        PRESET_COLOR_MODE, default=default_color_mode
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(
                                    value=COLOR_MODE_NONE, label="No Color"
                                ),
                                selector.SelectOptionDict(
                                    value=COLOR_MODE_COLOR_TEMP,
                                    label="Color Temperature",
                                ),
                                selector.SelectOptionDict(
                                    value=COLOR_MODE_RGB, label="RGB Color"
                                ),
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(
                        PRESET_COLOR_TEMP_KELVIN, default=default_color_temp
                    ): selector.NumberSelector(
                        selector.NumberSelectorConfig(
                            min=2000,
                            max=6500,
                            step=100,
                            unit_of_measurement="K",
                            mode=selector.NumberSelectorMode.SLIDER,
                        )
                    ),
                    vol.Optional(PRESET_RGB_COLOR): selector.ColorRGBSelector(),
                }
            ),
            description_placeholders={
                "entity_name": friendly_name,
            },
        )

    async def async_step_add_more_entities(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Add more entities to the preset."""
        if user_input is not None:
            new_entities = user_input.get("new_entities", [])
            if new_entities:
                # Add new entities to the list (avoid duplicates)
                current_entities = self._preset_data.get(PRESET_ENTITIES, [])
                for entity_id in new_entities:
                    if entity_id not in current_entities:
                        current_entities.append(entity_id)
                self._preset_data[PRESET_ENTITIES] = current_entities

            return await self.async_step_preset_entity_menu()

        # Get current entities to exclude from selection
        current_entities = self._preset_data.get(PRESET_ENTITIES, [])

        return self.async_show_form(
            step_id="add_more_entities",
            data_schema=vol.Schema(
                {
                    vol.Optional("new_entities"): selector.EntitySelector(
                        selector.EntitySelectorConfig(
                            domain=["light", "group"],
                            multiple=True,
                        )
                    ),
                }
            ),
            description_placeholders={
                "current_count": str(len(current_entities)),
            },
        )

    async def async_step_remove_entity(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Remove an entity from the preset."""
        entities = self._preset_data.get(PRESET_ENTITIES, [])

        if user_input is not None:
            entity_to_remove = user_input.get("entity_to_remove")
            if entity_to_remove and entity_to_remove in entities:
                # Remove from entities list
                entities.remove(entity_to_remove)
                self._preset_data[PRESET_ENTITIES] = entities
                # Also remove from targets if configured
                targets = self._preset_data.get("targets", {})
                if entity_to_remove in targets:
                    del targets[entity_to_remove]

            return await self.async_step_preset_entity_menu()

        # Build entity options
        entity_options = []
        for entity_id in entities:
            friendly_name = self._get_entity_friendly_name(entity_id)
            entity_options.append(
                selector.SelectOptionDict(value=entity_id, label=friendly_name)
            )

        return self.async_show_form(
            step_id="remove_entity",
            data_schema=vol.Schema(
                {
                    vol.Required("entity_to_remove"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=entity_options,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
        )

    async def _create_preset_from_data(self) -> ConfigFlowResult:
        """Create or update the preset from collected data with per-entity targets."""
        data = self._preset_data
        name = data.get(PRESET_NAME, "").strip()
        entities = data.get(PRESET_ENTITIES, [])
        targets_dict = data.get("targets", {})

        # Convert targets dict to list format expected by preset_manager
        targets = list(targets_dict.values())

        # Derive preset-level state from per-entity targets
        # If all targets are "off", preset state is "off"; otherwise "on"
        target_states = [t.get("state", "on") for t in targets]
        preset_state = (
            "off" if target_states and all(s == "off" for s in target_states) else "on"
        )

        # Derive preset-level transition from per-entity targets
        # Use the maximum transition among targets (or 0.0 if none set)
        target_transitions = [t.get("transition", 0) for t in targets]
        preset_transition = (
            float(max(target_transitions)) if target_transitions else 0.0
        )

        # Check if we're editing an existing preset
        editing_preset_id = getattr(self, "_editing_preset_id", None)

        # Get preset manager from runtime_data
        if (
            hasattr(self.config_entry, "runtime_data")
            and self.config_entry.runtime_data
        ):
            preset_manager = self.config_entry.runtime_data.preset_manager
            if preset_manager:
                # Collect preset-level defaults (round-trip from service-created presets)
                preset_kwargs: dict[str, Any] = {
                    "name": name,
                    "entities": entities,
                    "state": preset_state,
                    "targets": targets,
                    "transition": preset_transition,
                    "skip_verification": data.get(PRESET_SKIP_VERIFICATION, False),
                    "brightness_pct": data.get(PRESET_BRIGHTNESS_PCT, 100),
                    "rgb_color": data.get(PRESET_RGB_COLOR),
                    "color_temp_kelvin": data.get(PRESET_COLOR_TEMP_KELVIN),
                    "effect": data.get(PRESET_EFFECT),
                }

                if editing_preset_id and editing_preset_id in preset_manager.presets:
                    # Update in-place to preserve preset_id (and entity registry IDs)
                    await preset_manager.update_preset(
                        editing_preset_id, **preset_kwargs
                    )
                    _LOGGER.info(
                        "Updated preset: %s with %d entity configs", name, len(targets)
                    )
                else:
                    # Create new preset
                    await preset_manager.create_preset(**preset_kwargs)
                    _LOGGER.info(
                        "Created preset: %s with %d entity configs", name, len(targets)
                    )

        # Clear stored data
        self._preset_data = {}
        self._configuring_entity = None
        self._editing_preset_id = None

        # Return to menu
        return self.async_create_entry(title="", data=self.config_entry.options)

    async def async_step_manage_presets(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle managing existing presets - show menu with edit/delete options."""
        # Get preset manager from runtime_data
        preset_manager = None
        if (
            hasattr(self.config_entry, "runtime_data")
            and self.config_entry.runtime_data
        ):
            preset_manager = self.config_entry.runtime_data.preset_manager

        if not preset_manager or not preset_manager.presets:
            # No presets to manage
            return self.async_show_form(
                step_id="manage_presets",
                data_schema=vol.Schema({}),
                description_placeholders={"preset_count": "0"},
                errors={"base": "no_presets"},
            )

        return self.async_show_menu(
            step_id="manage_presets",
            menu_options=["edit_preset", "delete_preset"],
            description_placeholders={"preset_count": str(len(preset_manager.presets))},
        )

    async def async_step_edit_preset(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select a preset to edit."""
        preset_manager = None
        if (
            hasattr(self.config_entry, "runtime_data")
            and self.config_entry.runtime_data
        ):
            preset_manager = self.config_entry.runtime_data.preset_manager

        if not preset_manager or not preset_manager.presets:
            return await self.async_step_manage_presets()

        if user_input is not None:
            preset_id = user_input.get("preset_to_edit")
            if preset_id and preset_id in preset_manager.presets:
                # Load preset data into editing state
                preset = preset_manager.presets[preset_id]
                self._editing_preset_id = preset_id

                # Convert preset to _preset_data format for reuse of entity menu
                self._preset_data = {
                    PRESET_NAME: preset.name,
                    PRESET_ENTITIES: list(preset.entities),
                    PRESET_SKIP_VERIFICATION: preset.skip_verification,
                    PRESET_BRIGHTNESS_PCT: preset.brightness_pct,
                    PRESET_RGB_COLOR: preset.rgb_color,
                    PRESET_COLOR_TEMP_KELVIN: preset.color_temp_kelvin,
                    PRESET_EFFECT: preset.effect,
                    PRESET_TRANSITION: preset.transition,
                    "targets": {},
                }

                # Convert targets list to dict keyed by entity_id
                for target in preset.targets:
                    entity_id = target.get("entity_id")
                    if entity_id:
                        self._preset_data["targets"][entity_id] = target.copy()

                return await self.async_step_preset_entity_menu()

            return await self.async_step_manage_presets()

        # Build preset options
        preset_options = [
            selector.SelectOptionDict(value=pid, label=p.name)
            for pid, p in preset_manager.presets.items()
        ]

        return self.async_show_form(
            step_id="edit_preset",
            data_schema=vol.Schema(
                {
                    vol.Required("preset_to_edit"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=preset_options,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
        )

    async def async_step_delete_preset(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Select a preset to delete."""
        preset_manager = None
        if (
            hasattr(self.config_entry, "runtime_data")
            and self.config_entry.runtime_data
        ):
            preset_manager = self.config_entry.runtime_data.preset_manager

        if not preset_manager or not preset_manager.presets:
            return await self.async_step_manage_presets()

        if user_input is not None:
            preset_id = user_input.get("preset_to_delete")
            if preset_id and preset_id in preset_manager.presets:
                # Store for confirmation step
                self._deleting_preset_id = preset_id
                return await self.async_step_confirm_delete()

            return await self.async_step_manage_presets()

        # Build preset options with entity count
        preset_options = []
        for pid, preset in preset_manager.presets.items():
            entity_count = len(preset.entities)
            label = f"{preset.name} ({entity_count} {'entity' if entity_count == 1 else 'entities'})"
            preset_options.append(selector.SelectOptionDict(value=pid, label=label))

        return self.async_show_form(
            step_id="delete_preset",
            data_schema=vol.Schema(
                {
                    vol.Required("preset_to_delete"): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=preset_options,
                            mode=selector.SelectSelectorMode.LIST,
                        )
                    ),
                }
            ),
        )

    async def async_step_confirm_delete(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm preset deletion."""
        preset_id = getattr(self, "_deleting_preset_id", None)
        if not preset_id:
            return await self.async_step_manage_presets()

        preset_manager = None
        if (
            hasattr(self.config_entry, "runtime_data")
            and self.config_entry.runtime_data
        ):
            preset_manager = self.config_entry.runtime_data.preset_manager

        if not preset_manager or preset_id not in preset_manager.presets:
            return await self.async_step_manage_presets()

        preset = preset_manager.presets[preset_id]

        if user_input is not None:
            if user_input.get("confirm_delete"):
                await preset_manager.delete_preset(preset_id)
                _LOGGER.info("Deleted preset: %s", preset_id)
                self._deleting_preset_id = None
                return self.async_create_entry(title="", data=self.config_entry.options)
            else:
                # User didn't confirm, return to manage presets
                self._deleting_preset_id = None
                return await self.async_step_manage_presets()

        return self.async_show_form(
            step_id="confirm_delete",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "confirm_delete", default=False
                    ): selector.BooleanSelector(),
                }
            ),
            description_placeholders={
                "preset_name": preset.name,
                "entity_count": str(len(preset.entities)),
            },
        )
