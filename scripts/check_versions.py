#!/usr/bin/env python3
"""Verify version strings are consistent across all project metadata files.

Checks manifest.json (source of truth for HA), pyproject.toml, CHANGELOG.md,
and package.json (if present). Exits non-zero on mismatch.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def read_manifest_version() -> str | None:
    path = ROOT / "custom_components" / "ha_light_controller" / "manifest.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())["version"]


def read_pyproject_version() -> str | None:
    path = ROOT / "pyproject.toml"
    if not path.exists():
        return None
    match = re.search(r'^version\s*=\s*"([^"]+)"', path.read_text(), re.MULTILINE)
    return match.group(1) if match else None


def read_changelog_version() -> str | None:
    path = ROOT / "CHANGELOG.md"
    if not path.exists():
        return None
    match = re.search(r"^## \[([^\]]+)\]", path.read_text(), re.MULTILINE)
    return match.group(1) if match else None


def read_package_json_version() -> str | None:
    path = ROOT / "package.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())["version"]


def main() -> int:
    truth = read_manifest_version()
    if truth is None:
        print("ERROR: manifest.json not found", file=sys.stderr)
        return 1

    sources: dict[str, str | None] = {
        "manifest.json": truth,
        "pyproject.toml": read_pyproject_version(),
        "CHANGELOG.md": read_changelog_version(),
        "package.json": read_package_json_version(),
    }

    ok = True
    for name, version in sources.items():
        if version is None:
            continue
        status = "OK" if version == truth else "MISMATCH"
        if status == "MISMATCH":
            ok = False
        print(f"  {name:30s} {version:10s} [{status}]")

    if ok:
        print(f"\nAll versions consistent: {truth}")
    else:
        print(f"\nERROR: versions must match manifest.json ({truth})", file=sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
