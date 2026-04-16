Claude Code should use the `superpowers:receiving-code-review` skill before applying fixes.

# Release Readiness Review

## Snapshot

- verdict: `not release-ready`
- repo: `/home/chris/projects/ha-light-controller`
- branch: `main`
- commit: `11b525c1d0139673e78daf7a68a4557d3715f0ce`
- worktree: `dirty` (`?? .codex`, `?? docs/`)
- handoff: [docs/handoff.md](/home/chris/projects/ha-light-controller/docs/handoff.md:1)
- conventions: [docs/conventions.md](/home/chris/projects/ha-light-controller/docs/conventions.md:1)
- shared research reused: [docs/review-orchestrator/2026-04-16-0018-codex-review-shared-research.md](/home/chris/projects/ha-light-controller/docs/review-orchestrator/2026-04-16-0018-codex-review-shared-research.md:1)
- additional web research: none; the shared research pack already covered the release-relevant HA, GitHub Actions, PyPI, and testing guidance used here

## Passes

1. Artifact and version integrity
2. CI, validation, and provenance posture
3. Release workflow, rollback, and operator guidance
4. Quality signals, smoke coverage, and test evidence
5. Convergence pass: no new issues
6. Convergence pass: no new issues

## Top Findings

### RR-001

- severity: `high`
- confidence: `high`
- type: `version-integrity`
- summary: Release metadata is internally inconsistent. The integration manifest says `0.4.0`, but the Python and Node package metadata still say `0.3.0`.
- evidence:
  - [custom_components/ha_light_controller/manifest.json](/home/chris/projects/ha-light-controller/custom_components/ha_light_controller/manifest.json:1) sets `"version": "0.4.0"` at line 17.
  - [pyproject.toml](/home/chris/projects/ha-light-controller/pyproject.toml:1) still sets `version = "0.3.0"` at line 3.
  - [package.json](/home/chris/projects/ha-light-controller/package.json:1) still sets `"version": "0.3.0"` at line 3.
  - [CHANGELOG.md](/home/chris/projects/ha-light-controller/CHANGELOG.md:8) records `0.4.0` as the latest release.
  - `git show v0.4.0:...` confirms the same mismatch already existed on the `v0.4.0` tag, so this is not just unreleased drift.
- why it matters: Any release automation, package build, downstream tooling, or human operator reading project metadata can identify the same codebase as two different versions. That is a direct release-integrity failure.
- release impact: Blocker. Do not cut another release until every version-bearing surface is synchronized and checked before tagging.

### RR-002

- severity: `medium`
- confidence: `high`
- type: `provenance-and-ci-integrity`
- summary: Release-affecting validation depends on mutable upstream branch heads.
- evidence:
  - [validate.yml](/home/chris/projects/ha-light-controller/.github/workflows/validate.yml:13) uses `hacs/action@main` at lines 13-23.
  - [validate.yml](/home/chris/projects/ha-light-controller/.github/workflows/validate.yml:25) uses `home-assistant/actions/hassfest@master` at lines 25-33.
  - Shared research reused here links GitHub’s current hardening guidance recommending pinning actions to immutable SHAs for higher trust.
- why it matters: A release can start failing, passing, or behaving differently without any repo change. In the worst case, the repo executes compromised upstream workflow code in its release gate.
- release impact: Not an immediate functional blocker for one manual release, but it materially weakens trust in the validation surface that should protect releases.

### RR-003

- severity: `medium`
- confidence: `high`
- type: `release-governance`
- summary: The repo has no in-repo release workflow, no release checklist, and no rollback or post-release verification runbook.
- evidence:
  - `.github/workflows/` contains only `ci.yml` and `validate.yml`; there is no publish, tag, release, smoke, or rollback workflow in-repo.
  - [CONTRIBUTING.md](/home/chris/projects/ha-light-controller/CONTRIBUTING.md:58) covers PR hygiene at lines 58-64 but provides no release procedure.
  - Repo searches found no release checklist, rollback procedure, or post-release verification steps outside the changelog history.
  - The version drift in RR-001 is exactly the kind of error a release checklist should prevent.
- why it matters: Releases are currently dependent on undocumented operator memory. That makes version sync, tag creation, HACS/GitHub release publication, and rollback handling error-prone and hard to audit.
- release impact: Medium blocker for repeatable shipping. Even if a release can be pushed manually, the repo does not contain the controls needed to do it safely and consistently.

### RR-004

- severity: `medium`
- confidence: `high`
- type: `quality-signal-gap`
- summary: The repo advertises strong test coverage, but CI does not enforce a minimum coverage floor and the only E2E hook in `package.json` points to missing files.
- evidence:
  - [ci.yml](/home/chris/projects/ha-light-controller/.github/workflows/ci.yml:105) runs coverage reporting at lines 105-119 but never uses `--cov-fail-under` or any equivalent gate.
  - [quality_scale.yaml](/home/chris/projects/ha-light-controller/custom_components/ha_light_controller/quality_scale.yaml:113) claims `315 tests at 98%+ branch coverage`, but that claim is not enforced by CI.
  - [package.json](/home/chris/projects/ha-light-controller/package.json:9) defines `test:e2e` and `test:e2e:headed` at lines 9-19, but `tests/e2e/playwright.config.js` and `tests/e2e/` do not exist in the repo.
