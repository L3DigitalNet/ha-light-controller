# CLAUDE.md

**Session startup:** state is injected by the SessionStart hook (see `.claude/hooks/session_start.py`).

**Document layout (read on demand):**
- `docs/state.md` — live state + active incidents (auto-injected, do not read directly)
- `docs/deployed.md` — deployment truth
- `docs/architecture.md` — system graph + commands + testing + code style
- `docs/credentials.md` — OpenBao paths
- `docs/conventions.md` — pattern library (10 real conventions; Phase 5 deferred)
- `docs/sessions/` — monthly session logs (grep by date)
- `docs/bugs/` — per-file bug KB (grep by service or tag)
- `docs/specs-plans.md` — pointer into `docs/plans/`
