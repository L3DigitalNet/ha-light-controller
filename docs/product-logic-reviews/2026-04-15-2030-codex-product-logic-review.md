# Claude Code Review Handoff

Suggested skill: `superpowers:receiving-code-review`

## Review Meta

- review_type: `product-and-business-logic-review`
- repo: `/home/chris/projects/ha-light-controller`
- branch: `main`
- commit: `11b525c1d0139673e78daf7a68a4557d3715f0ce`
- worktree: `dirty` (`?? .codex`, `?? docs/`)
- shared_research_reused: `docs/review-orchestrator/2026-04-16-0018-codex-review-shared-research.md`
- additional_internet_research: `none`
- passes:
  - `pass-1`: config/setup and user-facing workflow inventory
  - `pass-2`: runtime ensure/retry/verification semantics
  - `pass-3`: preset lifecycle, edit/delete, and activation behavior
  - `pass-4`: cross-surface consistency across services, options UI, entity surfaces, docs, and tests
  - `pass-5`: convergence/no new issue pass

## What Was Verified

- Services, config flow, preset manager, button/sensor entity surfaces, translations, and README/service docs were reviewed directly.
- Shared Home Assistant guidance from the orchestrator research pack was sufficient for this review; no targeted follow-up browsing was needed.
- Local test execution could not be completed in this environment because `pytest` failed during collection with `Unknown config option: asyncio_default_fixture_loop_scope` and unregistered `asyncio` markers.

## Findings

### PLR-001

- severity: `high`
- confidence: `high`
- type: `workflow-semantics`
- title: `Single-mode color verification can never fail, so retries are skipped for the main advertised use case`
- evidence:
  - [custom_components/ha_light_controller/controller.py](/home/chris/projects/ha-light-controller/custom_components/ha_light_controller/controller.py:456)
  - [tests/test_controller.py](/home/chris/projects/ha-light-controller/tests/test_controller.py:1103)
- detail:
  - `_verify_light()` treats an unspecified color mode as automatically successful, then returns success when `rgb_ok or kelvin_ok` is true.
  - For an RGB-only target, `kelvin_ok` defaults to `True`, so an RGB mismatch still returns `SUCCESS`.
  - For a Kelvin-only target, `rgb_ok` defaults to `True`, so a Kelvin mismatch still returns `SUCCESS`.
  - The tests explicitly encode this as current expected behavior, which means the suite currently protects the bug rather than the intended business rule.
- impact:
  - Color scenes can report success without actually matching the requested color or temperature.
  - Retry logic is bypassed for the integration’s core “verify and retry” promise whenever only one color mode is targeted.

### PLR-002

- severity: `high`
- confidence: `high`
- type: `cross-surface-consistency`
- title: `Presets that include groups lose their configured per-entity settings after expansion`
- evidence:
  - [custom_components/ha_light_controller/config_flow.py](/home/chris/projects/ha-light-controller/custom_components/ha_light_controller/config_flow.py:410)
  - [custom_components/ha_light_controller/services.yaml](/home/chris/projects/ha-light-controller/custom_components/ha_light_controller/services.yaml:210)
  - [custom_components/ha_light_controller/preset_manager.py](/home/chris/projects/ha-light-controller/custom_components/ha_light_controller/preset_manager.py:301)
  - [custom_components/ha_light_controller/controller.py](/home/chris/projects/ha-light-controller/custom_components/ha_light_controller/controller.py:263)
- detail:
  - The UI and service docs allow presets to be created from `light.*` groups and `group.*` helpers.
  - Preset targets are stored against the original selected entity IDs.
  - `ensure_state()` expands groups to member lights first, then `_build_targets()` only looks up overrides by expanded member entity ID.
  - Any target stored against the group entity ID is therefore ignored during activation.
- impact:
  - Group-based presets silently fall back to preset defaults instead of the configured brightness/color/effect/transition.
  - `create_preset_from_current()` can also capture group-level targets that will not survive activation.
- note:
  - This is a direct code-path inference from the controller/preset flow; there is no compensating remap from group target to member lights.

### PLR-003

- severity: `medium-high`
- confidence: `high`
- type: `state-lifecycle`
- title: `Editing a preset is implemented as delete-and-recreate, which churns IDs and entity identity`
- evidence:
  - [custom_components/ha_light_controller/config_flow.py](/home/chris/projects/ha-light-controller/custom_components/ha_light_controller/config_flow.py:806)
  - [custom_components/ha_light_controller/preset_manager.py](/home/chris/projects/ha-light-controller/custom_components/ha_light_controller/preset_manager.py:229)
  - [custom_components/ha_light_controller/button.py](/home/chris/projects/ha-light-controller/custom_components/ha_light_controller/button.py:98)
  - [custom_components/ha_light_controller/sensor.py](/home/chris/projects/ha-light-controller/custom_components/ha_light_controller/sensor.py:103)
