Use Claude's `superpowers:receiving-code-review` skill for follow-up triage and fix execution.

# Observability Review

## Snapshot

- repo: `/home/chris/projects/ha-light-controller`
- branch: `main`
- commit: `11b525c1d0139673e78daf7a68a4557d3715f0ce`
- worktree: dirty (`.codex/`, `docs/` untracked)
- review time: `2026-04-15 20:29 EDT`
- review scope: repository-only observability + diagnosability review
- shared research reused: `docs/review-orchestrator/2026-04-16-0018-codex-review-shared-research.md`
- targeted follow-up research: Home Assistant diagnostics rule + log-when-unavailable rule only

## Method

- Pass 1: inventory repo-native signals: logs, logbook writes, diagnostics, entity attributes, docs
- Pass 2: inspect failure paths and signal quality in `controller.py`, `preset_manager.py`, `sensor.py`, `__init__.py`
- Pass 3: inspect supportability and data hygiene in diagnostics + troubleshooting docs
- Pass 4: inspect regression coverage in tests and compare against HA guidance
- Pass 5: convergence pass, no new issues
- Pass 6: convergence pass, no new issues

## Findings

### OBS-001

- severity: high
- confidence: high
- type: telemetry-data-hygiene
- files:
  - `custom_components/ha_light_controller/diagnostics.py:17`
  - `custom_components/ha_light_controller/diagnostics.py:23`
- issue:
  - Diagnostics do not use Home Assistant's redaction helper and return user-authored preset names verbatim. The official diagnostics rule expects sensitive fields to be redacted and shows `async_redact_data(...)` as the standard pattern for config/runtime exports. Even without API tokens, preset names can encode room names, occupant names, or other location/personal details, and the current export returns them unchanged.
- why it matters:
  - Support bundles are the place users most often paste into issues or chats. Returning human-authored names without a redaction policy creates unnecessary privacy risk and makes the repo's diagnostics surface weaker than current HA guidance.
- recommendation:
  - Introduce an explicit redaction policy for diagnostics.
  - Use `async_redact_data` for config/runtime payloads.
  - Either omit preset names entirely or replace them with stable synthetic labels in diagnostics.

### OBS-002

- severity: high
- confidence: high
- type: supportability-gap
- files:
  - `custom_components/ha_light_controller/diagnostics.py:19`
  - `custom_components/ha_light_controller/sensor.py:78`
  - `custom_components/ha_light_controller/sensor.py:140`
  - `custom_components/ha_light_controller/preset_manager.py:209`
  - `USAGE.md:682`
  - `USAGE.md:689`
- issue:
  - The integration's stateful failure context is mostly absent from diagnostics. Runtime status already tracks `last_result`, attempts, failed lights, skipped lights, and elapsed time via `PresetStatus`, and the sensor exposes that data when enabled, but diagnostics export only static config/options plus a lightweight preset summary. The only durable runtime surface is a preset status sensor that is disabled by default.
- why it matters:
  - After a failed preset activation, the most useful support clues are the recent result payload and affected entities. Today those details are only visible if the user had manually enabled the status sensor beforehand. A downloaded diagnostics bundle does not capture them, so the primary support artifact misses the most relevant failure evidence.
- recommendation:
  - Add a redacted runtime status section to diagnostics, sourced from `entry.runtime_data.preset_manager`.
  - Include recent result code, attempts, elapsed time, failed/skipped counts, and stable redacted entity identifiers.
  - Document that diagnostics are the preferred support artifact, not just debug logs.

### OBS-003

- severity: medium
- confidence: high
- type: signal-quality
- files:
  - `custom_components/ha_light_controller/controller.py:424`
  - `custom_components/ha_light_controller/controller.py:477`
  - `custom_components/ha_light_controller/controller.py:807`
  - `custom_components/ha_light_controller/controller.py:839`
  - `custom_components/ha_light_controller/controller.py:850`
  - `custom_components/ha_light_controller/controller.py:874`
  - `custom_components/ha_light_controller/sensor.py:140`
- issue:
  - The controller computes fine-grained verification outcomes (`WRONG_STATE`, `WRONG_BRIGHTNESS`, `WRONG_COLOR`, `UNAVAILABLE`, `ERROR`), but it discards that classification before returning the final result. The persisted/logged outcome only keeps a flat `failed_lights` list and a free-text message. On top of that, exception logging uses `_LOGGER.error(..., %s)` without traceback context in the core failure paths.
- why it matters:
  - When a command fails, operators cannot tell whether the problem was a service-call exception, stale state reporting, unsupported color mode, wrong brightness, or timeout-induced retry exhaustion. That forces users into debug logging and source inspection for issues that should be diagnosable from first-line support artifacts.
- recommendation:
  - Preserve per-light failure reasons in the result payload and preset status.
  - Add counters or a redacted `failure_reasons` map to diagnostics and status attributes.
  - Switch exception paths that represent unexpected failures to `_LOGGER.exception(...)` or `exc_info=True`.

### OBS-004

- severity: medium
- confidence: high
- type: docs-runbook-gap
- files:
  - `USAGE.md:689`
  - `USAGE.md:703`
  - `README.md:116`
- issue:
  - Troubleshooting guidance points users at debug logs and manual state inspection, but never tells them to collect Home Assistant diagnostics even though the integration implements them. README and usage docs also do not explain what the diagnostics bundle contains, what it intentionally redacts, or when maintainers should ask for it.
