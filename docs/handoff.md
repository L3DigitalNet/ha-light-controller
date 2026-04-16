# Handoff

- Last updated: 2026-04-16
- Previous session: 2026-04-15/16 — ran Codex review orchestrator sweep (9 reviews) and produced remediation plan; **no code changed**

## Session Instructions (read before starting work)

1. Read this file first. Then skim `docs/plans/2026-04-16-codex-review-remediation.md` — it defines the batches.
2. The plan has 9 open questions (Q1-Q9). User has not yet answered them. **Confirm answers with the user before executing any batch except Batch 0.**
3. Branch: per `CLAUDE.md`, all changes must be made on `testing`. `origin/testing` exists but not local. `main` is 5 `Auto-commit from sys76` commits beyond `v0.4.0`.
4. Review artifacts (`docs/review-orchestrator/`, `docs/*-reviews/`, `docs/plans/`, `.codex/`) are **untracked** — commit them as Batch 0 before any code change so the review trail is durable.
5. Use the `superpowers:receiving-code-review` skill when acting on review findings.
6. Tests cannot be run in sandbox without setup: `pytest` fails at collection with `Unknown config option: asyncio_default_fixture_loop_scope`. Batch 8 fixes this.

## Specs & Plans

| Artifact | Path | Status |
| --- | --- | --- |
| Review sweep outcome | `docs/review-orchestrator/2026-04-16-0018-codex-review-sweep.md` | 🟢 Complete |
| Shared research pack | `docs/review-orchestrator/2026-04-16-0018-codex-review-shared-research.md` | 🟢 Complete |
| Live sweep status | `docs/review-orchestrator/2026-04-16-0018-codex-review-live-status.md` | 🟢 Complete |
| Remediation plan | `docs/plans/2026-04-16-codex-review-remediation.md` | 🟡 Proposed, awaiting Q1-Q9 answers |
| Product-logic review | `docs/product-logic-reviews/2026-04-15-2030-codex-product-logic-review.md` | 🟢 Complete |
| Documentation review | `docs/documentation-reviews/2026-04-15-2029-codex-documentation-review.md` | 🟢 Complete |
| Release-readiness review | `docs/release-readiness-reviews/2026-04-15-2030-codex-release-readiness-review.md` | 🟢 Complete |
| CI/CD review | `docs/ci-reviews/2026-04-15-2028-codex-ci-review.md` | 🟢 Complete |
| Dependency review | `docs/dependency-reviews/2026-04-15-2026-codex-dependency-review.md` | 🟢 Complete |
| Observability review | `docs/observability-reviews/2026-04-15-2029-codex-observability-review.md` | 🟢 Complete |
| Incident-readiness review | `docs/incident-readiness-reviews/2026-04-15-2029-codex-incident-readiness-review.md` | 🟢 Complete |
| Test-suite review | `docs/test-reviews/2026-04-15-2034-codex-test-review.md` | 🟢 Complete |
| AI-workflow review | `docs/ai-workflow-reviews/2026-04-15-2029-codex-ai-workflow-review.md` | 🟢 Complete |

## What Is Deployed

- Released tag: `v0.4.0` (HACS custom integration)
- Version surfaces:
  - `custom_components/ha_light_controller/manifest.json` → `0.4.0`
  - `CHANGELOG.md` → `0.4.0`
  - `pyproject.toml` → `0.3.0` ⚠ **drift (Batch 1 fix)**
  - `package.json` → `0.3.0` ⚠ **drift (Batch 1 fix; also candidate for deletion per Batch 9)**
  - `uv.lock` → `0.2.1` ⚠ **drift (Batch 1 fix)**
- HEAD on `main`: `11b525c1d0139673e78daf7a68a4557d3715f0ce` (5 commits past `v0.4.0`, not tagged)
- CI surface: `.github/workflows/{ci,validate}.yml` — green matrix on Python 3.13 and 3.14; actions currently pinned to mutable tags (`@v5`, `@v6`, `@main`, `@master`)
- HACS + Hassfest validation runs on push/PR + nightly schedule

