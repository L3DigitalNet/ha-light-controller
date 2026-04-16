# Codex Review Shared Research Pack

## Repo Snapshot

- repo_root: `/home/chris/projects/ha-light-controller`
- planning_report: [`docs/review-orchestrator/2026-04-16-0018-codex-review-plan.md`](/home/chris/projects/ha-light-controller/docs/review-orchestrator/2026-04-16-0018-codex-review-plan.md)
- generated_at: `2026-04-15 20:22:31 EDT`
- planning_snapshot: branch `main`, head `11b525c1d0139673e78daf7a68a4557d3715f0ce`, worktree `dirty`
- repo shape from plan + manifests: Home Assistant custom integration, Python package metadata in `pyproject.toml`, Playwright E2E tooling in `package.json`, GitHub Actions CI, HACS/Hassfest validation
- scope note: shared external guidance only; no repo-specific findings and no child-review conclusions

## Selected Reviews

- `product-and-business-logic-review`
- `documentation-and-runbook-review`
- `dependency-supply-chain-review`
- `ai-and-prompt-workflow-review`
- `ci-cd-review`
- `observability-review`
- `release-readiness-review`
- `incident-readiness-review`
- `test-suite-review`

## Shared Stack And Ecosystem Guidance

### Home Assistant Custom Integration Baseline

- `manifest.json` is the canonical integration metadata surface. For custom integrations, Home Assistant requires a manifest and requires a valid `version`; `config_flow: true` must be declared if the integration exposes a config flow; `integration_type` should be set explicitly. This is shared input for release, docs, product, and test reviews.
- Config flows own user-input validation and stored config-entry data. Home Assistant guidance is to validate connectivity in the config flow, not defer obvious failure until startup.
- Setup failures should map to Home Assistant’s lifecycle exceptions: use `ConfigEntryNotReady` for transient setup problems, `ConfigEntryAuthFailed` for credential failures, and `ConfigEntryError` for durable misconfiguration. This is relevant to product logic, incident readiness, docs, and release posture.
- The current Home Assistant quality-scale rule set is a strong cross-review rubric even for custom integrations: config-flow coverage, overall test coverage, diagnostics, reauthentication, reconfiguration, troubleshooting docs, update-model docs, and strict typing are all first-class expectations.
- Custom integrations do not use Home Assistant Core’s translation build pipeline. Official localization guidance says not to rely on `strings.json` placeholders; custom components must ship full flat translations in `translations/en.json`. This is shared input for docs, release, and test reviews because broken translations surface as config-flow UX failures.

### Sensitive Data, Diagnostics, And User Support

- Home Assistant diagnostics are meant for support workflows, but the official guidance is explicit that diagnostics must not expose passwords, API keys, auth tokens, location data, or personal information; `async_redact_data` is the standard redaction utility.
- The quality-scale docs also treat troubleshooting documentation as a product expectation, not just a docs nice-to-have. Troubleshooting sections should describe symptoms plus concrete resolution steps.
- Reauthentication and repair flows are official UI-level recovery patterns. Downstream docs, product, incident-readiness, and release reviews can reuse this expectation when evaluating how the project handles broken credentials or user-action-required failures.

### Testing And CI Guidance

- Home Assistant testing guidance prefers black-box integration tests through Home Assistant interfaces over brittle assertions on internals: call services through `hass.services`, assert via registries and `ConfigEntry.state`, and use `MockConfigEntry` when appropriate.
- Home Assistant quality-scale expectations are explicit: config flows should have full coverage, and integration modules should be above 95% coverage overall. This is useful for both the test-suite and release-readiness reviews.
- Pytest recommends registering custom markers and using strict marker validation so typos become errors instead of warnings. `strict_config` is likewise the official way to fail invalid pytest config early.
- `pytest-asyncio` now documents that `asyncio_mode` defaults to `strict` when unset, while `asyncio_default_fixture_loop_scope` will move toward `function` as the default in future versions. Explicit loop-scope configuration avoids future-behavior drift.
- Playwright’s CI guidance still recommends reduced worker parallelism on CI and artifact upload for reports. Trace Viewer guidance recommends `trace: 'on-first-retry'` as the CI-friendly debugging default.

### GitHub Actions, Delivery, And Supply Chain Guidance

- GitHub’s workflow syntax and `GITHUB_TOKEN` docs continue to recommend least-privilege permissions. If a workflow or job specifies any permission explicitly, all unspecified permissions become `none`.
- GitHub’s security-hardening guidance still recommends pinning third-party actions to a full commit SHA instead of a movable tag. Repository policy can enforce SHA pinning.
- GitHub concurrency controls are the standard guardrail for non-reentrant jobs: a concurrency group permits at most one running and one pending run, and `cancel-in-progress: true` can actively replace stale runs. This is relevant to CI cost, release safety, and incident containment.
- GitHub’s dependency-review action is the built-in PR-time supply-chain gate for newly introduced vulnerable packages. It is reusable across dependency, CI, and release reviews.
- Artifact attestations are now a mainstream GitHub release-integrity mechanism. GitHub positions them as provenance and integrity guarantees for release artifacts, optionally paired with SBOMs. The docs explicitly say they are useful for software people consume, not for routine ephemeral CI outputs.

### Packaging And Provenance Guidance

