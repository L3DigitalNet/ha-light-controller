# Handoff

- Last updated: 2026-04-16
- Previous session: 2026-04-16 — executed full 16-batch remediation plan (all Codex review findings)

## Session Instructions (read before starting work)

1. Read this file first. The remediation plan is complete.
2. Branch: `testing` has 15 commits beyond `main`. All changes are on `testing`.
3. Next step: merge `testing` into `main` (or push `testing` for CI validation first).
4. Follow-up plan for integration test migration: `docs/plans/2026-04-16-test-harness-migration.md`

## Specs & Plans

| Artifact | Path | Status |
| --- | --- | --- |
| Remediation plan | `docs/plans/2026-04-16-codex-review-remediation.md` | ✅ Complete |
| Test harness migration | `docs/plans/2026-04-16-test-harness-migration.md` | 🟡 Follow-up |
| Review sweep outcome | `docs/review-orchestrator/2026-04-16-0018-codex-review-sweep.md` | ✅ Complete |

## What Is Deployed

- Released tag: `v0.4.0` (HACS custom integration)
- `testing` branch: 17 commits ahead of `main`, ready for merge
- Version: `0.4.0` consistent across manifest.json, pyproject.toml, CHANGELOG.md
- CI: all Actions pinned to SHA, uv-based dependency management, 95% coverage gate
- Tests: 324 passing, 98.55% branch coverage

## What Remains

- **Merge testing → main** and tag v0.4.1
- **Integration test migration** (follow-up plan exists): ~300 unit tests from manual mocks to pytest-homeassistant-custom-component harness
- **strict-typing** (quality_scale.yaml): add py.typed marker, verify mypy --strict
- **AI-002**: re-verify CLAUDE.md for credentialed HA instance references (deferred — no such content found in current CLAUDE.md)

## Bugs Found and Fixed

1. **[fixed]** PLR-001 — `controller.py` `rgb_ok or kelvin_ok` → `and`. Color verification now correctly fails for single-mode targets. Commit: `cff8179`
2. **[fixed]** PLR-002 — Group-based preset overrides now expand to member lights. Commit: `71ee033`
3. **[fixed]** PLR-003 — Preset edit preserves preset_id via update_preset(). Commit: `a654fda`
4. **[fixed]** PLR-004 — Config flow editor now round-trips preset-level defaults. Commit: `71ee033`
5. **[fixed]** PLR-005 — Case-insensitive preset name uniqueness enforced. Commit: `15b3309`
6. **[fixed]** RR-001 / DEP-002 / DOC-004 — Version metadata synced to 0.4.0. Commit: `1fbcb58`
7. **[fixed]** CI-001 / DEP-004 — All Actions pinned to SHA. Commit: `45cf8ea`
8. **[fixed]** DEP-001 / CI-002 / TEST-001 — Deps consolidated into pyproject.toml + uv.lock. Commit: `610f7c1`
9. **[fixed]** OBS-001/002/003 — Diagnostics redacts PII, includes runtime status, preserves per-light VerificationResult. Commit: `bc53159`
10. **[fixed]** DEP-005 — Created scripts/setup for devcontainer. Commit: `51ee8e8`
11. **[fixed]** DOC-001/002/003/005 — Docs drift fixed across USAGE.md, CONTRIBUTING.md. Commit: `e4ffdf3`
12. **[fixed]** AI-001/003/004 — Settings.local.json, branch workflow reconciled, gitignore cleaned. Commit: `7bca89f`
13. **[fixed]** IR-001 — Incident disablement and release runbooks created. Commit: `cf13003`
14. **[fixed]** TEST-006 / RR-004/005 — 95% coverage gate, five new conventions. Commit: `ca6f8ef`
15. **[fixed]** CI-005 / DEP-003 / TEST-005 — Dead npm/Playwright surface removed. Commit: `715aff4`

## Architecture

Home Assistant custom integration. Single Python package under `custom_components/ha_light_controller/`.

| Layer | File | Purpose |
| --- | --- | --- |
| Entry | `__init__.py` | Service registration, `LightControllerData` runtime data |
| Core | `controller.py` | `ensure_state()` → expand → build targets → group → send → verify → retry |
| Preset | `preset_manager.py` | CRUD in `ConfigEntry.data`, activation helpers, name uniqueness |
| Config flow | `config_flow.py` | Menu-based options: settings, add_preset, manage_presets |
| Entities | `button.py`, `sensor.py` | Per-preset button + status sensor, created dynamically via listener |
| Diagnostics | `diagnostics.py` | Redacted config-entry diagnostics with runtime status |
| Constants | `const.py` | All `CONF_*`, `ATTR_*`, `DEFAULT_*`, `PRESET_*` |

## Credentials

| Secret | OpenBao path |
| --- | --- |
| Home Assistant dev instance token | (referenced in project memory) |

## Gotchas

- Integration tests in `tests/integration/` are excluded from default pytest run (`--ignore=tests/integration` in pyproject.toml) because they conflict with the unit test mock layer
- `testing` branch was created fresh from `main` (old `origin/testing` had stale CircleCI/Serena commits); force-push to `origin/testing` will be needed
- `_LOGGER.exception` is now used in catch blocks (includes tracebacks); test assertions checking `_LOGGER.error` may need updating if new catch-site tests are added
