# Architecture

Home Assistant custom integration. Single Python package under `custom_components/ha_light_controller/`.

## Project Overview

HA-Light-Controller provides reliable light control with state verification, automatic retries, and preset management. It ensures lights actually reach their target state after commands are sent. Distributed via HACS.

## Core Components

| Layer | File | Purpose |
| --- | --- | --- |
| Entry | `__init__.py` | Service registration (individually in `async_setup()` for persistence across reloads), `LightControllerData` runtime data, `_get_param()` and `_service_response()` helpers |
| Core | `controller.py` | `ensure_state()` → `_expand_entities()` → `_build_targets()` → `_group_by_settings_with_transition()` → send → verify → retry |
| Preset | `preset_manager.py` | CRUD in `ConfigEntry.data[CONF_PRESETS]`, `activate_preset_with_options()` for shared activation logic, name uniqueness |
| Config flow | `config_flow.py` | Menu-based options flow: settings (collapsible sections), add_preset (multi-step), manage_presets (edit/delete with confirmation) |
| Entities | `button.py`, `sensor.py` | Per-preset button + status sensor, created dynamically via listener |
| Diagnostics | `diagnostics.py` | Redacted config-entry diagnostics with runtime status |
| Constants | `const.py` | All `CONF_*`, `ATTR_*`, `DEFAULT_*`, `PRESET_*` |

## Key Classes

- `LightSettingsMixin` — shared `to_service_data()` method for light settings
- `LightTarget(LightSettingsMixin)` — single light with target settings
- `LightGroup(LightSettingsMixin)` — batched lights with identical settings
- `OperationResult` — result of ensure_state operation
- `PresetConfig` — preset definition with `to_dict()`/`from_dict()` for storage

## Services

| Service | Description |
| --- | --- |
| `ensure_state` | Control lights with verification and retries |
| `activate_preset` | Activate preset by name or ID |
| `create_preset` | Create preset programmatically |
| `create_preset_from_current` | Capture current light states as preset |
| `delete_preset` | Delete preset by ID |

## Home Assistant Environment Constraints

**Blocking calls freeze the entire HA instance.** All I/O must be async or use `hass.async_add_executor_job()`.

| Constraint | Rule |
| --- | --- |
| Event loop | Single-threaded asyncio. Never use `time.sleep()`, sync `requests`, or blocking I/O |
| Resources | HA runs on RPi-class hardware. Poll 30–60s minimum, prefer listeners over polling |
| Sandbox | No filesystem access outside `config/`. Dependencies must be PyPI + `manifest.json` |
| APIs | Use `hass.services.async_call`, `hass.states.get`. Never bypass HA's state machine |

## Key Patterns

### Constants convention

All configuration keys and defaults live in `const.py`:

```python
CONF_NEW_OPTION: Final = "new_option"
DEFAULT_NEW_OPTION: Final = 10
ATTR_NEW_PARAM: Final = "new_param"
```

### Service parameter merging

```python
def _get_param(call_data: dict, options: dict, attr: str, conf: str, default: Any) -> Any:
    return call_data.get(attr, options.get(conf, default))
```

### Entity expansion

`_expand_entity()` resolves `light.*` groups and `group.*` helper groups to individual `light.` entities. Uses `_get_state()` directly for attribute access.

### Service registration

Services are registered individually in `async_setup()` (not `async_setup_entry()`). This ensures they persist across config entry reloads. Each handler resolves the active entry at call time via `_get_loaded_entry()`.

### Preset activation helper

```python
result = await preset_manager.activate_preset_with_options(preset, controller, options)
```

### Dynamic entity platform

Platforms use listener pattern to add/remove entities when presets change:

```python
preset_manager.register_listener(async_add_preset_entities)  # returns unsubscribe callable
```

### Runtime data (HA 2025.2+)

```python
@dataclass
class LightControllerData:
    controller: LightController
    preset_manager: PresetManager

entry.runtime_data = LightControllerData(...)
```

## Adding new service parameters

1. **const.py** — add `ATTR_*` (and `CONF_*`/`DEFAULT_*` if configurable)
2. **`__init__.py`** — add to voluptuous schema, use `_get_param()` in handler
3. **services.yaml** — add field definition with HA selector
4. **controller.py** — add to `ensure_state()` signature if needed
5. **preset_manager.py** — add to `activate_preset_with_options()` if preset-relevant

## Commands

```bash
make test              # full tests
make test-cov          # with coverage
make lint              # Ruff
make lint-fix
make format
make type-check        # mypy
make quality           # all checks
make ci                # simulate CI locally
make setup             # initial setup

# Direct (uv-managed venv)
uv run pytest tests/
uv run pytest tests/test_controller.py
uv run pytest tests/test_controller.py::test_ensure_state_single_light
uv run pytest --cov=custom_components/ha_light_controller

# Debug logging (HA configuration.yaml)
logger:
  logs:
    custom_components.ha_light_controller: debug
```

## Testing

### Unit tests

Tests mock HA modules before import. Key fixtures in `conftest.py`:

- `hass` — mock HomeAssistant instance
- `config_entry` / `config_entry_with_presets`
- `mock_light_states`, `create_light_state()`

### Integration tests

`tests/integration/` contains a skeleton for `pytest-homeassistant-custom-component` harness tests. Excluded from the default pytest run (`--ignore=tests/integration` in `pyproject.toml`) because they conflict with the unit test mock layer. See `docs/plans/2026-04-16-test-harness-migration.md` for the migration plan.

### Live testing with HA dev server

Podman-based HA instance at `~/ha-plugin-test-workspace/`:

```bash
cp -r custom_components/ha_light_controller/* \
  ~/ha-plugin-test-workspace/ha-config/custom_components/ha_light_controller/
podman restart ha-plugin-test
```

Unit tests validate logic in isolation. Live testing validates HA runtime behavior mocks can't cover — entity lifecycle, service registration persistence across reloads, config flow UI, entity registry cleanup.

## Code Style

- Prefer flat over nested (3+ levels → extract helpers)
- Consistent patterns — similar operations use identical structure throughout
- Delete, don't deprecate — no commented-out code or compatibility shims
- Fail early, fail clearly — validate at boundaries, trust internal state

## Environment

- **Python:** 3.14.2 (HA 2025.2+ requires Python 3.13+)
- **Testing:** tests mock `homeassistant` module, no running HA instance needed

## Git workflow

- All changes on `testing` branch
- No push to `main` without explicit permission

## Gotchas

- Integration tests in `tests/integration/` are excluded from the default pytest run (`--ignore=tests/integration`) because they conflict with the unit test mock layer.
- `testing` branch was created fresh from `main` (old `origin/testing` had stale CircleCI/Serena commits); force-push to `origin/testing` will be needed.
- `_LOGGER.exception` is now used in catch blocks (includes tracebacks); test assertions checking `_LOGGER.error` may need updating if new catch-site tests are added.
