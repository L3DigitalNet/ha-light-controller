# Handoff

> **Status: MIGRATING — do not edit.** Bug table will move to `docs/bugs/` in Phase 2.
> Live state is now in `docs/state.md`.

## Bugs Found and Fixed

1. **[fixed]** PLR-001 — `controller.py` `rgb_ok or kelvin_ok` → `and`. Color verification now correctly fails for single-mode targets. Commit: `cff8179`
2. **[fixed]** PLR-002 — Group-based preset overrides now expand to member lights. Commit: `71ee033`
3. **[fixed]** PLR-003 — Preset edit preserves preset_id via update_preset(). Commit: `a654fda`
4. **[fixed]** PLR-004 — Config flow editor now round-trips preset-level defaults. Commit: `71ee033`
5. **[fixed]** PLR-005 — Case-insensitive preset name uniqueness enforced. Commit: `15b3309`
6. **[fixed]** RR-001 / DEP-002 / DOC-004 — Version metadata synced to 0.4.0. Commit: `1fbcb58`
7. **[fixed]** CI-001 / DEP-004 — All Actions pinned to SHA. Commit: `45cf8ea`
8. **[fixed]** DEP-001 / CI-002 / TEST-001 — Deps consolidated into pyproject.toml + uv.lock. Commit: `610f7c1`
9. **[fixed]** OBS-001/002/003 — Diagnostics redacts PII, includes runtime status, preserves per-light VerificationResult. Commit: `bc53159`
10. **[fixed]** DEP-005 — Created scripts/setup for devcontainer. Commit: `51ee8e8`
11. **[fixed]** DOC-001/002/003/005 — Docs drift fixed across USAGE.md, CONTRIBUTING.md. Commit: `e4ffdf3`
12. **[fixed]** AI-001/003/004 — Settings.local.json, branch workflow reconciled, gitignore cleaned. Commit: `7bca89f`
13. **[fixed]** IR-001 — Incident disablement and release runbooks created. Commit: `cf13003`
14. **[fixed]** TEST-006 / RR-004/005 — 95% coverage gate, five new conventions. Commit: `ca6f8ef`
15. **[fixed]** CI-005 / DEP-003 / TEST-005 — Dead npm/Playwright surface removed. Commit: `715aff4`
