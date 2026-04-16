Claude should use the `superpowers:receiving-code-review` skill before acting on this report.

# Documentation And Runbook Review

## Repo Snapshot

- repo: `/home/chris/projects/ha-light-controller`
- branch: `main`
- commit: `11b525c1d0139673e78daf7a68a4557d3715f0ce`
- worktree: `dirty`
- dirty_details:
  - `?? .codex`
  - `?? docs/`
- generated_at: `2026-04-15 20:29 EDT`
- reviewer: `Codex`
- review_type: `documentation-and-runbook-review`

## Scope And Inputs

- primary docs reviewed:
  - `README.md`
  - `USAGE.md`
  - `CONTRIBUTING.md`
  - `SECURITY.md`
  - `CHANGELOG.md`
  - `info.md`
- repo evidence cross-checked:
  - `Makefile`
  - `pyproject.toml`
  - `package.json`
  - `.github/workflows/ci.yml`
  - `.github/workflows/validate.yml`
  - `custom_components/ha_light_controller/manifest.json`
  - `custom_components/ha_light_controller/services.yaml`
  - `custom_components/ha_light_controller/button.py`
  - `custom_components/ha_light_controller/sensor.py`
  - `custom_components/ha_light_controller/diagnostics.py`
- conventions input:
  - `docs/conventions.md`
- shared research reused:
  - `docs/review-orchestrator/2026-04-16-0018-codex-review-shared-research.md`
- additional internet research:
  - none; the shared research artifact already covered the Home Assistant docs/troubleshooting guidance needed for this review

## Review Passes

1. Entry docs and onboarding flow
2. Feature/reference docs vs service schemas and entity behavior
3. Troubleshooting, diagnostics, and support guidance
4. Maintainer workflows, release/validation surfaces, and freshness drift
5. Executable-doc checks via `scripts/verify_links.py`
6. Convergence pass for new issues: no new issues

## Findings

### DOC-001

- severity: `high`
- confidence: `high`
- issue_type: `setup/onboarding drift`
- summary: Contributor setup instructions are not executable as written and can push contributors into the wrong Python environment.
- evidence:
  - `CONTRIBUTING.md:30-35` says `make setup` "Creates venv and installs dependencies" and then tells contributors to run `source .venv/bin/activate`.
  - `Makefile:79-91` never creates a virtual environment; it installs directly with `pip` into the currently active interpreter and only installs pre-commit hooks.
  - `scripts/verify_environment.py:139-146` looks for `venv/`, not `.venv/`, so the repo’s own verification path disagrees with the contributor docs.
- why_it_matters: A new contributor following the docs can end up with a global install, a missing activation target, or a false sense that the environment is isolated. This is the highest-friction path in the repo and directly affects onboarding success.
- recommendation:
  - pick one canonical environment story (`uv venv .venv`, `python -m venv .venv`, or "use an already-activated env")
  - make `make setup` match that story
  - make `CONTRIBUTING.md`, `Makefile`, and `scripts/verify_environment.py` agree on the same path and behavior

### DOC-002

- severity: `medium`
- confidence: `high`
- issue_type: `troubleshooting inaccuracy`
- summary: The troubleshooting guide tells users to restart Home Assistant after creating presets, but the integration is implemented to add preset entities dynamically.
- evidence:
  - `USAGE.md:720-725` says preset issues can be resolved by restarting Home Assistant after creating presets via the options flow.
  - `custom_components/ha_light_controller/button.py:29-71` dynamically adds new preset button entities through a listener.
  - `custom_components/ha_light_controller/sensor.py:30-70` does the same for preset status sensors.
- why_it_matters: This advice sends users toward a slow, unnecessary recovery step and can hide the real failure mode if listener-based entity creation is actually broken. It also weakens trust in the troubleshooting section.
- recommendation:
  - replace the restart advice with steps that reflect current behavior: verify entity registry visibility, inspect integration logs, and re-open the options flow or reload the config entry if dynamic entity creation fails

### DOC-003

- severity: `medium`
- confidence: `high`
- issue_type: `docs-to-code drift`
- summary: The preset button icon behavior documented in `USAGE.md` is stale and contradicts the current implementation.
- evidence:
  - `USAGE.md:389-392` says the preset button icon changes between `mdi:lightbulb-group` and `mdi:lightbulb-group-off` based on target state.
  - `CHANGELOG.md:26-29` says the dynamic `icon` property was removed from `PresetButton`.
  - `custom_components/ha_light_controller/icons.json:3-6` defines only a single default button icon, not state-specific button icons.
- why_it_matters: This is small user-facing drift, but it is exactly the kind of detail that makes reference docs feel untrustworthy once a user notices the UI does not match the guide.
- recommendation:
  - update the preset-entity section to describe the current icon behavior
  - if state-based icons are intended long-term, add a note that only the status sensor is stateful today

### DOC-004

- severity: `medium`
- confidence: `high`
- issue_type: `freshness/version drift`
- summary: The repo presents conflicting release and runtime baselines across its docs and machine-readable metadata.
- evidence:
  - `CHANGELOG.md:8-31` documents a `0.4.0` release.
  - `custom_components/ha_light_controller/manifest.json:17` reports version `0.4.0`.
  - `pyproject.toml:3` still reports version `0.3.0`.
  - `package.json:3` still reports version `0.3.0`.
  - `CONTRIBUTING.md:19` says Python `3.13+`.
  - `CHANGELOG.md:86-87` says the Python requirement was updated to `3.14.2` / Home Assistant `2025.2.0+`.
  - `pyproject.toml:5` still says `>=3.13`, while `pyproject.toml:35` pins mypy analysis to `3.14`.