## What Remains

See `docs/plans/2026-04-16-codex-review-remediation.md` for full batch plan. Highlights:

**Critical bugs to fix (Batches 1-2, user-visible):**
- PLR-001: `controller.py:469-474` — `rgb_ok or kelvin_ok` with defaults causes single-mode color verification to always return `SUCCESS`. Retries never fire for the main advertised use case.
- RR-001 / DOC-004 / DEP-002: version metadata split across `manifest.json` (0.4.0), `pyproject.toml` (0.3.0), `package.json` (0.3.0), `uv.lock` (0.2.1).

**Correctness debt (Batches 4-6):**
- PLR-002: group-based presets silently lose per-entity overrides at activation
- PLR-003: editing a preset deletes-and-recreates, churning unique IDs on button/sensor entities
- PLR-004: options editor cannot round-trip presets with preset-level defaults
- PLR-005: preset names advertised unique but not enforced

**Hygiene / governance (Batches 7-15):**
- Pin every GitHub Action to a full SHA (`@main`/`@master` still in validation workflow)
- Move Python deps from ad hoc `pip install` lists into `pyproject.toml` + `uv.lock`
- Delete dead Playwright/npm surface (or restore it — see Q5)
- Diagnostics redaction + runtime status via `async_redact_data`
- Incident-disablement runbook + release runbook
- Coverage gate (`--cov-fail-under`)
- `.claude/settings.json` cross-repo read → local
- Resolve `CLAUDE.md` vs `CONTRIBUTING.md` branch-workflow contradiction

## Bugs Found and Fixed

1. **[open]** PLR-001 — `controller.py:469-474` `rgb_ok or kelvin_ok` short-circuits to `SUCCESS` when only one color mode is targeted (the non-targeted mode defaults to `True`). Retries skipped for the core verify-and-retry contract. Tests at `tests/test_controller.py:1103` currently encode the bug as expected behavior. *Fix scheduled: Batch 2.*
2. **[open]** PLR-002 — Presets built from `light.*` groups or `group.*` helpers store targets against the group entity ID. `ensure_state()` expands to member entities first, then `_build_targets()` only looks up overrides by expanded member IDs, so group-level overrides are silently ignored. *Fix scheduled: Batch 4.*
3. **[open]** PLR-003 — `config_flow.py:806` edit flow calls `create_preset()` which always mints a new UUID; button/sensor unique IDs derive from `preset_id`, so an edit deletes old entities and creates new ones, breaking automations and dashboard references. *Fix scheduled: Batch 5.*
4. **[open]** PLR-004 — Options editor only loads `preset.targets` into `_preset_data` and refuses to save without targets, so service-created presets with preset-level `brightness_pct`/`rgb_color`/`color_temp_kelvin`/`effect` cannot round-trip through the UI. *Fix scheduled: Batch 4.*
5. **[open]** PLR-005 — Docs and UI copy call preset names unique, but neither the options flow nor `create_preset` enforces it; `find_preset()` resolves name collisions by "first match wins." *Fix scheduled: Batch 6.*
6. **[open]** RR-001 / DEP-002 / DOC-004 — Version metadata diverges across `manifest.json` (0.4.0), `pyproject.toml` (0.3.0), `package.json` (0.3.0), `uv.lock` (0.2.1). Mismatch already present on the `v0.4.0` tag. *Fix scheduled: Batch 1.*
7. **[open]** CI-001 / DEP-004 — `.github/workflows/validate.yml` uses `hacs/action@main` and `home-assistant/actions/hassfest@master`; `ci.yml` uses floating semver tags. *Fix scheduled: Batch 7.*
8. **[open]** DEP-001 / CI-002 / TEST-001 — Python deps live in shell snippets in `Makefile`/CI only; `pyproject.toml` has no `project.dependencies`; `uv.lock` contains only the editable root. *Fix scheduled: Batch 8.*
9. **[open]** OBS-001 — `diagnostics.py` returns preset names verbatim and does not use `async_redact_data`. *Fix scheduled: Batch 10.*
10. **[open]** OBS-003 — Controller computes fine-grained `VerificationResult` values (`WRONG_STATE`, `WRONG_BRIGHTNESS`, `WRONG_COLOR`, `UNAVAILABLE`, `ERROR`) but collapses them to a free-text `failed_lights: list[str]` before return; exception sites use `_LOGGER.error(..., %s)` without tracebacks. *Fix scheduled: Batch 10.*
11. **[open]** DEP-005 — `.devcontainer/devcontainer.json:4` calls `scripts/setup`, but no such file exists. *Fix scheduled: Batch 15.*
12. **[open]** DOC-001 — `CONTRIBUTING.md:30-35` says `make setup` creates a venv; `Makefile:79-91` installs into whatever interpreter is active; `scripts/verify_environment.py:139-146` looks for `venv/` while docs reference `.venv/`. Three sources disagree. *Fix scheduled: Batch 3.*
13. **[open]** DOC-002 — `USAGE.md:720-725` tells users to restart Home Assistant after creating presets, but `button.py` + `sensor.py` add preset entities via dynamic listener. *Fix scheduled: Batch 3.*
14. **[open]** DOC-003 — `USAGE.md:389-392` describes preset-button icon state switching (`mdi:lightbulb-group` ↔ `mdi:lightbulb-group-off`) but `icons.json` defines only a single static icon; `CHANGELOG.md:26-29` confirms the dynamic icon was removed. *Fix scheduled: Batch 3.*
15. **[open]** AI-003 — `CLAUDE.md` says "changes must be made on `testing`"; `CONTRIBUTING.md` says "create a feature branch, PR to `main`." Conflicting instructions. *Fix scheduled: Batch 14.*

