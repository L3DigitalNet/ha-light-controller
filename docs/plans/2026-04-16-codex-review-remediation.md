# Codex Review Remediation Plan

- Status: 🟡 Proposed — awaiting Q1-Q9 answers before execution
- Source sweep: `docs/review-orchestrator/2026-04-16-0018-codex-review-sweep.md`
- Created: 2026-04-16
- Target branch: `testing` (per `CLAUDE.md`) — see Q1

## Open Questions (block execution until answered)

| ID | Topic | Recommendation |
| --- | --- | --- |
| Q1 | Branch strategy: `testing` exists on `origin` but not local; `main` has 5 `Auto-commit from sys76` commits since `v0.4.0` | Fetch `origin/testing`, rebase on `main`, commit batches there, PR/merge per batch |
| Q2 | Color-verify semantics (PLR-001) — pass gate when only one mode is requested | `(rgb_ok if has_rgb else True) and (kelvin_ok if has_kelvin else True)` — every requested mode must match |
| Q3 | Group-in-preset handling (PLR-002/PLR-004) | Remap overrides at activation time (preserves group-member evolution) |
| Q4 | Preset name uniqueness (PLR-005) | Enforce at service + config flow; reject duplicates |
| Q5 | Playwright / npm surface (CI-005, DEP-003, TEST-005, AI-005, RR-004) | Delete `package.json`, `package-lock.json`, Playwright deps, `test:e2e*` scripts |
| Q6 | Test-harness fidelity (TEST-002/003) | Thin slice now (setup+unload, one `ensure_state`, one config flow); defer bulk via follow-up plan |
| Q7 | Coverage gate (TEST-006, RR-004) | Add `--cov-fail-under=95` in CI |
| Q8 | `.claude/settings.json` cross-repo read (AI-001) | Move to `.claude/settings.local.json` |
| Q9 | `CLAUDE.md` credentialed HA instance instructions (AI-002) | Re-verify against current `CLAUDE.md`; move any such content to `CLAUDE.local.md` |

## Finding → Batch Map

| Finding | Source review | Batch |
| --- | --- | --- |
| PLR-001 | product-logic | 2 |
| PLR-002, PLR-004 | product-logic | 4 |
| PLR-003 | product-logic | 5 |
| PLR-005 | product-logic | 6 |
| DOC-001 | documentation | 3 |
| DOC-002 | documentation | 3 |
| DOC-003 | documentation | 3 |
| DOC-004 | documentation | 1 |
| DOC-005 | documentation | 3 |
| DOC-006 | documentation | 11 |
| RR-001 | release-readiness | 1 |
| RR-002 | release-readiness | 7 |
| RR-003 | release-readiness | 11 |
| RR-004 | release-readiness | 9 (npm) + 12 (coverage gate) |
| RR-005 | release-readiness | 12 |
| CI-001 | ci-cd | 7 |
| CI-002 | ci-cd | 8 |
| CI-003 | ci-cd | 11 (Makefile/PR template parity) |
| CI-004 | ci-cd | 7 |
| CI-005 | ci-cd | 9 |
| DEP-001 | dependency | 8 |
| DEP-002 | dependency | 1 |
| DEP-003 | dependency | 9 |
| DEP-004 | dependency | 7 |
| DEP-005 | dependency | 15 |
| TEST-001 | test-suite | 8 |
| TEST-002 | test-suite | 13 |
| TEST-003 | test-suite | 13 |
| TEST-004 | test-suite | 13 follow-up plan |
| TEST-005 | test-suite | 9 |
| TEST-006 | test-suite | 12 |
| OBS-001 | observability | 10 |
| OBS-002 | observability | 10 |
| OBS-003 | observability | 10 |
| OBS-004 | observability | 3 |
| OBS-005 | observability | 12 |
| IR-001 | incident-readiness | 11 |
| IR-002 | incident-readiness | 10 |
| IR-003 | incident-readiness | 10 |
| IR-004 | incident-readiness | 7 |
| IR-005 | incident-readiness | 12 |
| AI-001 | ai-workflow | 14 |
| AI-002 | ai-workflow | 14 |
| AI-003 | ai-workflow | 14 |
| AI-004 | ai-workflow | 14 |
| AI-005 | ai-workflow | 9 |

