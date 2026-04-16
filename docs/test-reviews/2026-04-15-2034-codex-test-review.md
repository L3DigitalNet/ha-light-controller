# Suggestion For Claude

- Use the `superpowers:receiving-code-review` skill before making follow-up changes.

# Test Suite Review

## Snapshot

- Repo: `/home/chris/projects/ha-light-controller`
- Branch: `main`
- Commit: `11b525c1d0139673e78daf7a68a4557d3715f0ce`
- Worktree: dirty
- Review date: `2026-04-15`
- Scope: full-repo test-suite review
- Research basis: reused `docs/review-orchestrator/2026-04-16-0018-codex-review-shared-research.md`; no additional external research was needed

## Method

- Pass 1: test runner and environment reproducibility
- Pass 2: harness fidelity vs Home Assistant testing guidance
- Pass 3: coverage shape, layering, and CI enforcement
- Pass 4: high-risk behavior gaps and stale test surfaces
- Pass 5: convergence check, no new issues
- Pass 6: convergence check, no new issues

## Local Verification

- `pytest tests` failed at collection in the current shell:
  - `Unknown config option: asyncio_default_fixture_loop_scope`
  - `'asyncio' not found in markers configuration option`
- `pytest tests --cov=custom_components --cov-report=term-missing` also failed because `pytest-cov` is not installed locally.
- The failures are consistent with the repo relying on ad hoc environment bootstrapping rather than a declared, reproducible test environment.

## Findings

### TEST-001

- Severity: high
- Confidence: high
- Type: execution-environment
- Summary: the repo does not declare a reproducible test environment, so the suite is not runnable from project metadata alone.
- Evidence:
  - `pyproject.toml:65-85` configures pytest to require async support and strict config.
  - `Makefile:79-84` installs test dependencies imperatively with `pip install ...` instead of deriving them from project metadata.
  - `CONTRIBUTING.md:19-45` tells contributors to use UV, but `uv.lock:1-8` only contains the editable root package and no test/dev dependency graph.
  - `.github/workflows/ci.yml:99-118` repeats another ad hoc install list in CI.
- Why it matters:
  - A contributor or automation environment can satisfy the repo’s Python requirement and still be unable to collect tests.
  - CI and local development can silently drift because the authoritative dependency set lives in shell snippets instead of one lockable source.
- Recommendation:
  - Move test and dev dependencies into first-class project metadata or dependency groups and regenerate `uv.lock`.
  - Make CI and `make install` consume the same declared environment instead of hand-maintained `pip install` lists.

### TEST-002

- Severity: high
- Confidence: high
- Type: harness-fidelity
- Summary: the suite replaces Home Assistant with a global `MagicMock` module tree, so it mostly validates local assumptions instead of the real integration contract.
- Evidence:
  - `tests/conftest.py:17-221` injects mocked `homeassistant.*`, `homeassistant.helpers.*`, and `voluptuous` modules into `sys.modules`.
  - `tests/conftest.py:27-29` reduces `ConfigEntryState` to string-like mock attributes.
  - `tests/test_init.py:122-141` only checks that `async_register` was called five times, not that real Home Assistant service registration behaves correctly.
  - `tests/test_button.py`, `tests/test_sensor.py`, `tests/test_config_flow.py`, and `tests/test_controller.py` all run on top of the same mocked substrate rather than a `pytest-homeassistant-custom-component` harness.
- Why it matters:
  - Regressions in config-entry lifecycle, service registration semantics, entity platform setup, selector behavior, or Home Assistant type changes can slip through while the suite still stays green.
  - The suite gives strong branch coverage signals without exercising the actual runtime boundary the integration ships against.
- Recommendation:
  - Add a smaller number of high-fidelity integration tests using the official Home Assistant test harness and `MockConfigEntry`.
  - Keep pure unit tests where useful, but stop treating the mocked module tree as the primary confidence source.

### TEST-003

