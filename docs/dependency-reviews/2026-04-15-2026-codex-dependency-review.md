# Dependency Supply-Chain Review

Claude: use the `superpowers:receiving-code-review` skill before acting on this report.

## Snapshot

- repo: `/home/chris/projects/ha-light-controller`
- branch: `main`
- head: `11b525c1d0139673e78daf7a68a4557d3715f0ce`
- worktree: dirty (`.codex`, `docs/`)
- generated_at: `2026-04-15 20:26:21 EDT`
- review_type: `dependency-supply-chain-review`
- shared_research_reused: `docs/review-orchestrator/2026-04-16-0018-codex-review-shared-research.md`
- targeted_follow_up_research:
  - `uv` dependency declaration guidance
  - GitHub Dependabot supported ecosystems guidance

## Evidence Boundary

- Verified from repo: Python, npm, GitHub Actions, pre-commit, and devcontainer dependency surfaces.
- Verified from official docs: GitHub still recommends SHA-pinning Actions; Dependabot supports `pip`/PEP 621 manifests and `npm`; `uv` expects tracked dependency declarations; npm lockfiles are the reproducibility artifact.
- Not verifiable from repo alone: branch protection, org-level SHA pinning policy, GitHub Actions allowlists, release-signing policy, registry mirrors, and any private dependency proxy.

## Pass Log

1. Manifest and lockfile pass: found `DEP-001`, `DEP-002`.
2. CI bootstrap pass: expanded evidence for `DEP-001`; found `DEP-004`.
3. Update automation pass: found `DEP-003`.
4. Trust and provenance pass: no new issues beyond `DEP-004`.
5. Bootstrap tooling pass (`pre-commit`, devcontainer): found `DEP-005`.
6. Convergence pass: no new issues.
7. Convergence re-check: no new issues.

## Findings

### DEP-004 | High | issue_type: mutable-third-party-execution | confidence: high

- Impact: every CI run executes third-party code from movable refs, so an upstream tag or branch change can alter the repo's trusted build inputs without a corresponding repo diff.
- Evidence:
  - `.github/workflows/ci.yml:18` uses `actions/checkout@v6`
  - `.github/workflows/ci.yml:21` uses `actions/setup-python@v6`
  - `.github/workflows/ci.yml:26` uses `actions/cache@v5`
  - `.github/workflows/ci.yml:114` uses `codecov/codecov-action@v5`
  - `.github/workflows/validate.yml:19` uses `actions/checkout@v6`
  - `.github/workflows/validate.yml:21` uses `hacs/action@main`
  - `.github/workflows/validate.yml:33` uses `home-assistant/actions/hassfest@master`
- Why this matters here: the validation workflow is part of the dependency and release trust boundary for a Home Assistant integration distributed via GitHub/HACS. `@main` and `@master` are especially exposed because they can change outside normal semver/tag review.
- Recommendation: pin every GitHub Action to a full commit SHA, then let Dependabot manage SHA bumps for the `github-actions` ecosystem.

### DEP-001 | High | issue_type: undeclared-dependency-inventory | confidence: high

- Impact: the project's effective Python dependency set is not represented in tracked dependency metadata, so installs are floating, review diffing is weak, `uv.lock` is not authoritative, and Dependabot has almost nothing real to update.
- Evidence:
  - `pyproject.toml:1` declares project metadata but no `project.dependencies`, `project.optional-dependencies`, or `dependency-groups`
  - `pyproject.toml:8` only declares the build backend dependency `setuptools>=68.0`
  - `uv.lock:5` contains only the editable project entry
  - `.github/workflows/ci.yml:33`, `.github/workflows/ci.yml:66`, `.github/workflows/ci.yml:99`, `.github/workflows/ci.yml:143` install runtime, test, and lint/type packages directly from PyPI with plain `pip install`
  - `Makefile:79` installs the same toolchain ad hoc for local development
  - `scripts/verify_environment.py:148` treats `homeassistant`, `aiohttp`, `voluptuous`, `pytest`, `pytest-asyncio`, `pytest-homeassistant-custom-component`, `pytest-cov`, `ruff`, `mypy`, and `pre-commit` as required bootstrap dependencies
  - `.github/dependabot.yml:4` configures `package-ecosystem: "pip"`, but there is no actual tracked Python dependency inventory for it to manage besides `build-system.requires`
- Why this matters here: the repo currently relies on "whatever PyPI serves today" for CI, local setup, and pre-commit bootstrap. That weakens both security response and reproducibility.
- Recommendation: move the full Python inventory into `pyproject.toml` using `project.dependencies` plus `dependency-groups` (or equivalent tracked manifests), regenerate `uv.lock`, and make CI/Makefile/install docs consume that single declared source of truth.

### DEP-002 | Medium | issue_type: lock-and-version-drift | confidence: high

- Impact: tracked metadata disagrees about what version and lock state the repo actually represents, which undermines trust in lockfiles and complicates update automation.
- Evidence:
  - `pyproject.toml:3` sets project version `0.3.0`
  - `uv.lock:7` records the editable package as version `0.2.1`
  - `custom_components/ha_light_controller/manifest.json:17` sets integration version `0.4.0`
  - `package.json:3` sets version `0.3.0`
  - `package-lock.json:3` sets root version `1.0.0`