## Batches

### Batch 0 — Branch setup + persist review trail

- Fetch `origin/testing`, check out, rebase on `main`
- Commit untracked review artifacts (`docs/review-orchestrator/`, `docs/*-reviews/`, `docs/plans/`, `.codex/` if relevant)
- Risk: none (docs only)

### Batch 1 — Version truth

- Covers: RR-001, DOC-004, DEP-002
- Set `pyproject.toml`, `package.json`, `uv.lock` to `0.4.0` (match `manifest.json` + `CHANGELOG.md`)
- Add `scripts/check_versions.py`; call from `make ci`
- Risk: near-zero; unblocks release

### Batch 2 — Color-verify bug

- Covers: PLR-001
- Fix `controller.py:469-474` per Q2
- Update `tests/test_controller.py:1103` expectations (tests currently encode the bug)
- Add regressions: RGB-only mismatch → `WRONG_COLOR`, Kelvin-only mismatch → `WRONG_COLOR`
- Risk: low; contained to one function

### Batch 3 — Docs drift sweep

- Covers: DOC-001, DOC-002, DOC-003, DOC-005, OBS-004
- Align `make setup` ↔ `CONTRIBUTING.md` ↔ `scripts/verify_environment.py` on one venv path
- Replace "restart HA" preset advice in `USAGE.md:720-725` with listener-verification steps
- Update `USAGE.md:389-392` preset-button icon to match current `icons.json`
- Add "Collect diagnostics" subsection to `USAGE.md`; link from `README.md`
- Risk: docs only; `scripts/verify_links.py` guards

### Batch 4 — Preset data-model fixes

- Covers: PLR-002, PLR-004
- Implement group-remap-at-activation per Q3 in `controller.py` + `preset_manager.py`
- Teach options editor (`config_flow.py`) to load/save preset-level `brightness_pct`/`rgb_color`/`color_temp_kelvin`/`effect`
- Tests: group-based preset activation end-to-end; service-created preset round-trip through editor
- Risk: medium; multi-file

### Batch 5 — Preset identity on edit

- Covers: PLR-003
- Replace delete-and-recreate at `config_flow.py:806` with true update path preserving `preset_id`
- Add entity-registry stability test for edit
- Risk: medium; entity lifecycle

### Batch 6 — Preset name uniqueness

- Covers: PLR-005
- Enforce case-insensitive uniqueness in `create_preset` service + config flow create/edit
- Reject duplicates with `vol.Invalid` + clear message
- Tests for duplicate rejection
- Risk: low

### Batch 7 — Supply-chain pinning + concurrency

- Covers: CI-001, CI-004, DEP-004, RR-002, IR-004
- Pin every Action to full commit SHA with trailing `# v5.x` comment
- Add `concurrency: {group: ${{ github.workflow }}-${{ github.ref }}, cancel-in-progress: true}` to both workflows
- Ensure Dependabot `github-actions` entry rotates SHAs
- Risk: low; CI-only

### Batch 8 — Authoritative dep inventory

- Covers: CI-002, DEP-001, TEST-001
- Move runtime + test + dev deps into `pyproject.toml` `[project.dependencies]` + `[dependency-groups.dev]`
- Regenerate `uv.lock`
- Rewrite CI + Makefile to `uv sync --locked --group dev`; drop ad hoc `pip install` lists
- Cache key → lockfile hash
- Risk: medium-high; sequenced after Batch 7 so runs are deterministic

### Batch 9 — Dead npm surface removal

- Covers: CI-005, DEP-003, TEST-005, AI-005, RR-004 (E2E part)
- Delete `package.json`, `package-lock.json`, any npm Dependabot, Playwright references
- Strip `test:e2e*` from docs
- Risk: low per Q5

### Batch 10 — Diagnostics + supportability

