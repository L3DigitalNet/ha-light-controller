# Codex Instructions for ha-light-controller

**Session state:** detect layout first. V2: read `docs/handoff/state.md`, then this file, then conventions; V1: read `docs/handoff.md`, then this file, then conventions.

**Full conventions reference:** [`docs/handoff/conventions.md`](docs/handoff/conventions.md) - LLM-targeted pattern library. Every convention follows the six-field schema (Applies-when / Rule / Code / Why / Sources / Related) with a Quick Reference table at the top for O(1) lookup. Do not introduce new patterns without checking conventions first.

**Detailed review workflows:** [AGENTS.reviews.md](AGENTS.reviews.md) - read this only for review-related tasks (review planning, review sweeps, code/security/test/etc. reviews). The verbose per-review routing, defaults, and orchestrator notes live there.

## Repo Purpose

Home Assistant custom integration for reliable light control, retries, verification, and presets.

## Branch Rules

- Make all changes on `testing`.
- Do not push to `main` without explicit permission.

## Commands

```bash
make test
make test-cov
make lint
make format
make type-check
make ci
```

## Key Rules

- Home Assistant is single-threaded asyncio: no blocking I/O on the event loop.
- All config keys and defaults live in `const.py`.
- Services register in `async_setup()`, not `async_setup_entry()`.
- Shared preset activation logic belongs in `PresetManager.activate_preset_with_options()`.
- Unit tests mock HA; live runtime checks happen against the separate dev server workspace when needed.
