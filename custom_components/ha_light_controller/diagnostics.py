"""Diagnostics support for Light Controller integration."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_PRESETS

TO_REDACT = {"name", "entities", "entity_id"}


def _redact_dict(data: dict[str, Any], keys: set[str]) -> dict[str, Any]:
    """Redact values for specified keys in a dict."""
    return {k: "**REDACTED**" if k in keys else v for k, v in data.items()}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    presets_data = entry.data.get(CONF_PRESETS, {})

    # Redact preset details (names and entity IDs are PII-adjacent)
    redacted_presets = {}
    for pid, p in presets_data.items():
        redacted_presets[pid] = {
            "name": "**REDACTED**",
            "entity_count": len(p.get("entities", [])),
            "state": p.get("state", "unknown"),
            "has_targets": bool(p.get("targets")),
            "skip_verification": p.get("skip_verification", False),
        }

    # Runtime status from preset manager (if loaded)
    runtime_status: dict[str, Any] = {}
    if hasattr(entry, "runtime_data") and entry.runtime_data:
        pm = entry.runtime_data.preset_manager
        if pm:
            for pid in pm.presets:
                status = pm.get_status(pid)
                runtime_status[pid] = {
                    "status": status.status,
                    "last_activated": status.last_activated,
                }

    return {
        "config_entry_data": _redact_dict(
            {k: v for k, v in entry.data.items() if k != CONF_PRESETS},
            TO_REDACT,
        ),
        "options": dict(entry.options),
        "preset_count": len(presets_data),
        "presets": redacted_presets,
        "runtime_status": runtime_status,
    }
