# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.1] - 2026-04-16

### Fixed
- Color verification now correctly detects mismatches for single-mode targets (RGB-only
  or kelvin-only). Previously, the `or` logic silently passed when only one mode was
  requested, so retries never fired for the core use case (PLR-001)
- Group-based preset overrides now reach individual member lights instead of being
  silently discarded after entity expansion (PLR-002)
- Preset editing preserves the original preset ID, preventing button/sensor entity churn
  that broke automations and dashboard references (PLR-003)
- Config flow editor now round-trips preset-level defaults (brightness, color, effect)
  for service-created presets (PLR-004)
- Case-insensitive preset name uniqueness enforced in both service calls and config flow;
  duplicate names are rejected with a clear error (PLR-005)
- Version metadata synchronized across manifest.json, pyproject.toml, and CHANGELOG.md;
  `scripts/check_versions.py` prevents future drift (RR-001)
- Diagnostics output now redacts preset names and entity IDs; includes runtime preset
  status and per-light verification failure reasons (OBS-001/002/003)
- Devcontainer `scripts/setup` bootstrap script created (was missing) (DEP-005)
- Exception logging switched from `_LOGGER.error` to `_LOGGER.exception` for full
  tracebacks at catch sites

### Changed
- All GitHub Actions pinned to full commit SHA with version comments; Dependabot rotates
  SHAs automatically (CI-001)
- Python dependencies consolidated into `pyproject.toml` `[dependency-groups.dev]` with
  locked `uv.lock`; CI and Makefile use `uv sync --locked --group dev` (DEP-001)
- Makefile uses `uv run` prefix for all tool invocations
- Concurrency groups added to CI and Validate workflows
- 95% coverage gate enforced via `--cov-fail-under`
- CONTRIBUTING.md updated: branch from `testing`, PR to `testing` (not `main`)

### Removed
- `package.json`, `package-lock.json`, and all Playwright/npm references (dead surface)
- Stale AI-artifact comment block from `.gitignore`

### Added
- `scripts/check_versions.py` for version consistency validation (called from `make ci`)
- `docs/runbooks/incident-disablement.md` and `docs/runbooks/release.md`
- Five new conventions in `docs/conventions.md` (release, deps, diagnostics, ops)
- Integration test skeleton (`tests/integration/`) with follow-up migration plan
- `PresetManager.update_preset()` for in-place preset modification

## [0.4.0] - 2026-02-18

### Added
- Diagnostics support — `async_get_config_entry_diagnostics()` returns preset summary for
  HA diagnostics downloads (IQS Gold)
- Exception translation keys for all service errors — `ServiceValidationError` and
  `HomeAssistantError` now carry `translation_domain`, `translation_key`, and
  `translation_placeholders` for localizable error messages (IQS Gold)
- `PARALLEL_UPDATES = 0` in button and sensor platforms — allows HA to update all preset
  entities simultaneously rather than sequentially (IQS Silver)
- Community health files: `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, and
  `.github/pull_request_template.md`

### Fixed
- Preset status timestamps now use timezone-aware `datetime.now(tz=UTC)` instead of
  naive `datetime.utcnow()` (Python 3.12+ deprecation)
- Removed deprecated `homeassistant` key from `manifest.json` (hassfest compliance)

### Changed
- Removed dynamic `icon` property from `PresetButton` — icons are now declared entirely
  via `icons.json` icon translations (IQS Gold icon-translations compliance)
- Simplified repository documentation: removed ~25,000 lines of auto-generated reference
  docs, replaced by the home-assistant-dev plugin which supersedes embedded skills and
  agents

## [0.3.0] - 2026-02-18

### Added
- Icon translations (`icons.json`) for sensor states and button default — IQS Gold compliance
- HACS and Hassfest validation GitHub Actions workflow
- Entity self-removal on preset deletion (stale entity cleanup)
- Tracking set cleanup in button/sensor platform listeners to prevent unbounded growth

### Changed
- Service handlers now raise `ServiceValidationError`/`HomeAssistantError` instead of returning error dicts — IQS Silver compliance
- Removed `STATUS_ICONS` dict and `icon` property from sensor (replaced by icon translations)
- Updated documentation versions to 0.3.0
- Updated GitHub repo description and added topics for HACS discoverability
- Added `.claude/state/`, `.playwright-mcp/`, and `ui-test-*.png` to `.gitignore`

### Removed
- Notification feature and blueprints to simplify integration scope
- Old `.claude/skills/` directory (migrated to plugin system)
- `.vscode/settings.json` (consolidated to global settings)
- Dead code: removed redundant entity registry cleanup tests


## [0.2.2] - 2026-02-14

### Fixed

- Handle non-string entity IDs in entity expansion
- Config flow typing and lint issues
- Typing and lint issues for light controller services

### Changed

- Updated documentation for v0.2.1 release
- Updated contributor documentation with current tooling and versions
- Updated core instruction files to reflect current environment

### Added

- Skills for Home Assistant integration development
- Link verification tooling and report
- uv.lock file for package management

## [0.2.1] - 2026-02-07

### Added

- Per-entity state and transition support in presets
- Mixed on/off states in single preset (e.g., turn some lights on, others off)
- Per-entity transition times with fallback to global preset transition
- `_send_commands_per_target()` method for handling mixed-state presets

### Changed

- Updated Python requirement to 3.14.2 (Home Assistant 2025.2.0+)
- Updated minimum Home Assistant version to 2025.2.0
- Improved documentation clarity and removed early beta disclaimer
- Preset creation now derives preset-level state/transition from per-entity configs

### Fixed

- Preset configuration gaps where UI-collected per-entity settings were not used by
  backend
- Hardcoded `state="on"` and `transition=0.0` in preset creation
- Minor bug fixes and stability improvements

## [0.2.0] - 2026-01-31

### Removed

- Notification feature (`notify_on_failure` parameter)
- Blueprint automation templates (adaptive_lighting, button_scene_controller,
  motion_activated_scene, scene_scheduler)

### Changed

- Simplified scope to focus on core light control and preset management
- Updated documentation to reflect current feature set

### Notes

This release removes features that were not essential to the core functionality. Users
requiring notifications can implement them via automations triggered by service
responses. The core ensure_state service and preset management remain fully functional.

## [0.1.3] - 2026-01-31

- Previous release (see git history)