- Covers: OBS-001, OBS-002, OBS-003, IR-002, IR-003
- `diagnostics.py`: adopt `async_redact_data` with named redaction policy; add redacted runtime-status summary
- `controller.py`: preserve per-light `VerificationResult` in `OperationResult`; switch core `except` to `_LOGGER.exception`
- Add `system_health.py`
- Tests for redaction, runtime summary, `caplog` assertions
- Risk: medium; changes result payload shape — update service docs + tests together

### Batch 11 — Runbooks + local/CI parity

- Covers: IR-001, DOC-006, RR-003, CI-003
- New `docs/runbooks/incident-disablement.md` — containment, evidence capture, fallback to native `light.turn_*`, rollback verification
- New `docs/runbooks/release.md` — version bump order, validation expectations, HACS/Hassfest failure triage, rollback
- Align `make ci` with actual GitHub required checks (or split `make ci-core`/`make ci-all`); reconcile `.github/pull_request_template.md`
- Link both runbooks from `README.md` + `CONTRIBUTING.md`
- Risk: docs + Makefile targets only

### Batch 12 — Coverage gate + conventions + quality scale

- Covers: TEST-006, RR-004 (coverage part), RR-005, IR-005, OBS-005
- Add `--cov-fail-under=95` per Q7
- Reassess `quality_scale.yaml` `repair-issues` exemption
- Add to `docs/conventions.md` (six-field schema):
  - `conv-release-001` version-sync-before-tag
  - `conv-release-002` actions-pinned-to-SHA
  - `conv-release-003` authoritative-dep-inventory
  - `conv-obs-001` diagnostics-must-redact
  - `conv-ops-001` runbook-on-user-visible-failure
- Risk: low

### Batch 13 — Test-harness thin slice

- Covers: TEST-002, TEST-003 (partial)
- Add `tests/integration/` with `pytest-homeassistant-custom-component` harness
- Three harness tests: setup+unload, `ensure_state` end-to-end, config-flow happy path
- `@pytest.mark.integration`; wire marker into CI (non-blocking initially)
- Write follow-up plan `docs/plans/<date>-test-harness-migration.md` for TEST-004 rebalance + ~300-test migration
- Risk: medium but isolated; existing mocks stay

### Batch 14 — AI/prompt hygiene

- Covers: AI-001, AI-002, AI-003, AI-004
- Move `.claude/settings.json` cross-repo read to `.claude/settings.local.json` per Q8
- Re-verify `CLAUDE.md` credentialed-HA references against reviewer line numbers; relocate per Q9
- Reconcile CONTRIBUTING.md branch workflow with CLAUDE.md `testing` rule (see Q1)
- Clean up stale AI-artifact claims in `.gitignore` (lines 210-239)
- Risk: low; meta-only

### Batch 15 — Misc bootstrap hygiene

- Covers: DEP-005
- Create or remove `scripts/setup` (referenced by `.devcontainer/devcontainer.json:4`)
- Decide ownership for pre-commit mypy hook extra deps
- Risk: low

## Dependency Graph

```
0 → 1 → 2 → 3 → 4 → 5 → 6
            ↓
7 → 8 → 9
        ↓
       10 → 12
       ↓
       13
11 (independent)
14 (independent)
15 (independent)
```

## Suggested Scopes

- **Fast ship-ready (0.4.1):** Batches 0, 1, 2, 3, 7 (~5 commits, no risky surgery)
- **Correctness-complete:** add Batches 4, 5, 6, 10 (product-logic + diagnostics)
- **Full sweep:** all 16 batches (≈ 2-4 focused sessions)

## Execution Notes

- Each batch = one logical commit on `testing`; surface for review before proceeding
- After each batch: run `make ci`, `python scripts/verify_links.py`, and (post-Batch 8) `uv sync --locked --group dev`
- Log every merged-to-main batch as a new bug-fixed row under `docs/handoff.md` "Bugs Found and Fixed"
- If any batch fails CI, fix root cause — do not bypass hooks per global instructions