- Severity: high
- Confidence: high
- Type: validation-coverage
- Summary: schema and input-validation paths are effectively untested because the suite stubs out `voluptuous` and Home Assistant config validation helpers.
- Evidence:
  - `tests/conftest.py:188-198` turns `vol.Schema`, `vol.Required`, `vol.Optional`, `vol.All`, `vol.Range`, and related validators into identity/no-op shims.
  - `tests/conftest.py:85-91` turns `cv.entity_ids`, `cv.entity_id`, `cv.string`, `cv.boolean`, and `cv.ensure_list` into `MagicMock`s.
  - `custom_components/ha_light_controller/__init__.py:159-286` defines substantial service schemas that the tests never execute against the real validation layer.
  - `custom_components/ha_light_controller/config_flow.py:104-220` and later flow steps build rich selector-backed schemas, but the tests only inspect returned dicts and mutated `_preset_data`.
- Why it matters:
  - Invalid service payloads, selector regressions, coercion bugs, and range-boundary mistakes can ship undetected.
  - This is especially risky for a Home Assistant integration where user-facing config flows and service calls are core product surfaces.
- Recommendation:
  - Add schema-focused tests that instantiate and execute the real validators.
  - Add at least a few end-to-end config-flow tests through Home Assistant’s flow manager so selector and validation behavior is exercised for real.

### TEST-004

- Severity: medium
- Confidence: high
- Type: maintainability
- Summary: the suite is heavily white-box and couples itself to private methods and internal mutable state, which reduces refactor safety and diagnostic value.
- Evidence:
  - `tests/test_controller.py:351-431`, `440-509`, `535-662`, and `815-886` directly test private helpers such as `_get_state`, `_expand_entity`, `_build_targets`, `_verify_*`, `_send_turn_on`, `_send_turn_off`, and `_log_to_logbook`.
  - `tests/test_config_flow.py:325-367`, `407-467`, and many later cases mutate and assert against `flow._preset_data`, `flow._configuring_entity`, and other private fields.
  - `tests/test_button.py:148-169` and `tests/test_sensor.py:124-142` assert internal `_attr_*` values directly instead of verifying behavior through entity registration and state updates.
- Why it matters:
  - Safe internal refactors will require broad test churn even when user-visible behavior does not change.
  - The suite spends a lot of effort proving implementation details while leaving more important runtime seams under-tested.
- Recommendation:
  - Rebalance future tests toward public behavior: service call results, config-flow transitions, entity states, and runtime side effects.
  - Keep a limited set of helper-level unit tests only where the logic is dense and stable enough to justify the coupling.

### TEST-005

- Severity: medium
- Confidence: high
- Type: layer-coverage
- Summary: the repo lacks a credible higher-level integration/E2E layer, and the advertised Playwright surface is currently dead.
- Evidence:
  - `package.json:9-19` advertises `test:e2e` and `test:e2e:headed` against `tests/e2e/playwright.config.js`.
  - The repo tree contains no `tests/e2e/` files.
  - The suite declares `unit`, `integration`, and `slow` markers in `pyproject.toml:78-82`, but current test inventory uses none of them.
  - Current inventory is `316` tests total, `183` async tests, `0` `unit` marks, `0` `integration` marks, `0` `slow` marks.
- Why it matters:
  - There is no clean way to run only high-fidelity integration coverage or to validate the actual HA-facing UX path the config flow and preset workflow depend on.
  - The Playwright scripts currently create false affordances for contributors and downstream automation.
- Recommendation:
  - Either remove the dead Playwright surface or implement it.
  - Introduce a small, explicit integration layer and actually use the declared markers so suites can be selected intentionally.

### TEST-006

- Severity: medium
- Confidence: high
- Type: coverage-governance
- Summary: coverage is measured but not enforced, despite the repo self-asserting a high coverage bar.
- Evidence:
  - `custom_components/ha_light_controller/quality_scale.yaml:113-114` claims `315 tests at 98%+ branch coverage`.
  - `.github/workflows/ci.yml:105-118` produces coverage output and uploads it to Codecov, but there is no `--cov-fail-under` gate and the Codecov upload is non-blocking.
  - The repo does not expose any in-repo threshold or policy that would fail CI when coverage drops materially.
- Why it matters:
  - Coverage regressions can accumulate quietly while documentation and quality-scale metadata continue to claim a stronger posture.
  - This is exactly the sort of drift that makes branch coverage numbers stop meaning what maintainers think they mean.
- Recommendation:
  - Add an explicit fail-under policy for the enforced coverage metric that the team actually cares about.
  - Update `quality_scale.yaml` only when it is backed by an enforceable CI threshold or checked artifact.

## Test Layer Matrix

