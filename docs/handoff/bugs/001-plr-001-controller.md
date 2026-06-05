---
bug_id: 1
date: 2026-04-16
title: "PLR-001 — `controller"
services: [ha-light-controller]
tags: [plr-001]
status: fixed
supersedes: null
superseded_by: null
---
# Bug 1: PLR-001 — `controller

## Summary

`controller.py` `rgb_ok or kelvin_ok` → `and`. Color verification now correctly fails for single-mode targets.

**Commit:** `cff8179`
