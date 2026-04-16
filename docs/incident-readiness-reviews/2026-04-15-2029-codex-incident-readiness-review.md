Claude: use `superpowers:receiving-code-review`.

# Incident Readiness Review

## Repo Snapshot

- repo: `/home/chris/projects/ha-light-controller`
- branch: `main`
- commit: `11b525c1d0139673e78daf7a68a4557d3715f0ce`
- worktree: `dirty` (`.codex/`, `docs/` untracked)
- review timestamp: `2026-04-15 20:29 EDT`
- review scope: full incident-readiness review of repo-controlled surfaces only

## Inputs

- required repo docs: `docs/handoff.md`, `docs/conventions.md`
- shared research reused first: `docs/review-orchestrator/2026-04-16-0018-codex-review-shared-research.md`
- targeted follow-up research only:
  - Home Assistant system health: https://developers.home-assistant.io/docs/core/integration_system_health/
  - Home Assistant repair issues rule: https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/repair-issues
  - Home Assistant troubleshooting-docs rule: https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/docs-troubleshooting/

## Method

- pass 1: runtime failure handling and manual mitigation surfaces
- pass 2: user recovery docs, rollback docs, and support guidance
- pass 3: diagnostics, status surfaces, and support artifacts
- pass 4: CI/change-safety and hotfix validation posture
- pass 5: convention and quality-scale alignment
- pass 6: convergence pass, no new issues
- pass 7: convergence pass, no new issues

## Area Matrix

| Area | Status | Notes |
| --- | --- | --- |
| Detection and triage | weak | Failures mostly surface via transient service responses, logbook entries, and an opt-in status sensor. |
| Rollback and disablement | weak | No explicit incident playbook or documented emergency fallback path. |
| Manual mitigation | partial | Users can tune retries/tolerances, but docs do not define an emergency containment sequence. |
| Diagnostics and support export | weak | Diagnostics are intentionally minimal and omit the most useful incident context. |
| Runtime recovery behavior | partial | Retry loop, timeout handling, and preset failure states exist. |
| Change safety during hotfixes | partial | CI exists, but validation workflow uses mutable action refs. |
| Incident testing | partial | Failure/timeout code paths are tested, but operator recovery and restart-era observability are not. |

## Findings

### IR-001

- severity: high
- confidence: high
- issue_type: runbook-gap

The repo does not document an incident disablement or rollback path.

Why it matters:
- During a bad rollout or live automation failure, operators need a fast, low-risk sequence to contain blast radius.
- Current docs explain parameter tuning and eventual removal, but not how to stop the integration safely, revert affected automations to native `light.turn_on` / `light.turn_off`, capture evidence first, or verify recovery after rollback.

Verified evidence:
- README removal guidance is permanent removal only, not incident containment or rollback: `README.md:58-66`.
- The usage guide troubleshooting section focuses on tolerance/delay tuning and restarts, not emergency disablement, evidence capture, or rollback verification: `USAGE.md:689-740`.
- No dedicated incident/runbook docs exist under `docs/` beyond generated review artifacts.

Recommended fix:
- Add a short incident runbook covering containment, evidence capture, temporary fallback to native light services, preset isolation, rollback steps, and post-recovery verification.

### IR-002

- severity: medium
- confidence: high
- issue_type: observability-support-gap

The support bundle is too thin to help with real incident triage.

Why it matters:
- This integration’s failures are often caused by per-entity target mismatches, unsupported color modes, or timing/tolerance issues.
- The current diagnostics export omits the exact preset targets, last activation result, failed/skipped lights, timestamps, and any system-health style summary, which makes remote triage much harder.

Verified evidence:
- Diagnostics only export config-entry data without raw presets, plus options and a small preset summary: `custom_components/ha_light_controller/diagnostics.py:13-33`.
- The tests enforce that diagnostics remain summary-only and exclude raw preset data: `tests/test_diagnostics.py:44-82`.
- Repo scan found no `custom_components/ha_light_controller/system_health.py`, despite Home Assistant documenting system health as a standard support surface.

Recommended fix:
- Expand diagnostics with redacted preset target detail and last-known failure metadata.
- Add `system_health.py` with lightweight integration-health signals that help users and maintainers understand current state.

### IR-003

- severity: medium
- confidence: high
- issue_type: failure-signaling-gap

Failure context is non-durable and easy to miss after the initial incident.