- why it matters: The release decision currently relies on unenforced quality claims and a stale smoke-test surface. If coverage regresses or install/runtime behavior breaks, the release gate will not necessarily stop it.
- release impact: Medium. This does not prove the current code is broken, but it does mean the repo lacks a trustworthy automated signal for “safe to ship.”

### RR-005

- severity: `low`
- confidence: `high`
- type: `convention-quality`
- summary: The conventions file is too thin to govern release safety. It has no rule for version synchronization, release checklists, rollback expectations, or immutable action pinning.
- evidence:
  - [docs/conventions.md](/home/chris/projects/ha-light-controller/docs/conventions.md:5) only defines doc, review, Python, and HA layout conventions at lines 5-56.
  - There is no release-specific convention to prevent RR-001 through RR-004.
- why it matters: Repo reviews are being asked to enforce release quality, but the local convention set does not encode the most important release rules for future contributors or agents.
- release impact: Low by itself, but it leaves repeated release mistakes ungoverned.

## Release Readiness Matrix

| Area | Status | Notes |
| --- | --- | --- |
| Version and artifact integrity | `red` | RR-001 |
| CI and validation coverage | `yellow` | CI exists, but provenance and gating are weak; RR-002, RR-004 |
| Release automation and governance | `red` | No release workflow or runbook; RR-003 |
| Rollback and recovery guidance | `red` | No documented rollback or post-release verification path; RR-003 |
| Test and quality confidence | `yellow` | Large unit/integration suite exists, but release gating is incomplete; RR-004 |
| Provenance and supply-chain trust | `yellow` | Mutable workflow refs in validation jobs; RR-002 |

## Verified / Inferred / Unverified

### Verified from repo evidence

- The repo has CI and validation workflows, but no release workflow.
- The latest tagged release is `v0.4.0`, while `HEAD` is several commits ahead and not tagged.
- Version metadata is inconsistent across manifest, changelog, `pyproject.toml`, and `package.json`.
- There are 316 test functions in `tests/`.
- The advertised Playwright E2E script path does not exist in the repo.

### Inferred

- GitHub Releases or HACS publication are likely manual today, because no in-repo automation or checklist documents them.
- RR-001 has probably already affected at least one shipped release because the mismatch exists on the `v0.4.0` tag.

### Could not verify from repo alone

- Branch protection, required checks, environment approvals, and release permissions
- Whether GitHub Releases are created from source archives only or from additional built artifacts
- Any external post-release smoke testing in a real Home Assistant environment
- Any out-of-band rollback checklist or operator playbook

## Verification Notes

- I attempted a local `pytest tests/ -q` rerun in the sandbox. It did not complete meaningfully because the current environment lacks the repo’s expected pytest async/Home Assistant plugin stack, leading to `Unknown config option: asyncio_default_fixture_loop_scope` and missing `asyncio` marker registration before real test execution. That is a sandbox limitation for this review, not direct proof of a repo defect, so I did not turn it into a finding.

## Proposed Convention Candidates

- `conv-release-001`: Before tagging or publishing, all version-bearing files must match: `custom_components/.../manifest.json`, `pyproject.toml`, `package.json` if retained, and `CHANGELOG.md`.
- `conv-release-002`: Every release must follow a checked-in checklist covering validation, tag creation, publish steps, rollback path, and post-release verification.
- `conv-release-003`: Release-affecting GitHub Actions must pin third-party actions to immutable SHAs; branch refs like `@main` and `@master` are disallowed.
- `conv-release-004`: The release gate must enforce at least one measurable runtime-confidence signal, such as a coverage floor, install smoke test, or Home Assistant integration smoke workflow.

## Fix Order

1. Fix RR-001 first. Synchronize version metadata and add a pre-release check so this cannot recur.
2. Fix RR-003 next. Add a release checklist or workflow with explicit publish, rollback, and post-release verification steps.
3. Fix RR-002 in the same batch as RR-003. Immutable action pinning belongs in the release-governance hardening pass.
4. Fix RR-004 after the release path is defined. Decide whether to enforce coverage, add install smoke tests, or remove dead E2E hooks.
5. Fold RR-005 into the same PR series by updating `docs/conventions.md` once the release rules are settled.

## Claude Handoff

- Recommended batching:
  - Batch A: version sync + automated version consistency check
  - Batch B: release runbook/workflow + immutable action pinning
  - Batch C: quality gate hardening + cleanup of dead E2E hooks
  - Batch D: conventions update
- Suggested first implementation target: add a single source of truth for the release version and fail CI if any mirrored metadata drifts.
- Residual risk after Batch A only: releases will still be manual and weakly governed until Batch B lands.
