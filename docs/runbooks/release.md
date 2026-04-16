# Release Runbook

## Pre-release Checklist

1. All changes on `testing` branch, CI green
2. Run `python scripts/check_versions.py` — all files must match
3. Run `make ci` locally — all checks must pass
4. Update `CHANGELOG.md` with new version section

## Version Bump Order

1. `custom_components/ha_light_controller/manifest.json` — HA reads this
2. `pyproject.toml` — tooling reads this
3. `CHANGELOG.md` — humans read this
4. Run `uv lock` to update `uv.lock`
5. Run `python scripts/check_versions.py` to verify consistency

## Release Steps

1. Merge `testing` into `main`
2. Tag: `git tag vX.Y.Z && git push origin vX.Y.Z`
3. Create GitHub Release from the tag (copy CHANGELOG section as body)
4. HACS picks up the new release automatically via the GitHub Release

## Validation After Release

1. HACS: Settings > HACS > check that new version appears
2. Hassfest: GitHub Actions `Validate` workflow should be green
3. Install/update on a test instance before announcing

## Failure Triage

| Symptom | Likely cause | Fix |
|---------|-------------|-----|
| HACS doesn't see release | Missing GitHub Release object | Create Release from tag |
| Hassfest fails | `manifest.json` schema error | Fix and re-tag |
| CI fails on main | Test or lint regression | Fix on testing, re-merge |
| Users report breakage | Behavior change | See incident-disablement.md |
