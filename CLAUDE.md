# CLAUDE.md

**Session handoff:** [`docs/handoff.md`](docs/handoff.md) — read this first. Current deployed state, remaining work, bugs log, architecture, credentials, and gotchas.

**Full conventions reference:** [`docs/conventions.md`](docs/conventions.md) — LLM-targeted pattern library. Every convention follows the six-field schema (Applies-when / Rule / Code / Why / Sources / Related) with a Quick Reference table at the top for O(1) lookup. Do not introduce new patterns without checking conventions first.

This file provides guidance to Claude Code (claude.ai/code) when working with code in
this repository.

## Git Workflow

- **All changes must be made on the `testing` branch**
- **Do NOT push to `main` without explicit permission**

## Project Overview

HA-Light-Controller is a Home Assistant custom integration providing reliable light
control with state verification, automatic retries, and preset management. It ensures
lights actually reach their target state after commands are sent. Distributed via HACS.

## Environment

- **Python**: 3.14.2 (HA 2025.2+ requires Python 3.13+)
- **Testing**: Tests mock `homeassistant` module, no running HA instance needed

## Home Assistant Environment Constraints

**Blocking calls freeze the entire HA instance.** All I/O must be async or use
`hass.async_add_executor_job()`.

| Constraint | Rule                                                                                |
| ---------- | ----------------------------------------------------------------------------------- |
| Event loop | Single-threaded asyncio. Never use `time.sleep()`, sync `requests`, or blocking I/O |
| Resources  | HA runs on RPi-class hardware. Poll 30-60s minimum, prefer listeners over polling   |
| Sandbox    | No filesystem access outside `config/`. Dependencies must be PyPI + `manifest.json` |
| APIs       | Use `hass.services.async_call`, `hass.states.get`. Never bypass HA's state machine  |

## Commands

All commands can be run via Makefile targets or directly:

```bash
# Makefile targets (recommended)
make test              # Run all tests
make test-cov          # Run tests with coverage report
make lint              # Run Ruff linter
make lint-fix          # Lint with auto-fix
make format            # Format code with Ruff
make type-check        # Run mypy type checker
make quality           # Run all quality checks
make ci                # Simulate CI checks locally
make setup             # Initial project setup

# Direct commands (also work)
pytest tests/
pytest tests/test_controller.py
pytest tests/test_controller.py::test_ensure_state_single_light
pytest --cov=custom_components/ha_light_controller

# Enable debug logging (add to HA configuration.yaml)
logger:
  logs:
    custom_components.ha_light_controller: debug
```

Tests mock the entire `homeassistant` module in `tests/conftest.py` and don't require a
running HA instance.

## Architecture

### Core Components

| File                      | Purpose                                                                                                                                                                   |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `__init__.py`             | Entry point: registers services individually in `async_setup()`, initializes `LightController` and `PresetManager`, uses `_get_param()` and `_service_response()` helpers |
| `controller.py`           | Light control: `ensure_state()` → `_expand_entities()` → `_build_targets()` → `_group_by_settings_with_transition()` → send → verify → retry                              |
| `preset_manager.py`       | Preset storage in `ConfigEntry.data[CONF_PRESETS]`, `activate_preset_with_options()` for shared activation logic                                                          |
| `config_flow.py`          | Menu-based options flow: settings (collapsible sections), add_preset (multi-step with per-entity config), manage_presets (edit/delete with confirmation)                  |
| `button.py` / `sensor.py` | Preset entities: button activates preset via `preset_manager.activate_preset_with_options()`, sensor tracks status                                                        |
| `const.py`                | All `CONF_*`, `ATTR_*`, `DEFAULT_*`, `PRESET_*` constants                                                                                                                 |

### Key Classes

- `LightSettingsMixin` - Shared `to_service_data()` method for light settings
- `LightTarget(LightSettingsMixin)` - Single light with target settings
- `LightGroup(LightSettingsMixin)` - Batched lights with identical settings
- `OperationResult` - Result of ensure_state operation
- `PresetConfig` - Preset definition with `to_dict()`/`from_dict()` for storage