| Layer | Current state | Notes |
| --- | --- | --- |
| Unit/helper tests | strong | Heavy coverage of controller, preset manager, entity classes, and config-flow helpers |
| Home Assistant integration tests | weak | No evidence of official HA harness usage despite `pytest-homeassistant-custom-component` being installed in CI |
| Config-flow end-to-end tests | weak | Flow steps are exercised through mocked base classes and private state, not HA’s real flow manager |
| Service contract tests | weak | Real voluptuous/cv validation is stubbed out |
| Diagnostics tests | partial | Output shape is checked, but redaction and HA diagnostics semantics are still mock-based |
| Browser/E2E tests | absent | `package.json` advertises Playwright, but the referenced test files are missing |
| CI smoke for test environment | partial | CI installs missing packages manually, but local reproducibility is not guaranteed |

## CI And Execution Coverage Analysis

- Strengths:
  - CI runs pytest on Python `3.13` and `3.14`.
  - Coverage is collected and exported.
  - A local `verify_environment.py` script exists.
- Gaps:
  - Test environment definition is duplicated across CI and Makefile.
  - Coverage is informational only, not gating.
  - There is no repo-visible separation between fast unit tests and slower or higher-fidelity integration tests.

## Missing Test Types

- Official Home Assistant harness tests for setup, unload, and config-entry lifecycle
- Real schema-validation tests for services and config-flow selectors
- Higher-level config-flow/user-journey coverage through HA interfaces
- A real browser/E2E layer or removal of the dead Playwright surface
- Targeted regression tests for compatibility with future HA/validator changes at the actual runtime boundary

## High-Risk Untested Behaviors

- Service schema coercion and rejection behavior for malformed payloads
- Selector-backed config-flow schemas and section flattening under the real HA flow engine
- Actual service registration semantics and `SupportsResponse` behavior in Home Assistant
- Entity registration and platform lifecycle behavior under the real entity registry/device registry implementations
- Upgrade/regression behavior when Home Assistant changes helper APIs or validation expectations

## Security Testing Gaps

- No high-fidelity tests that prove invalid or malicious service payloads are rejected by the real validation layer
- No repo-visible tests around diagnostics redaction using Home Assistant’s real support/export helpers
- No negative tests around malformed entity IDs or selector inputs at the true integration boundary

## API Contract Testing Gaps

- Service contracts are asserted by calling handlers directly, not by exercising the registered schemas
- Config-flow contracts are asserted via internal dict shape, not via Home Assistant’s actual flow contract machinery
- No contract-style assertions for compatibility of service responses across releases

## Charlotte-Assisted Opportunities

- None directly inside this repo today because there is no standalone browser app surface.
- If a reproducible Home Assistant demo fixture is added later, Charlotte would be useful for validating config-flow UX, preset management flows, and accessibility/operability of the integration’s UI surfaces.

## Convention Notes

- `docs/conventions.md` exists and was used as review input.
- No convention-quality issue rose above the main findings, but the current conventions do not yet encode a repo-standard testing strategy for:
  - authoritative dependency declaration
  - when to use the official HA harness vs pure unit mocks
  - coverage threshold enforcement
  - marker usage for unit/integration/slow layers

## Proposed Convention Candidates

- Define one authoritative source for dev/test dependencies and require CI plus local commands to consume it unchanged.
- Require Home Assistant integration changes to add at least one real harness-backed test when touching config flows, service registration, or config-entry lifecycle.
- Reserve private-method tests for dense pure logic only; default new tests toward public behavior.
- Enforce coverage with a repo-visible threshold instead of relying on descriptive metadata.
- Either maintain a working E2E layer or remove dead E2E scripts and dependencies promptly.

## Claude Handoff

- Fix order:
  1. `TEST-001`
  2. `TEST-002`
  3. `TEST-003`
  4. `TEST-005`
  5. `TEST-006`
  6. `TEST-004`
- Suggested batching:
  - Batch A: establish authoritative dev/test dependency metadata and make CI/local setup consume it
  - Batch B: add a minimal HA-harness test slice for setup, one service, and one config-flow path
  - Batch C: replace validator mocks with real schema execution for service/config-flow contracts
  - Batch D: either implement or remove Playwright E2E, then add marker discipline and coverage gating
  - Batch E: gradually retire brittle private-state assertions as higher-level coverage lands
