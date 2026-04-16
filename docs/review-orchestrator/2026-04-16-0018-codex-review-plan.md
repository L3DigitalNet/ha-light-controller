# Codex Review Orchestrator Plan

Claude Code note: consider using the `superpowers:receiving-code-review` skill.

## Review Orchestrator Metadata
- repo_root: /home/chris/projects/ha-light-controller
- repo_name: ha-light-controller
- mode: sweep
- budget: standard
- scope: .
- current_branch: main
- head_commit: 11b525c1d0139673e78daf7a68a4557d3715f0ce
- working_tree_state: dirty
- execution_profile_used: review-sweep
- search_enabled: True
- codex_cli_mode: exec
- orchestrator_version: stage2

## Repo Scan Summary
- primary_repo_pattern: library-cli-tooling
- secondary_repo_patterns: document-centric-sensitive-data, sensitive-fastapi-internal-tool, retrieval-knowledge-base
- language_signals: python
- framework_signals: playwright, pytest
- behavior_signals: authentication, authorization, cli-tooling, webhooks
- artifact_signals: conventions-doc, github-actions, tests
- sensitivity_signals: legal-estate-data, personal-data
- deployment_signals: github-actions
- packaging_signals: desktop-installer
- nested_repo_signals: none
- existing_review_artifacts: none
- unknowns_that_reduce_confidence: none

## Repo Pattern Classification
- primary_repo_pattern: library-cli-tooling
- secondary_repo_patterns: document-centric-sensitive-data, sensitive-fastapi-internal-tool, retrieval-knowledge-base

## Framework And Artifact Signals
- framework_evidence: `{"playwright": ["CHANGELOG.md", "package-lock.json", "package.json"], "pytest": ["CONTRIBUTING.md", "package.json", "pyproject.toml", "CLAUDE.md", ".github/dependabot.yml", ".github/pull_request_template.md", ".github/workflows/ci.yml", ".vscode/launch.json"]}`
- behavior_evidence: `{"authentication": ["AGENTS.md", "CLAUDE.md", "docs/handoff.md"], "authorization": ["CODE_OF_CONDUCT.md", "AGENTS.md", "CLAUDE.md", ".claude/settings.json", ".github/workflows/ci.yml", ".github/workflows/validate.yml"], "cli-tooling": ["README.md", "USAGE.md", "custom_components/ha_light_controller/controller.py", "custom_components/ha_light_controller/services.yaml", "custom_components/ha_light_controller/strings.json", "custom_components/ha_light_controller/translations/en.json"], "webhooks": ["AGENTS.md"]}`
- artifact_evidence: `{"conventions-doc": ["docs/conventions.md"], "github-actions": [".github/workflows/ci.yml", ".github/workflows/validate.yml"], "tests": ["tests/__init__.py", "tests/conftest.py", "tests/test_button.py", "tests/test_config_flow.py", "tests/test_controller.py", "tests/test_diagnostics.py", "tests/test_init.py", "tests/test_preset_manager.py"]}`

## Conventions Inputs
- conventions_inputs_found: docs/conventions.md
- conventions_maturity: present
- likely_convention_heavy_reviews: architecture-boundary-review, api-contract-review, observability-review, test-suite-review, ci-cd-review
- missing_conventions_hotspots: none

## Available And Missing Review Skills
- available_review_skills: ai-and-prompt-workflow-review, api-contract-review, architecture-boundary-review, background-jobs-and-async-workflow-review, ci-cd-review, comprehensive-code-review, data-schema-migration-review, dependency-supply-chain-review, desktop-packaging-review, documentation-and-runbook-review, frontend-state-and-interaction-review, incident-readiness-review, integration-and-third-party-boundary-review, mcp-and-agent-tool-boundary-review, observability-review, performance-review, product-and-business-logic-review, release-readiness-review, retrieval-and-knowledge-base-review, shell-and-automation-script-review, test-suite-review, ui-ux-accessibility-review
- missing_review_skills: none

## Run Now
### release-readiness-review
- canonical_prompt: `perform a release readiness review`
- applicable: `yes`
- expected_value: `critical`
- confidence: `high`
- run_recommendation: `run_now`
- default_execution_group: `delivery-and-runtime`
- why_selected_or_skipped: Selected from weighted repo evidence.
- key_signals: delivery or packaging surface
- blocking_unknowns: none
- latest_existing_report: none

### ci-cd-review
- canonical_prompt: `perform a CI review`
- applicable: `yes`
- expected_value: `critical`
- confidence: `high`
- run_recommendation: `run_now`
- default_execution_group: `delivery-and-runtime`
- why_selected_or_skipped: Selected from weighted repo evidence.
- key_signals: CI workflow artifacts
- blocking_unknowns: none
- latest_existing_report: none