### Services

| Service                      | Description                                  |
| ---------------------------- | -------------------------------------------- |
| `ensure_state`               | Control lights with verification and retries |
| `activate_preset`            | Activate preset by name or ID                |
| `create_preset`              | Create preset programmatically               |
| `create_preset_from_current` | Capture current light states as preset       |
| `delete_preset`              | Delete preset by ID                          |

## Key Patterns

### Constants Convention

All configuration keys and defaults live in `const.py`:

```python
CONF_NEW_OPTION: Final = "new_option"
DEFAULT_NEW_OPTION: Final = 10
ATTR_NEW_PARAM: Final = "new_param"
```

### Service Parameter Merging

Use the `_get_param()` helper for call data with options fallback:

```python
def _get_param(call_data: dict, options: dict, attr: str, conf: str, default: Any) -> Any:
    return call_data.get(attr, options.get(conf, default))

# Usage in handler:
brightness_tolerance = _get_param(data, options, ATTR_BRIGHTNESS_TOLERANCE, CONF_BRIGHTNESS_TOLERANCE, DEFAULT_BRIGHTNESS_TOLERANCE)
```

### Entity Expansion

`_expand_entity()` resolves `light.*` groups and `group.*` helper groups to individual
`light.` entities. Uses `_get_state()` directly for attribute access.

### Service Registration

Services are registered individually in `async_setup()` (not `async_setup_entry()`).
This ensures they persist across config entry reloads. Each handler resolves the active
entry at call time via `_get_loaded_entry()`:

```python
hass.services.async_register(
    DOMAIN, SERVICE_ENSURE_STATE, async_handle_ensure_state,
    schema=SERVICE_ENSURE_STATE_SCHEMA, supports_response=SupportsResponse.OPTIONAL,
)
```

### Preset Activation Helper

`PresetManager.activate_preset_with_options()` centralizes preset activation logic:

```python
result = await preset_manager.activate_preset_with_options(preset, controller, options)
```

### Dynamic Entity Platform

Platforms use listener pattern to add/remove entities when presets change:

```python
preset_manager.register_listener(async_add_preset_entities)  # Returns unsubscribe callable
```

### Runtime Data (HA 2025.2+)

```python
@dataclass
class LightControllerData:
    controller: LightController
    preset_manager: PresetManager

entry.runtime_data = LightControllerData(...)
```

## Adding New Service Parameters

1. **const.py** - Add `ATTR_*` constant (and `CONF_*`/`DEFAULT_*` if configurable)
2. **\_\_init\_\_.py** - Add to voluptuous schema, use `_get_param()` helper in handler
3. **services.yaml** - Add field definition with HA selector
4. **controller.py** - Add to `ensure_state()` signature if needed
5. **preset_manager.py** - Add to `activate_preset_with_options()` if preset-relevant

## Testing

### Unit Tests

Tests mock HA modules before import. Key fixtures in `conftest.py`:

- `hass` - Mock HomeAssistant instance
- `config_entry` / `config_entry_with_presets` - Mock config entries
- `mock_light_states` - Pre-configured light states
- `create_light_state()` - Helper for mock State objects

### Live Testing with HA Dev Server

A Podman-based HA instance at `~/ha-plugin-test-workspace/` enables runtime testing.
Connection details and access token are stored in project memory.

```bash
# Deploy and restart
cp -r custom_components/ha_light_controller/* \
  ~/ha-plugin-test-workspace/ha-config/custom_components/ha_light_controller/
podman restart ha-plugin-test
```

Unit tests validate logic in isolation. Live testing validates HA runtime behavior that
mocks can't cover — entity lifecycle, service registration persistence across reloads,
config flow UI, and entity registry cleanup.

## Code Style

- Prefer flat over nested (3+ levels → extract helpers)
- Consistent patterns — similar operations use identical structure throughout
- Delete, don't deprecate — no commented-out code or compatibility shims
- Fail early, fail clearly — validate at boundaries, trust internal state