Why it matters:
- Preset failure context is stored only in runtime memory and disappears on Home Assistant restart or config-entry reload.
- The richest failure surface is a status sensor that ships disabled by default, so many users will not have a persistent UI signal when preset activations begin failing.
- Built-in failure notifications were removed, but the repo does not provide replacement automation patterns for operators.

Verified evidence:
- Preset status is runtime-only and initialized empty on load; `last_result` and `last_activated` are not persisted to config-entry storage: `custom_components/ha_light_controller/preset_manager.py:110-146`, `209-227`.
- The status sensor is disabled by default: `custom_components/ha_light_controller/sensor.py:76-85`.
- Failure details are only attached to the sensor attributes when status is present in memory: `custom_components/ha_light_controller/sensor.py:122-160`.
- Notification support was explicitly removed, with the changelog stating users should build their own automations from service responses: `CHANGELOG.md:102-115`.

Recommended fix:
- Persist a small last-failure record for presets or expose it in diagnostics.
- Ship documented example automations for actionable failure notifications.
- Reconsider whether the preset status sensor should remain disabled by default when incident visibility is important.

### IR-004

- severity: low
- confidence: high
- issue_type: hotfix-validation-risk

The validation workflow depends on mutable third-party action refs.

Why it matters:
- During a hotfix or release recovery window, validation should be deterministic.
- `@main` and `@master` can change underneath the repo, creating new failures or altered behavior exactly when operators are trying to ship a contained fix.

Verified evidence:
- `hacs/action@main`: `.github/workflows/validate.yml:19-23`
- `home-assistant/actions/hassfest@master`: `.github/workflows/validate.yml:31-33`

Recommended fix:
- Pin these actions to full commit SHAs and document the update process.

### IR-005

- severity: low
- confidence: medium
- issue_type: convention-quality-problem

The local quality-scale claim that `repair-issues` is exempt looks under-justified.

Why it matters:
- Home Assistant’s own rule says repair issues are appropriate when user intervention is needed.
- This repo’s troubleshooting guidance already tells users to adjust tolerances, delays, retries, and capability expectations, which means there are user-fixable failure modes.
- Treating the rule as categorically exempt can hide a useful recovery surface from future maintainers.

Verified evidence:
- Local exemption says there are no configuration states requiring repair-style user intervention: `custom_components/ha_light_controller/quality_scale.yaml:195-201`.
- The troubleshooting guide instructs users to change integration settings and investigate entity capabilities to recover: `USAGE.md:691-730`.

Recommended fix:
- Revisit the exemption rationale. If the project keeps the exemption, tighten the justification. Otherwise, consider repair issues for repeated, user-fixable preset or verification failures.

## Verified vs Inferred

### Verified from repo evidence

- Retry, timeout, and failure-return paths exist in the controller.
- Failure logbook writes exist for several unhappy paths.
- Preset failure status exists, but it is runtime-only.
- Docs contain troubleshooting guidance but no incident runbook.
- Diagnostics are summary-only.
- Validation workflow uses mutable refs.

### Inferred

- Users are likely to miss incidents unless they explicitly consume service responses or enable the status sensor.
- Support triage will likely require extra back-and-forth because diagnostics lack failure detail.

### Not Verifiable From Repo Alone

- Branch protection, required checks, environment approvals, and release rollback procedures in GitHub settings.
- Production alert routing, dashboards, or support escalation outside the repository.
- Whether maintainers already use an external incident runbook or operational checklist.

## Testing Notes

- Repo review included source inspection and test-surface inspection.
- `pytest -q` could not be completed in this environment because the local pytest environment is missing the expected asyncio plugin/config support:
  - `Unknown config option: asyncio_default_fixture_loop_scope`
  - `'asyncio' not found in markers configuration option`
- I did not modify code or docs other than saving this report.

## Fix Order

1. IR-001: add the incident disablement and rollback runbook.
2. IR-002: improve diagnostics and add system health.
3. IR-003: make failure signals durable and document notification patterns.
4. IR-004: pin validation actions for deterministic hotfix validation.
5. IR-005: revisit the `repair-issues` exemption and align conventions with actual recovery behavior.

## Batching Guidance For Claude

- batch A: docs/runbook work (`README.md`, `USAGE.md`, optional new runbook doc)
- batch B: support surfaces (`diagnostics.py`, optional `system_health.py`, tests)
- batch C: failure-signaling improvements (preset status persistence or notification examples)
- batch D: CI hardening (`.github/workflows/validate.yml`)
- batch E: convention cleanup (`quality_scale.yaml`, related docs)
