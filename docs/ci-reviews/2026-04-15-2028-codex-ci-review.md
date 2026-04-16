Use `superpowers:receiving-code-review`.

# CI/CD Review

## Snapshot

- Repo: `/home/chris/projects/ha-light-controller`
- Branch: `main`
- Head: `11b525c1d0139673e78daf7a68a4557d3715f0ce`
- Worktree: dirty (`?? .codex`, `?? docs/`)
- Shared research reused: `docs/review-orchestrator/2026-04-16-0018-codex-review-shared-research.md`
- Additional web research: none; shared research already covered the GitHub Actions, concurrency, dependency-review, and provenance guidance needed for this review
- Conventions input read: `docs/conventions.md`

## Pass Log

- Pass 1: workflow graph, triggers, permissions, action refs -> found `CI-001`, `CI-004`
- Pass 2: dependency bootstrap and reproducibility -> found `CI-002`
- Pass 3: local/PR operator workflow parity -> found `CI-003`
- Pass 4: package-manager and auxiliary CI surface governance -> found `CI-005`
- Pass 5: release/deploy governance and provenance follow-through -> no new issues
- Pass 6: convergence pass -> no new issues

## Findings

### CI-001

- Severity: High
- Confidence: High
- Type: supply-chain-integrity
- Where: `.github/workflows/validate.yml:19`, `.github/workflows/validate.yml:21`, `.github/workflows/validate.yml:31`, `.github/workflows/validate.yml:33`, `.github/workflows/ci.yml:18`, `.github/workflows/ci.yml:21`, `.github/workflows/ci.yml:26`, `.github/workflows/ci.yml:114`
- Issue: The workflows depend on mutable action refs instead of immutable commit SHAs. The riskiest cases are `hacs/action@main` and `home-assistant/actions/hassfest@master`, which let upstream branch changes alter push, PR, and scheduled validation behavior without any repo change. `codecov/codecov-action@v5` is also a movable third-party tag.
- Why it matters: This weakens build provenance and makes failures or compromise upstream instantly part of this repo's trusted pipeline. The nightly scheduled validate workflow amplifies that exposure.
- Recommendation: Pin every external action to a full commit SHA, then let Dependabot rotate those SHAs. Treat mutable branch refs as blockers for validation and release-facing workflows.

### CI-002

- Severity: Medium
- Confidence: High
- Type: reproducibility-and-bootstrap
- Where: `.github/workflows/ci.yml:33`, `.github/workflows/ci.yml:66`, `.github/workflows/ci.yml:99`, `.github/workflows/ci.yml:143`, `CONTRIBUTING.md:19`, `CONTRIBUTING.md:33`, `Makefile:79`
- Issue: CI bootstraps each job with floating `pip install ...` commands instead of a locked environment, even though the repo advertises UV-based setup and includes `uv.lock`. The jobs also validate dependencies directly rather than installing the project in a reproducible, repo-defined environment.
- Why it matters: A green run is tied to whatever happened to resolve from PyPI at that moment, not to a committed dependency set. That creates rerun drift, local/CI mismatch, and harder failure triage when upstream releases change behavior.
- Recommendation: Standardize on one bootstrap path for local and CI, ideally lockfile-driven (`uv sync --locked` or an equivalent committed constraints flow). Make cache keys incorporate the lockfile used by CI, not just `pyproject.toml`.

### CI-003

- Severity: Medium
- Confidence: High
- Type: workflow-drift
- Where: `Makefile:101`, `CONTRIBUTING.md:47`, `CONTRIBUTING.md:64`, `.github/pull_request_template.md:53`, `.github/pull_request_template.md:85`, `.pre-commit-config.yaml:4`, `.github/workflows/ci.yml:121`, `.github/workflows/validate.yml:12`
- Issue: The documented local preflight does not match the actual GitHub checks. `make ci` only runs Ruff, format check, mypy, and pytest, while GitHub also runs `verify-environment`, HACS validation, Hassfest validation, and the Python matrix. The PR template also requires `pre-commit run --all-files`, but CI never executes the extra file-integrity hooks from `.pre-commit-config.yaml`.
- Why it matters: Contributors can satisfy the documented local workflow and still open PRs that fail in Actions. That burns maintainer time and makes CI status less predictable than the repo documentation claims.
- Recommendation: Either make `make ci` a faithful preflight for the required GitHub checks, or explicitly split commands into `make ci-core` and `make ci-all`. If pre-commit is required in PRs, run it in CI or remove it from the mandatory checklist.

### CI-004

