# Conventions

## Quick Reference

| ID | Applies-when | Rule |
| --- | --- | --- |
| `conv-docs-001` | Editing `docs/` | Keep docs concise, scannable, and LLM-oriented. |
| `conv-review-001` | Running repo reviews | Save new timestamped review artifacts; do not overwrite prior runs. |
| `conv-review-002` | Running orchestrator sweeps | Use `review-orchestrator`; persist artifacts under `docs/review-orchestrator/`. |
| `conv-python-001` | Editing Python | Preserve strict typing and Ruff/Mypy compatibility from `pyproject.toml`. |
| `conv-ha-001` | Editing integration code | Keep Home Assistant integration logic inside `custom_components/ha_light_controller/`. |

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