- detail:
  - The edit flow comment says it will recreate the preset “with same ID”, but `create_preset()` always generates a fresh UUID.
  - Button and sensor unique IDs are derived from `preset_id`, so an edit deletes the old entities and creates new ones with different unique IDs.
- impact:
  - User customizations tied to the preset entities can be lost on edit.
  - Any automation or dashboard item referencing the old preset entity IDs can drift or break after a routine edit.

### PLR-004

- severity: `medium`
- confidence: `high`
- type: `cross-surface-consistency`
- title: `The options editor cannot round-trip presets that rely on preset-level defaults`
- evidence:
  - [custom_components/ha_light_controller/__init__.py](/home/chris/projects/ha-light-controller/custom_components/ha_light_controller/__init__.py:462)
  - [custom_components/ha_light_controller/preset_manager.py](/home/chris/projects/ha-light-controller/custom_components/ha_light_controller/preset_manager.py:64)
  - [custom_components/ha_light_controller/config_flow.py](/home/chris/projects/ha-light-controller/custom_components/ha_light_controller/config_flow.py:491)
  - [custom_components/ha_light_controller/config_flow.py](/home/chris/projects/ha-light-controller/custom_components/ha_light_controller/config_flow.py:900)
- detail:
  - Service-created presets can store preset-level `brightness_pct`, `rgb_color`, `color_temp_kelvin`, and `effect` without per-target overrides.
  - The edit UI only loads `preset.targets` into `_preset_data`, ignores preset-level fields, and refuses to save unless at least one target is configured.
  - When the edited preset is saved, `_create_preset_from_data()` only writes `state`, `targets`, `transition`, and `skip_verification`.
- impact:
  - Presets created through services are not faithfully editable through the options UI.
  - Round-tripping a preset through the editor can discard valid preset-level semantics even before the ID churn from PLR-003 is considered.

### PLR-005

- severity: `medium`
- confidence: `high`
- type: `workflow-semantics`
- title: `Preset names are documented as unique but the implementation allows ambiguous duplicates`
- evidence:
  - [custom_components/ha_light_controller/services.yaml](/home/chris/projects/ha-light-controller/custom_components/ha_light_controller/services.yaml:203)
  - [custom_components/ha_light_controller/config_flow.py](/home/chris/projects/ha-light-controller/custom_components/ha_light_controller/config_flow.py:382)
  - [custom_components/ha_light_controller/__init__.py](/home/chris/projects/ha-light-controller/custom_components/ha_light_controller/__init__.py:453)
  - [custom_components/ha_light_controller/preset_manager.py](/home/chris/projects/ha-light-controller/custom_components/ha_light_controller/preset_manager.py:193)
- detail:
  - Both the service docs and the UI copy describe preset names as unique.
  - Neither the options flow nor the `create_preset` service enforces uniqueness.
  - `find_preset()` resolves by ID first, then returns the first case-insensitive name match.
- impact:
  - `activate_preset` by name becomes ambiguous as soon as duplicates exist.
  - The repo’s documented contract and actual business rule diverge, which makes user behavior unpredictable.

## Residual Risks

- Mixed-state presets are intentionally collapsed to a single preset-level `state` of `on` when any target is on, which can make button/sensor attributes less descriptive than actual activation behavior.
- Existing tests are strong on internal coverage but currently miss or normalize several cross-surface product invariants, especially edit round-trips, name uniqueness, and group-based preset activation semantics.

## Claude-Oriented Fix Order

- batch-1:
  - Fix PLR-001 first.
  - Update the controller tests that currently assert the false-positive behavior as success.
  - Add explicit regression coverage for RGB-only and Kelvin-only mismatches.
- batch-2:
  - Fix PLR-002 and PLR-004 together because both point to the same preset data-model mismatch between stored targets and activation-time expansion.
  - Decide whether groups should be expanded at capture time or whether override remapping should happen at activation time.
- batch-3:
  - Fix PLR-003 by introducing a true update path that preserves preset IDs and entity continuity.
  - Re-test button/sensor lifecycle and entity registry cleanup after edit.
- batch-4:
  - Fix PLR-005 by enforcing unique names or by changing the product contract so activation is ID-only.
  - Align the service docs, options UI, and error messaging with the chosen rule.