### test-suite-review
- canonical_prompt: `perform a test review`
- applicable: `yes`
- expected_value: `critical`
- confidence: `high`
- run_recommendation: `run_now`
- default_execution_group: `broad-integrative`
- why_selected_or_skipped: Selected from weighted repo evidence.
- key_signals: test files and tooling detected
- blocking_unknowns: none
- latest_existing_report: none

### product-and-business-logic-review
- canonical_prompt: `perform a product logic review`
- applicable: `yes`
- expected_value: `critical`
- confidence: `high`
- run_recommendation: `run_now`
- default_execution_group: `repo-shape-and-intent`
- why_selected_or_skipped: Selected from weighted repo evidence.
- key_signals: domain or workflow logic surface
- blocking_unknowns: none
- latest_existing_report: none

### dependency-supply-chain-review
- canonical_prompt: `perform a dependency review`
- applicable: `yes`
- expected_value: `critical`
- confidence: `high`
- run_recommendation: `run_now`
- default_execution_group: `boundary-and-trust`
- why_selected_or_skipped: Selected from weighted repo evidence.
- key_signals: dependency manifest surface
- blocking_unknowns: none
- latest_existing_report: none

### observability-review
- canonical_prompt: `perform an observability review`
- applicable: `yes`
- expected_value: `critical`
- confidence: `high`
- run_recommendation: `run_now`
- default_execution_group: `delivery-and-runtime`
- why_selected_or_skipped: Selected from weighted repo evidence.
- key_signals: none recorded
- blocking_unknowns: none
- latest_existing_report: none

### documentation-and-runbook-review
- canonical_prompt: `perform a documentation review`
- applicable: `yes`
- expected_value: `high`
- confidence: `high`
- run_recommendation: `run_now`
- default_execution_group: `repo-shape-and-intent`
- why_selected_or_skipped: Selected from weighted repo evidence.
- key_signals: documentation surface
- blocking_unknowns: none
- latest_existing_report: none

### ai-and-prompt-workflow-review
- canonical_prompt: `perform an AI workflow review`
- applicable: `yes`
- expected_value: `high`
- confidence: `high`
- run_recommendation: `run_now`
- default_execution_group: `contract-and-integration`
- why_selected_or_skipped: Selected from weighted repo evidence.
- key_signals: none recorded
- blocking_unknowns: none
- latest_existing_report: none

### incident-readiness-review
- canonical_prompt: `perform an incident readiness review`
- applicable: `yes`
- expected_value: `high`
- confidence: `high`
- run_recommendation: `run_now`
- default_execution_group: `delivery-and-runtime`
- why_selected_or_skipped: Selected from weighted repo evidence.
- key_signals: runtime operations surface
- blocking_unknowns: none
- latest_existing_report: none

## Consider Next
### api-contract-review
- canonical_prompt: `perform an API contract review`
- applicable: `yes`
- expected_value: `medium`
- confidence: `medium`
- run_recommendation: `consider_next`
- default_execution_group: `contract-and-integration`
- why_selected_or_skipped: Selected from weighted repo evidence. Medium-value review kept visible to avoid false negatives.
- key_signals: contract artifacts or endpoint surface
- blocking_unknowns: none
- latest_existing_report: none

### integration-and-third-party-boundary-review
- canonical_prompt: `perform an integration review`
- applicable: `yes`
- expected_value: `medium`
- confidence: `medium`
- run_recommendation: `consider_next`
- default_execution_group: `contract-and-integration`
- why_selected_or_skipped: Selected from weighted repo evidence. Medium-value review kept visible to avoid false negatives.
- key_signals: external integration surface
- blocking_unknowns: none
- latest_existing_report: none

### background-jobs-and-async-workflow-review
- canonical_prompt: `perform an async workflow review`
- applicable: `yes`
- expected_value: `medium`
- confidence: `medium`
- run_recommendation: `consider_next`
- default_execution_group: `state-data-and-workflow`
- why_selected_or_skipped: Selected from weighted repo evidence. Medium-value review kept visible to avoid false negatives.
- key_signals: none recorded
- blocking_unknowns: none
- latest_existing_report: none

### performance-review
- canonical_prompt: `perform a performance review`
- applicable: `yes`
- expected_value: `medium`
- confidence: `medium`
- run_recommendation: `consider_next`
- default_execution_group: `delivery-and-runtime`
- why_selected_or_skipped: Selected from weighted repo evidence. Medium-value review kept visible to avoid false negatives.
- key_signals: runtime or UI performance surface
- blocking_unknowns: none
- latest_existing_report: none

### architecture-boundary-review
- canonical_prompt: `perform an architecture review`
- applicable: `yes`
- expected_value: `medium`
- confidence: `medium`
- run_recommendation: `consider_next`
- default_execution_group: `repo-shape-and-intent`
- why_selected_or_skipped: Selected from weighted repo evidence. Medium-value review kept visible to avoid false negatives.
- key_signals: meaningful implementation surface
- blocking_unknowns: none
- latest_existing_report: none