- Severity: Medium-Low
- Confidence: Medium-High
- Type: pipeline-reliability-and-cost
- Where: `.github/workflows/ci.yml:1`, `.github/workflows/validate.yml:1`
- Issue: Neither workflow defines `concurrency` or `cancel-in-progress`. Rapid pushes to the same PR or branch can leave stale matrix test runs and validation runs burning runner time after a newer commit is already queued.
- Why it matters: This is mostly a cost and signal-quality problem, but it also slows feedback and makes maintainers sort through failures from superseded revisions.
- Recommendation: Add per-workflow concurrency groups keyed by workflow name and ref, and enable `cancel-in-progress: true` for push/PR workflows.

### CI-005

- Severity: Low
- Confidence: Medium
- Type: auxiliary-surface-governance
- Where: `package.json:9`, `package.json:17`, `.github/dependabot.yml:1`, `.github/workflows/ci.yml:1`
- Issue: The repo carries a Node/Playwright surface (`package.json`, `package-lock.json`, `test:e2e` scripts), but CI never installs Node or runs that lane, Dependabot does not cover npm packages, and there is no `tests/e2e/` tree in the repo snapshot.
- Why it matters: This looks like stale or unmanaged test infrastructure. If anyone expects browser automation to exist, it is currently outside CI and update governance, so breakage or vulnerable JS dependency drift can go unnoticed.
- Recommendation: Either remove the dead Playwright surface, or add a real Node lane (`npm ci` + E2E execution), npm Dependabot coverage, and a committed E2E test directory.

## CI/CD Area Matrix

| Area | Status | Notes |
| --- | --- | --- |
| Pipeline graph and trigger risks | At risk | Separate `CI` and `Validate` workflows on push/PR; no concurrency controls. |
| Build, artifact, and retention integrity | Partial | Test coverage XML exists, but there is no package/build/install smoke path in CI. |
| Provenance and supply-chain integrity | At risk | Mutable action refs and floating Python bootstrap dominate the current risk. |
| Release and deploy governance | Unknown | No in-repo release/deploy workflow or environment policy was visible. |
| Runner trust and isolation | Partial | GitHub-hosted runners and mostly read-only permissions are good, but external action trust remains loose. |
| Secret and identity risks | Partial | Job permissions are scoped well; Codecov token handling is present but org/repo settings are out of band. |
| Environment promotion and recovery | Unknown | No repo-visible staging/prod promotion, rollback, or environment approval flow. |
| Pipeline reliability and cost | At risk | Duplicate bootstrap work across jobs plus missing concurrency cancellation. |
| Operator ergonomics and drift | At risk | Local docs, `make ci`, PR checklist, and GitHub-required behavior do not currently align. |

## Verified, Inferred, Unknown

- Verified from repo evidence:
  - Two GitHub Actions workflows exist: `CI` and `Validate`
  - Workflow jobs use least-privilege `contents: read` or `{}` permissions
  - Validation relies on mutable upstream refs
  - CI bootstraps Python tooling with ad hoc `pip install` commands
  - `make ci` does not cover HACS, Hassfest, pre-commit hooks, or the Python matrix
  - `package.json` and `package-lock.json` exist, but there is no repo-visible E2E directory
- Inferred:
  - Contributors are likely to hit avoidable PR failures because documented local preflight is weaker than GitHub checks
  - Rerun results can drift over time because dependency resolution is not locked
- Could not verify from repo evidence:
  - Branch protection, required checks, rulesets, SHA-pinning enforcement, Actions policy
  - Codecov repository settings
  - Release process, environment approvals, or any deployment target

## Convention Notes

- Existing conventions are concise and useful for review artifact handling.
- No convention-quality defect stood out during this review.
- Strong CI/CD convention candidates for `docs/conventions.md`:
  - All external GitHub Actions must be pinned to full commit SHAs.
  - CI dependency bootstrap must use committed lockfiles or committed constraints, not floating ad hoc install lists.
  - Any command documented as the local CI preflight must cover every required GitHub check or explicitly name what it omits.
  - Any package-manager surface kept in the repo must have both update governance and an exercised CI lane, or be removed.

## Claude Handoff

- Fix order:
  1. `CI-001`
  2. `CI-002`
  3. `CI-003`
  4. `CI-004`
  5. `CI-005`
- Suggested batching:
  - Batch A: action pinning plus concurrency (`CI-001`, `CI-004`)
  - Batch B: lockfile-driven bootstrap and cache-key cleanup (`CI-002`)
  - Batch C: local/PR parity cleanup across Makefile, contributing docs, PR template, and CI (`CI-003`)
  - Batch D: decide whether Playwright is real or dead, then either remove it or wire it into CI (`CI-005`)
- Residual risk after those fixes:
  - Release provenance, environment approvals, and required-check enforcement still need repo-settings or org-policy confirmation outside the codebase.