- why_it_matters: Readers cannot tell which version is current, what release the docs correspond to, or which Python baseline is actually supported. That hurts user confidence and makes support triage harder.
- recommendation:
  - establish a single release/version source of truth
  - align `CHANGELOG.md`, `manifest.json`, `pyproject.toml`, `package.json`, and contributor-facing runtime requirements in one update

### DOC-005

- severity: `medium`
- confidence: `medium`
- issue_type: `support/runbook gap`
- summary: The docs do not teach users or maintainers how to collect diagnostics, even though diagnostics support is implemented and already called out as a shipped feature.
- evidence:
  - `custom_components/ha_light_controller/diagnostics.py:13-33` exposes config-entry diagnostics.
  - `CHANGELOG.md:10-13` highlights diagnostics support as a notable feature.
  - `README.md:127-130` sends users to `USAGE.md` for the operational docs, but `USAGE.md:689-740` troubleshooting guidance never mentions collecting diagnostics for bug reports.
- why_it_matters: Home Assistant support flows rely on diagnostics exports for reproducible issue reports. Omitting that path means users are pushed toward screenshots and logs instead of the structured artifact the integration already provides.
- recommendation:
  - add a short "Collect diagnostics" subsection to `USAGE.md` troubleshooting
  - link that from `README.md` and optionally from the issue template/docs path

### DOC-006

- severity: `medium`
- confidence: `medium`
- issue_type: `maintainer runbook gap`
- summary: The repo has CI and validation workflows, but no maintainer-facing release/validation runbook that explains how to use them before shipping.
- evidence:
  - `.github/workflows/ci.yml:10-169` defines lint, type-check, test, environment verification, and coverage upload.
  - `.github/workflows/validate.yml:12-33` defines HACS and Hassfest validation.
  - `CONTRIBUTING.md:37-56` documents developer checks but stops at local quality commands; there is no release checklist, validation runbook, or "before tagging/releasing" section.
- why_it_matters: This repo ships a Home Assistant custom integration with repo-specific validation surfaces. Without a maintainer runbook, release quality depends on tribal knowledge instead of a reproducible checklist.
- recommendation:
  - add a short maintainer section covering local preflight, CI/validation expectations, changelog/version bump order, and where to look when HACS/Hassfest fails

## Documentation Area Matrix

| Area | Status | Notes |
| --- | --- | --- |
| Repo entrypoint / README | `amber` | Good feature overview and install path, but version freshness and support-path links are thin. |
| Setup / onboarding | `red` | Contributor setup instructions conflict with actual automation and environment checks. |
| Usage / reference docs | `amber` | Broad service coverage is strong; a few behavior details have drifted from implementation. |
| Troubleshooting / support | `red` | Concrete steps exist, but at least one recovery step is wrong and diagnostics are undocumented. |
| Maintainer runbooks | `red` | No release/validation runbook despite non-trivial CI + HACS/Hassfest surfaces. |
| Freshness / ownership | `red` | Version and runtime baselines disagree across docs and metadata. |
| ADR / decision history | `gray` | No ADR surface found; not a blocker for users, but decision history is thin. |
| Executable documentation | `amber` | `scripts/verify_links.py` passes for internal/anchor links, but there is no doc smoke test for command examples or setup flows. |

## Verified vs Inferred

- verified from repo evidence:
  - onboarding/setup mismatch
  - dynamic preset entity creation behavior
  - current icon behavior
  - diagnostics surface exists
  - CI/HACS/Hassfest workflows exist
  - internal and anchor links pass `scripts/verify_links.py`
- inferred but strongly supported:
  - users and maintainers will take longer to troubleshoot because diagnostics collection is undocumented
  - release handling likely depends on tribal knowledge because no runbook is present
- not verified from repo evidence:
  - GitHub release/tag workflow outside the repo
  - actual published package metadata on external registries
  - branch protection, required checks, and release governance in repo settings

## Convention Alignment

- `conv-docs-001`: partly met
  - docs are concise and scannable overall
  - truthfulness/freshness drift is the main convention miss, not verbosity
- convention-quality issues found:
  - none in `docs/conventions.md`; the conventions are minimal but internally consistent

## Executable-Doc Checks

- command run: `python scripts/verify_links.py`
- result: pass
- notes:
  - internal links: `0` broken
  - anchor links: `0` broken
  - external links were only enumerated, not fully live-checked by the script

## Proposed Convention Candidates

- Add a doc convention that every contributor command shown in `CONTRIBUTING.md` must be backed by a real automation target or an explicit "manual" note.
- Add a doc convention that release version values must be updated atomically across `manifest.json`, packaging metadata, and `CHANGELOG.md`.
- Add a doc convention that every troubleshooting guide should include the project’s canonical support artifact path when one exists (here: Home Assistant diagnostics export).
- Add a doc convention that repos with CI validation beyond basic tests must include a minimal maintainer release/validation checklist.

## Claude Handoff

- recommended fix order:
  1. Fix `DOC-001` first because it blocks contributors immediately.
  2. Fix `DOC-004` next so every other doc update lands against a single truthful version/runtime baseline.
  3. Fix `DOC-002` and `DOC-005` together as one troubleshooting/support pass.
  4. Fix `DOC-003` as a small reference-doc cleanup.
  5. Add the maintainer runbook from `DOC-006`.
- batching guidance:
  - batch A: onboarding + version baseline (`DOC-001`, `DOC-004`)
  - batch B: user support docs (`DOC-002`, `DOC-003`, `DOC-005`)
  - batch C: maintainer release/validation runbook (`DOC-006`)
- low-risk verification after fixes:
  - rerun `python scripts/verify_links.py`
  - sanity-check every documented command against `Makefile`
  - sanity-check user-facing behavior claims against `services.yaml`, `icons.json`, and entity platform code