### comprehensive-code-review
- canonical_prompt: `perform a code review`
- applicable: `yes`
- expected_value: `medium`
- confidence: `medium`
- run_recommendation: `consider_next`
- default_execution_group: `broad-integrative`
- why_selected_or_skipped: Selected from weighted repo evidence. Medium-value review kept visible to avoid false negatives.
- key_signals: meaningful implementation surface
- blocking_unknowns: none
- latest_existing_report: none

## Not Applicable
### mcp-and-agent-tool-boundary-review
- canonical_prompt: `perform an MCP review`
- applicable: `no`
- expected_value: `low`
- confidence: `high`
- run_recommendation: `skip_now`
- default_execution_group: `contract-and-integration`
- why_selected_or_skipped: No MCP or tool-boundary surface was detected.
- key_signals: none recorded
- blocking_unknowns: none
- latest_existing_report: none

### retrieval-and-knowledge-base-review
- canonical_prompt: `perform a retrieval review`
- applicable: `no`
- expected_value: `low`
- confidence: `high`
- run_recommendation: `skip_now`
- default_execution_group: `contract-and-integration`
- why_selected_or_skipped: No retrieval or knowledge-base surface was detected.
- key_signals: none recorded
- blocking_unknowns: none
- latest_existing_report: none

### data-schema-migration-review
- canonical_prompt: `perform a data review`
- applicable: `no`
- expected_value: `low`
- confidence: `high`
- run_recommendation: `skip_now`
- default_execution_group: `state-data-and-workflow`
- why_selected_or_skipped: No persistent schema or migration surface was detected.
- key_signals: none recorded
- blocking_unknowns: none
- latest_existing_report: none

### frontend-state-and-interaction-review
- canonical_prompt: `perform a frontend state review`
- applicable: `no`
- expected_value: `low`
- confidence: `high`
- run_recommendation: `skip_now`
- default_execution_group: `state-data-and-workflow`
- why_selected_or_skipped: No meaningful interactive client or desktop state surface was detected.
- key_signals: none recorded
- blocking_unknowns: none
- latest_existing_report: none

### desktop-packaging-review
- canonical_prompt: `perform a desktop packaging review`
- applicable: `no`
- expected_value: `low`
- confidence: `high`
- run_recommendation: `skip_now`
- default_execution_group: `delivery-and-runtime`
- why_selected_or_skipped: No desktop packaging surface was detected.
- key_signals: none recorded
- blocking_unknowns: none
- latest_existing_report: none

### shell-and-automation-script-review
- canonical_prompt: `perform a shell automation review`
- applicable: `no`
- expected_value: `low`
- confidence: `high`
- run_recommendation: `skip_now`
- default_execution_group: `delivery-and-runtime`
- why_selected_or_skipped: No meaningful shell automation surface was detected.
- key_signals: none recorded
- blocking_unknowns: none
- latest_existing_report: none

### ui-ux-accessibility-review
- canonical_prompt: `perform a UI review`
- applicable: `no`
- expected_value: `low`
- confidence: `high`
- run_recommendation: `skip_now`
- default_execution_group: `delivery-and-runtime`
- why_selected_or_skipped: No meaningful user-facing UI surface was detected.
- key_signals: none recorded
- blocking_unknowns: none
- latest_existing_report: none

## Execution Order
- 1. `product-and-business-logic-review`: repo-shape-and-intent / critical
- 2. `documentation-and-runbook-review`: repo-shape-and-intent / high
- 3. `dependency-supply-chain-review`: boundary-and-trust / critical
- 4. `ai-and-prompt-workflow-review`: contract-and-integration / high
- 5. `ci-cd-review`: delivery-and-runtime / critical
- 6. `observability-review`: delivery-and-runtime / critical
- 7. `release-readiness-review`: delivery-and-runtime / critical
- 8. `incident-readiness-review`: delivery-and-runtime / high
- 9. `test-suite-review`: broad-integrative / critical

## Planning Risks And Unknowns
- missing_evidence_that_could_change_prioritization: Sweep execution relies on non-interactive child Codex runs and will save a durable JSON manifest.
- environment_limitations: none recorded
- search_or_profile_limitations: execution profile `review-sweep` with search_enabled=True

## Claude Handoff
- highest_value_reviews_to_run_first: product-and-business-logic-review, documentation-and-runbook-review, dependency-supply-chain-review
- reviews_likely_to_change_conventions: architecture-boundary-review, api-contract-review, observability-review, test-suite-review, ci-cd-review
- reviews_to_revisit_after_major_changes: api-contract-review, integration-and-third-party-boundary-review, background-jobs-and-async-workflow-review, performance-review
- follow_up_questions_for_human_if_needed: none