## Architecture

Home Assistant custom integration. Single Python package under `custom_components/ha_light_controller/`.

| Layer | File | Purpose |
| --- | --- | --- |
| Entry | `__init__.py` | Service registration, `LightControllerData` runtime data |
| Core | `controller.py` | `ensure_state()` → expand → build targets → group → send → verify → retry |
| Preset | `preset_manager.py` | CRUD in `ConfigEntry.data`, activation helpers |
| Config flow | `config_flow.py` | Menu-based options: settings, add_preset, manage_presets |
| Entities | `button.py`, `sensor.py` | Per-preset button + status sensor, created dynamically via listener |
| Diagnostics | `diagnostics.py` | Config-entry diagnostics (currently summary-only, unredacted) |
| Constants | `const.py` | All `CONF_*`, `ATTR_*`, `DEFAULT_*`, `PRESET_*` |

Tests mock `homeassistant.*` in `tests/conftest.py` — no running HA instance needed, but fidelity is limited (TEST-002/003). Live testing uses Podman HA at `~/ha-plugin-test-workspace/`.

## Credentials

| Secret | OpenBao path |
| --- | --- |
| Home Assistant dev instance token | (referenced in project memory; see AI-002 re-verification task in Batch 14) |

No other secrets required by this repo.

## Gotchas

- Tests currently encode PLR-001 as expected behavior — Batch 2 must update test expectations or new regression tests will conflict with existing asserts.
- `pytest` in sandbox fails at collection without the repo's pytest plugin stack installed; Batch 8 resolves this via `uv sync --locked --group dev`.
- `package.json` advertises `test:e2e` scripts that reference `tests/e2e/playwright.config.js` — that file does not exist. Treat as dead surface (Q5 / Batch 9).
- `main` has `Auto-commit from sys76` commits from a different machine's auto-sync. Confirm with user before rebasing or force-pushing anything near main.
- Nine reviews all reuse `docs/review-orchestrator/2026-04-16-0018-codex-review-shared-research.md` — cite it rather than re-doing research during remediation.
- `docs/` is LLM-oriented only; keep batch updates terse. Human-facing narrative belongs in root `README.md`.
- `.codex/` is untracked and may contain local review-agent state; include in Batch 0 commit only if user confirms its contents are shareable.