- PyPI Trusted Publishing uses GitHub Actions OIDC to exchange short-lived identity tokens for short-lived publish credentials, removing the need for long-lived PyPI API tokens. Job-level `id-token: write` is the required permission and is the recommended least-exposure placement.
- PyPI’s attestation docs now treat digital attestations as first-class release metadata tied to uploaded artifacts and verified identities. This pairs naturally with GitHub artifact attestations for release-readiness and dependency provenance discussions.
- npm’s `package-lock.json` remains the official mechanism for reproducible dependency trees: npm documents it as the representation that lets teammates, CI, and deployments install the same dependency tree and review tree changes in source control.

### AI Workflow Scope Note

- Current repo-surface inspection did not confirm a concrete model vendor, prompt artifact set, or agent/tool boundary beyond orchestrator review artifacts. Downstream `ai-and-prompt-workflow-review` work should first verify that an actual prompt/model/tool surface exists before applying vendor-specific guidance.

## Cross-Cutting Review Guidance

- Reuse Home Assistant quality-scale rules as a shared rubric before inventing repo-local expectations.
- Treat diagnostics, logs, support exports, and troubleshooting docs as one coupled surface because this repo has personal-data and legal-estate-data sensitivity signals.
- Separate CI evidence from repository-settings evidence. Branch protection, required checks, SHA-pinning enforcement, environment approvals, and Actions policy may matter, but they are often invisible from repo contents alone.
- Separate release-artifact trust from routine CI convenience. Official guidance is strongest on provenance for published or user-consumed artifacts, not every test run.
- Treat config-flow UX, reauth, reconfigure, and repair flows as product behavior, docs behavior, incident-recovery behavior, and test targets simultaneously.

## Source Links

- Home Assistant integration manifest: https://developers.home-assistant.io/docs/creating_integration_manifest/
- Home Assistant config flow: https://developers.home-assistant.io/docs/core/integration/config_flow
- Home Assistant integration diagnostics: https://developers.home-assistant.io/docs/core/integration_diagnostics
- Home Assistant testing guidance: https://developers.home-assistant.io/docs/development_testing/
- Home Assistant integration quality scale: https://developers.home-assistant.io/docs/core/integration-quality-scale/
- Home Assistant quality-scale rules: https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/
- Home Assistant config-flow coverage rule: https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/config-flow-test-coverage
- Home Assistant test-coverage rule: https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-coverage
- Home Assistant setup-failure rule: https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/test-before-setup
- Home Assistant troubleshooting-docs rule: https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/docs-troubleshooting/
- Home Assistant reauthentication rule: https://developers.home-assistant.io/docs/core/integration-quality-scale/rules/reauthentication-flow/
- Home Assistant custom integration localization: https://developers.home-assistant.io/docs/internationalization/custom_integration/
- GitHub Actions workflow syntax and permissions: https://docs.github.com/actions/using-workflows/workflow-syntax-for-github-actions
- GitHub `GITHUB_TOKEN` guidance: https://docs.github.com/en/actions/configuring-and-managing-workflows/authenticating-with-the-github_token
- GitHub Actions security hardening: https://docs.github.com/actions/learn-github-actions/security-hardening-for-github-actions
- GitHub Actions concurrency: https://docs.github.com/en/actions/concepts/workflows-and-actions/concurrency
- GitHub dependency review action: https://docs.github.com/en/code-security/supply-chain-security/understanding-your-software-supply-chain/configuring-the-dependency-review-action?apiVersion=2022-11-28
- GitHub artifact attestations: https://docs.github.com/en/actions/concepts/security/artifact-attestations
- GitHub Dependabot on Actions: https://docs.github.com/en/code-security/reference/supply-chain-security/dependabot-on-actions
- Pytest markers and strictness: https://docs.pytest.org/en/stable/how-to/mark.html
- Pytest reference for `strict_config` and `strict_markers`: https://docs.pytest.org/en/latest/reference/reference.html
- Pytest good integration practices: https://docs.pytest.org/en/stable/explanation/goodpractices.html
- pytest-asyncio configuration: https://pytest-asyncio.readthedocs.io/en/stable/reference/configuration.html
- Playwright CI guidance: https://playwright.dev/docs/ci
- Playwright Trace Viewer guidance: https://playwright.dev/docs/next/trace-viewer
- PyPI Trusted Publishing overview: https://docs.pypi.org/trusted-publishers/
- PyPI publishing with a trusted publisher: https://docs.pypi.org/trusted-publishers/using-a-publisher/
- PyPI attestations: https://docs.pypi.org/attestations/
- Python Packaging User Guide packaging flow: https://packaging.python.org/en/latest/flow/
- npm `package-lock.json`: https://docs.npmjs.com/cli/v11/configuring-npm/package-lock-json/

## Open Gaps

- `ai-and-prompt-workflow-review` likely needs targeted follow-up only if a real prompt/model/tool surface is confirmed in repo code or runtime config.
- `desktop-installer` was a planning signal, but repo-level packaging evidence still looks weak; downstream review may need a second pass to verify whether a real desktop distribution surface exists.
- GitHub repository settings are out of band. Child reviews may still need targeted follow-up on branch protection, required checks, environment approvals, SHA-pinning enforcement, OIDC permissions, and rulesets.
- Runtime observability and incident handling outside the repo remain unverified: log sinks, alert routing, support runbooks, release dashboards, and Home Assistant deployment context may require external confirmation.
- If downstream reviews need to judge HACS or Hassfest usage beyond basic workflow presence, they may need targeted follow-up against the upstream action READMEs and current Home Assistant custom-component validation expectations.
