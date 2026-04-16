# Conventions

## Quick Reference

| ID | Applies-when | Rule |
| --- | --- | --- |
| `conv-docs-001` | Editing `docs/` | Keep docs concise, scannable, and LLM-oriented. |
| `conv-review-001` | Running repo reviews | Save new timestamped review artifacts; do not overwrite prior runs. |
| `conv-review-002` | Running orchestrator sweeps | Use `review-orchestrator`; persist artifacts under `docs/review-orchestrator/`. |
| `conv-python-001` | Editing Python | Preserve strict typing and Ruff/Mypy compatibility from `pyproject.toml`. |
| `conv-ha-001` | Editing integration code | Keep Home Assistant integration logic inside `custom_components/ha_light_controller/`. |
| `conv-release-001` | Bumping version | Update all version-bearing files; run `scripts/check_versions.py`. |
| `conv-release-002` | Modifying CI actions | Pin every GitHub Action to a full commit SHA with version comment. |
| `conv-release-003` | Adding/removing deps | All deps in `pyproject.toml`; regenerate `uv.lock`; no ad hoc pip install. |
| `conv-obs-001` | Touching diagnostics | Redact PII (names, entity IDs) via `TO_REDACT`; include runtime status. |
| `conv-ops-001` | Adding user-visible failure mode | Document containment + rollback in `docs/runbooks/`. |

## Convention: `conv-docs-001`

- Applies-when: creating or editing files under `docs/`
- Rule: write for LLM consumption; prefer short sections and compact bullets over narrative prose
- Code: `docs/*.md`
- Why: repo-level AGENTS instructions require `docs/` to be token-efficient and machine-friendly
- Sources: `AGENTS.md`
- Related: `conv-review-001`, `conv-review-002`

## Convention: `conv-review-001`

- Applies-when: saving any review artifact
- Rule: create a new timestamped Markdown file in the review-specific `docs/` subdirectory; do not overwrite previous reports
- Code: `docs/*-reviews/`, `docs/review-orchestrator/`
- Why: preserves review history and matches repo automation expectations
- Sources: `AGENTS.md`
- Related: `conv-docs-001`, `conv-review-002`

## Convention: `conv-review-002`

- Applies-when: the user asks for a review planning scan or review sweep
- Rule: use the `review-orchestrator` workflow first and rely on its deterministic helper scripts when available
- Code: `docs/review-orchestrator/`
- Why: repo instructions explicitly prefer the orchestrator for cross-review planning and sweeps
- Sources: `AGENTS.md`, `~/.agents/skills/review-orchestrator/SKILL.md`
- Related: `conv-review-001`

## Convention: `conv-python-001`

- Applies-when: modifying Python application or test code
- Rule: keep code compatible with the repo's Ruff and strict Mypy settings unless the user requests a convention change
- Code: `pyproject.toml`, `mypy.ini`, `custom_components/**/*.py`, `tests/**/*.py`
- Why: the repo already enforces a strong static-analysis baseline
- Sources: `pyproject.toml`, `mypy.ini`
- Related: `conv-ha-001`

## Convention: `conv-ha-001`

- Applies-when: changing feature logic for the Home Assistant integration
- Rule: keep Home Assistant integration surfaces organized under `custom_components/ha_light_controller/` and use tests under `tests/` as the verification layer
- Code: `custom_components/ha_light_controller/`, `tests/`
- Why: repo structure and package metadata indicate standard Home Assistant custom component layout
- Sources: `README.md`, `pyproject.toml`
- Related: `conv-python-001`

## Convention: `conv-release-001`

- Applies-when: bumping the integration version for a release
- Rule: update `manifest.json`, `pyproject.toml`, `CHANGELOG.md` in one commit; run `uv lock` and `scripts/check_versions.py` before tagging
- Code: `scripts/check_versions.py`
- Why: version drift across 3+ files caused silent mismatch between v0.3.0 and v0.4.0 (RR-001, DEP-002, DOC-004)
- Sources: `docs/runbooks/release.md`
- Related: `conv-release-003`

## Convention: `conv-release-002`

- Applies-when: adding or updating GitHub Actions in `.github/workflows/`
- Rule: pin every action to a full commit SHA with a trailing `# vX.Y.Z` comment; rely on Dependabot `github-actions` ecosystem for rotation
- Code: `.github/workflows/*.yml`, `.github/dependabot.yml`
- Why: mutable tags (`@main`, `@v6`) are a supply-chain risk; Dependabot handles SHA rotation automatically (CI-001, DEP-004)
- Sources: GitHub Security Hardening Guide
- Related: `conv-release-001`

## Convention: `conv-release-003`

- Applies-when: adding, removing, or upgrading a Python dependency
- Rule: declare in `pyproject.toml` `[dependency-groups.dev]`; run `uv lock`; never add ad hoc `pip install` lines to CI or Makefile
- Code: `pyproject.toml`, `uv.lock`
- Why: ad hoc pip install lists in CI diverged from Makefile and docs (DEP-001, CI-002)
- Sources: uv docs
- Related: `conv-release-001`

## Convention: `conv-obs-001`

- Applies-when: modifying `diagnostics.py` or adding diagnostic data
- Rule: redact preset names and entity IDs using `TO_REDACT`; include runtime preset status
- Code: `custom_components/ha_light_controller/diagnostics.py`
- Why: preset names reveal room layout (PII-adjacent); raw entity IDs expose home topology (OBS-001)
- Sources: HA diagnostics docs
- Related: `conv-ha-001`

## Convention: `conv-ops-001`

- Applies-when: introducing a new user-visible failure mode
- Rule: document containment, evidence capture, fallback, and rollback steps in `docs/runbooks/`
- Code: `docs/runbooks/*.md`
- Why: incident-readiness review (IR-001) found no documented rollback or containment path
- Sources: `docs/runbooks/incident-disablement.md`
- Related: `conv-release-001`