- why it matters:
  - That leaves the support flow log-centric and ad hoc. Users are nudged toward noisier, less structured evidence instead of the repo's built-in support artifact.
- recommendation:
  - Add a short "Collect diagnostics" subsection to `USAGE.md` troubleshooting.
  - Document the support sequence: reproduce -> download diagnostics -> optionally enable debug logging if needed.
  - Note that the preset status sensor is optional and disabled by default.

### OBS-005

- severity: low
- confidence: high
- type: observability-testing-gap
- files:
  - `tests/test_diagnostics.py:14`
  - `tests/test_diagnostics.py:68`
  - `tests/test_controller.py:867`
- issue:
  - Observability tests mostly assert shape and "does not crash" behavior. They do not verify redaction, runtime-status inclusion, or emitted log content/level. There are no `caplog`-style assertions protecting message quality, single-unavailability logging behavior, or traceback-bearing exception paths.
- why it matters:
  - Observability regressions are easy to introduce silently: diagnostics may leak more than intended or become less useful, and logs may degrade without breaking functional tests.
- recommendation:
  - Add tests for diagnostics redaction and runtime summary fields.
  - Add logging assertions for the key failure paths, especially verification exceptions and unavailable-light handling.

## Area Matrix

| Area | Status | Notes |
| --- | --- | --- |
| Structured logging | partial | Standard `_LOGGER` usage exists, but context is thin and exception traces are dropped in core paths. |
| Runtime state / support export | weak | Diagnostics are implemented, but runtime failure evidence is omitted. |
| User-visible status surface | partial | Preset status sensors expose useful result fields, but they are disabled by default. |
| Troubleshooting docs | partial | Debug-log instructions exist; diagnostics collection guidance is missing. |
| Metrics / traces / SLOs | not present | No repo evidence of metrics, tracing, SLOs, dashboards, or alerting. Likely out of scope for this HA integration, but unverified externally. |
| Telemetry pipeline / collector | unverified | No in-repo sink/export pipeline. |
| Alert routing / incident response | unverified | No pager/dashboard/runbook artifacts in repo. |
| Data hygiene / redaction | weak | Diagnostics export lacks explicit redaction policy/helper usage. |
| Observability tests | weak | Functional surfaces are tested more than observability semantics. |

## Verified / Inferred / Unverified

### Verified from repo

- Logs, logbook writes, diagnostics, and preset status sensors are the only repo-native observability surfaces.
- Preset runtime status exists in memory and is exposed through the sensor attributes.
- Diagnostics export is static and does not include runtime status.
- Troubleshooting docs recommend debug logging but not diagnostics download.

### Inferred

- The intended support workflow today is "check logs first," not "collect diagnostics first."
- Preset names are likely user-authored and may contain location/personal context.

### Could not verify from repo

- Any external dashboards, log sinks, alert routing, HA Supervisor add-ons, or release-time telemetry outside this repo
- Whether maintainers currently request diagnostics in GitHub issues or community support flows
- Production log volume/noise characteristics in real Home Assistant installations

## Convention And Guidance Notes

- `docs/conventions.md` has no observability-specific rule set for diagnostics redaction, result-shape stability, or support collection workflow.
- `custom_components/ha_light_controller/quality_scale.yaml:123` marks diagnostics as done, but the current implementation is weaker than the current HA example because it skips explicit redaction and omits runtime status.

## Proposed Convention Candidates

- `cand-obs-001`: Any diagnostics export must use `async_redact_data` and define an explicit redact/omit policy for user-authored names and entity identifiers.
- `cand-obs-002`: If runtime status exists in memory, diagnostics must include a redacted recent-status summary so support bundles capture the last known failure context.
- `cand-obs-003`: Result payloads for retrying service operations must preserve machine-readable failure reasons, not just entity lists and free-text summary strings.
- `cand-obs-004`: Troubleshooting docs must prefer diagnostics-first support collection and only escalate to debug logging when diagnostics are insufficient.
- `cand-obs-005`: Add regression tests for diagnostics redaction and for log semantics in primary failure paths.

## Research Notes

- Shared research pack reused: `docs/review-orchestrator/2026-04-16-0018-codex-review-shared-research.md`
- Targeted official follow-up:
  - HA diagnostics rule: https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/diagnostics/
  - HA log-when-unavailable rule: https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/log-when-unavailable/

## Validation Notes

- I attempted a targeted pytest run for observability-adjacent tests, but the current local environment lacks the plugin/config combination expected by this repo's pytest settings. The run failed during collection with `Unknown config option: asyncio_default_fixture_loop_scope` and missing `asyncio` marker registration, so the review relies on source inspection plus existing test code rather than executed test results.

## Claude Handoff

- suggested fix order:
  1. OBS-001 and OBS-002 together: redesign diagnostics around redacted config + redacted runtime status.
  2. OBS-003 next: preserve machine-readable per-light failure reasons and improve exception logging.
  3. OBS-004 and OBS-005 last: update support docs and add regression coverage.
- batching guidance:
  - Batch A: `diagnostics.py`, redaction helpers, runtime summary wiring, diagnostics tests
  - Batch B: `controller.py` result schema + sensor/runtime status propagation + logging improvements
  - Batch C: `USAGE.md` / `README.md` support workflow updates + observability-focused tests
- watchouts:
  - Keep diagnostics safe for public issue attachment.
  - Avoid making the preset status sensor noisier unless diagnostics now carry enough recent state on their own.
  - If result payload shape changes, update service docs and tests together.
