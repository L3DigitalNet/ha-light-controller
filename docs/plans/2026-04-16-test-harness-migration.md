# Test Harness Migration Plan

- Status: 🟡 Proposed — follow-up from Batch 13
- Created: 2026-04-16
- Context: current test suite uses manual mocks in `tests/conftest.py`; this plan migrates to `pytest-homeassistant-custom-component` fixtures

## Goal

Replace the hand-rolled `homeassistant` mock layer in `tests/conftest.py` with `pytest-homeassistant-custom-component` fixtures. This gives real HA event loop, entity registry, config entry lifecycle, and service call plumbing.

## Current State

- 324 unit tests using manual mocks (all pass, 98%+ coverage)
- `tests/integration/` skeleton created with `@pytest.mark.integration`
- `pytest-homeassistant-custom-component` is in `[dependency-groups.dev]`

## Migration Steps

1. **Fixture mapping**: map each existing `conftest.py` fixture to its `pytest-homeassistant-custom-component` equivalent (`hass`, `config_entry`, `enable_custom_integrations`, etc.)
2. **Convert 3 smoke tests first**: setup+unload, one `ensure_state` call, one config-flow happy path — validate the harness works
3. **Batch migrate**: convert test classes one at a time, keeping old mocks alongside new harness tests until each class is fully migrated
4. **Remove mock layer**: once all tests run on the real harness, delete the manual mock setup in `conftest.py`
5. **CI marker**: add `integration` marker to CI matrix; initially non-blocking, then required after full migration

## Estimated Scope

~300 test cases to migrate. Priority order:
1. `test_controller.py` (core logic, highest value)
2. `test_config_flow.py` (config flow lifecycle)
3. `test_preset_manager.py` (data layer)
4. `test_button.py` + `test_sensor.py` (entity lifecycle)
5. `test_diagnostics.py` (small, easy)

## Risk

Medium. The real harness may expose behaviors that differ from the mock layer (e.g., event loop timing, entity registry side effects). Each divergence is valuable but needs investigation.
