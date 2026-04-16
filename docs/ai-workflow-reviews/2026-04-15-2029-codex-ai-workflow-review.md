# AI And Prompt Workflow Review

Claude Code note: consider using the `superpowers:receiving-code-review` skill.

## Snapshot

- generated_at: `2026-04-15 20:29 EDT`
- repo_path: `/home/chris/projects/ha-light-controller`
- branch: `main`
- commit: `11b525c1d0139673e78daf7a68a4557d3715f0ce`
- worktree: `dirty` (`docs/`, `.codex/` untracked)
- conventions_input: `docs/conventions.md`
- shared_research_input: `docs/review-orchestrator/2026-04-16-0018-codex-review-shared-research.md`

## Scope

- Verified repo-local AI surface is limited to developer-agent artifacts: `CLAUDE.md`, `.claude/settings.json`, `.contextstream/config.json`, AI/editor comments in `.gitignore`, and browser-tooling remnants in `package.json`.
- No product-side model SDK, prompt template directory, `.mcp.json`, `.claude/rules/`, committed subagents, or user-facing LLM feature code was found in the repo.
- Review therefore focuses on prompt governance, tool boundaries, operator safety, and validation posture for developer-agent workflows.

## Pass Log

- Pass 1: repo-wide AI surface inventory and scope confirmation
- Pass 2: prompt artifact review (`CLAUDE.md`, `AGENTS.md`, contributor docs)
- Pass 3: tool and permission boundary review (`.claude/settings.json`)
- Pass 4: governance and drift review across AI-related docs and repo contents
- Pass 5: validation/eval surface review for browser or agent-assisted workflows
- Pass 6: convergence pass; no new issues after pass 5

## Findings

### AI-001

- severity: medium
- confidence: high
- type: least-authority / tool-boundary
- evidence: `.claude/settings.json:1-6`
- issue: Shared project settings grant `Read(//home/chris/projects/ha-template/**)`, which is an unrelated repo path and a machine-specific absolute path.
- why_it_matters: In Claude Code, project settings are team-shared, while local scope is intended for machine-specific settings. This entry both widens model-visible context beyond this repo on one machine and becomes dead or misleading config for other collaborators.
- recommendation: Move this rule to `.claude/settings.local.json` if it is personal, or replace it with a repo-relative, documented boundary that every collaborator actually needs. Add explicit deny rules for secrets if any cross-repo read remains necessary.

### AI-002

- severity: medium
- confidence: high
- type: secret-handling / operator-safety
- evidence: `CLAUDE.md:188-198`
- issue: The shared project prompt instructs Claude to use a machine-specific Podman Home Assistant instance and says connection details plus an access token are stored in project memory.
- why_it_matters: This mixes credentialed operational access into shared prompt context without a repo-auditable boundary, approval rule, or reproducible setup path. It also conflicts with Claude Code guidance that project instructions should stay team-shared and that personal project-specific data belongs in local instructions.
- recommendation: Move the live-environment path and credentialed workflow into `CLAUDE.local.md` or local settings, keep the repo prompt limited to sanitized setup guidance, and require explicit human confirmation before any agent uses remembered credentials or touches an external HA instance.

### AI-003

- severity: low
- confidence: high
- type: prompt-governance / conflicting-instructions
- evidence: `CLAUDE.md:10-13`, `CONTRIBUTING.md:8-13`
- issue: `CLAUDE.md` says all changes must be made on `testing`, while `CONTRIBUTING.md` tells contributors to create a feature branch and open a PR against `main`.
- why_it_matters: Claude Code’s own guidance warns that conflicting instructions reduce adherence and can cause the agent to choose arbitrarily. This repo now has diverging human and agent workflow rules for the same operation.
- recommendation: Pick one branch workflow and align both docs. If `testing` is only a maintainer-local rule, move it out of the shared project prompt into local instructions.

### AI-004

- severity: low
- confidence: high
- type: prompt-artifact drift
- evidence: `.gitignore:210-239`, `CHANGELOG.md:29-31`, `CHANGELOG.md:46-50`
- issue: `.gitignore` still declares several AI/editor artifacts as files that "MUST be tracked" (`.github/copilot-instructions.md`, `.vscode/codex-instructions.md`, `resources/agents/`, `REFERENCE_GUIDE.md`, `.github/AUTOMATION_GUIDE.md`), but the repo inventory does not contain them and the changelog says embedded skills/agents were removed in favor of a plugin-based approach.
- why_it_matters: This leaves future agents and reviewers with an inaccurate source-of-truth for the repo’s AI workflow, increasing setup ambiguity and making it hard to tell which prompt/tool artifacts are authoritative.
- recommendation: Remove stale inventory claims from `.gitignore` or reintroduce the missing artifacts with owners and current usage notes. Keep the changelog, ignore comments, and actual repo contents in sync.

### AI-005

- severity: low
- confidence: high
- type: eval-gap / tooling drift
- evidence: `package.json:9-19`, `.gitignore:235-239`
- issue: The repo still advertises Playwright-based `test:e2e` scripts pointing to `tests/e2e/playwright.config.js`, but no `tests/e2e/` directory or Playwright config exists in the repo.
- why_it_matters: If browser-assisted or MCP-style validation is part of the intended developer-agent workflow, it is currently not reproducible from source control. The only remaining evidence is dead scripts plus ignored `.playwright-mcp/` artifacts.
- recommendation: Either remove the dead Playwright/browser-agent references or restore a minimal committed harness and document when it should be used as part of the AI workflow.

## Verified / Inferred / Unverified

- verified: repo-local AI surface is developer tooling only; no product-side LLM integration was found.
- inferred: the active AI workflow is primarily Claude/Codex-style repo assistance, not user-facing model behavior.
- unverified: contents of project memory, safety of the remembered HA access token, any user-local Claude settings, and any plugin-based tooling that exists outside this repository.

## Sources

- Shared research pack: `docs/review-orchestrator/2026-04-16-0018-codex-review-shared-research.md`
- Claude Code settings: https://code.claude.com/docs/en/settings
- Claude Code memory and instruction scoping: https://code.claude.com/docs/en/memory

## Claude Handoff

- fix_order:
- 1. Remove or localize the unrelated cross-repo read permission in `.claude/settings.json`.
- 2. Move credentialed live-environment instructions out of shared `CLAUDE.md` and into local-only artifacts.
- 3. Reconcile branch workflow instructions between `CLAUDE.md` and `CONTRIBUTING.md`.
- 4. Clean up stale AI/plugin/browser artifact references in `.gitignore`, `package.json`, and supporting docs.
- batching_guidance:
- batch_a: AI-001 and AI-002 together as the least-authority and secret-boundary cleanup.
- batch_b: AI-003 and AI-004 together as prompt-governance and repo-inventory alignment.
- batch_c: AI-005 separately if the team wants to decide whether browser-agent validation is in scope at all.
