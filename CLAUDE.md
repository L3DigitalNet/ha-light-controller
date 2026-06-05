# CLAUDE.md

**Session startup:** state is injected by the SessionStart hook (see `.claude/hooks/session_start.py`).

**Document layout (read on demand):**
- `docs/handoff/state.md` — live state + active incidents (auto-injected, do not read directly)
- `docs/handoff/deployed.md` — deployment truth
- `docs/handoff/architecture.md` — system graph + commands + testing + code style
- `docs/handoff/credentials.md` — OpenBao paths
- `docs/handoff/conventions.md` — pattern library (10 real conventions; Phase 5 deferred)
- `docs/handoff/sessions/` — monthly session logs (grep by date)
- `docs/handoff/bugs/` — per-file bug KB (grep by service or tag)
- `docs/handoff/specs-plans.md` — pointer into `docs/plans/`