- Why this matters here: if contributors or automation trust these files for release or bootstrap decisions, they will get conflicting answers. It also signals that the current locks are not being regenerated as part of normal dependency updates.
- Recommendation: choose a canonical versioning flow for Python package metadata, Home Assistant manifest metadata, and npm metadata; then regenerate or remove stale lock/state files so each tracked artifact reflects current reality.

### DEP-003 | Medium | issue_type: orphaned-npm-surface | confidence: medium

- Impact: the repo carries a Node/Playwright dependency tree that appears to be stale, unexercised, and outside update governance, which expands attack surface without an active payoff.
- Evidence:
  - `package.json:9` defines Playwright test scripts
  - `package.json:17` adds `@playwright/test` and `playwright` as runtime `dependencies`
  - `package-lock.json:16` through `package-lock.json:74` lock the Playwright tree
  - `.github/dependabot.yml:1` has no `npm` update entry
  - repo inspection found no checked-in `tests/e2e/*` config or other Playwright consumer outside package metadata
- Why this matters here: stale test-only npm dependencies still need patching, review, and provenance. Right now they are neither used nor automatically updated.
- Recommendation: either remove the npm/Playwright surface entirely, or keep it and make it first-class by moving it to `devDependencies`, checking in the actual E2E config/tests, and adding an `npm` Dependabot entry.

### DEP-005 | Medium | issue_type: unmanaged-bootstrap-surfaces | confidence: medium

- Impact: bootstrap dependency paths outside the main Python/npm manifests are untracked or broken, so onboarding and local-tool trust can drift independently of the main dependency story.
- Evidence:
  - `.pre-commit-config.yaml:26` uses `pre-commit/mirrors-mypy`
  - `.pre-commit-config.yaml:30` adds extra packages `homeassistant` and `types-requests` inside the hook environment
  - `.devcontainer/devcontainer.json:3` pulls `mcr.microsoft.com/devcontainers/python:3.13`
  - `.devcontainer/devcontainer.json:4` runs `scripts/setup`
  - `.devcontainer/devcontainer.json:39` installs `ghcr.io/devcontainers-extra/features/apt-packages:1`
  - repo inspection found no `scripts/setup` file
- Why this matters here: these surfaces pull external code and packages during developer bootstrap, but they are not connected to the repo's main lock/update flow. The missing `scripts/setup` path also means the devcontainer bootstrap is already broken.
- Recommendation: either fold bootstrap dependencies into the tracked primary dependency system or explicitly govern them with their own update automation and health checks; fix or remove the broken devcontainer bootstrap command.

## Dependency Area Matrix

| Area | Status | Notes |
| --- | --- | --- |
| Python manifests and locks | red | Effective dependency inventory is outside tracked metadata. |
| npm manifests and locks | yellow | Lockfile exists, but update automation and live consumer evidence are missing. |
| GitHub Actions dependencies | red | Mutable refs, including branch refs, remain in trusted CI paths. |
| pre-commit bootstrap | yellow | Hook environments add their own unmanaged packages. |
| devcontainer/bootstrap | yellow | Floating external surfaces plus missing `scripts/setup`. |
| Release provenance | yellow | No repo-local evidence of signed or attested user-consumed release artifacts. |

## Convention Alignment

- `conv-review-001`: followed. This review was saved as a new timestamped artifact.
- Convention gap: `docs/conventions.md` has no repo-specific dependency governance convention covering manifest ownership, lock refresh rules, action pinning, or auxiliary bootstrap surfaces. This is not a separate finding, but the repo would benefit from adding one.

## Proposed Convention Candidates

- Define one canonical source of truth for Python dependency inventory and require CI, local setup, and docs to install only from that source.
- Treat `uv.lock` as authoritative only if it is regenerated in the same change that modifies dependency declarations; otherwise remove it.
- Require all GitHub Actions to be pinned to full SHAs, with Dependabot responsible for updates.
- Require every committed dependency surface (`pyproject.toml`, `package-lock.json`, `.pre-commit-config.yaml`, devcontainer config) to have an owner and an update path.
- Remove dormant dependency surfaces within one release cycle if they have no checked-in consumer or CI job.

## Fix Order And Batching

1. Batch A: declare the Python dependency inventory in `pyproject.toml`, regenerate `uv.lock`, and rewrite CI/Makefile/bootstrap commands to install from the tracked manifest instead of raw `pip install`.
2. Batch B: pin all Actions to SHAs, with special priority on `.github/workflows/validate.yml`.
3. Batch C: decide whether Playwright stays. If yes, add `npm` automation and real checked-in consumers; if no, delete `package.json` and `package-lock.json`.
4. Batch D: repair bootstrap edges by removing or fixing `scripts/setup` and deciding whether pre-commit extra deps need their own governance.

## Sources

- Shared artifact: `docs/review-orchestrator/2026-04-16-0018-codex-review-shared-research.md`
- GitHub Actions security hardening: https://docs.github.com/actions/learn-github-actions/security-hardening-for-github-actions
- Dependabot supported ecosystems: https://docs.github.com/en/enterprise-server%403.16/code-security/reference/supply-chain-security/supported-ecosystems-and-repositories
- uv dependency declaration guidance: https://docs.astral.sh/uv/concepts/projects/dependencies/
- npm lockfile guidance: https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json/
