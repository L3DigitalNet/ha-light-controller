"""Fixtures for integration tests using real HA test harness."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):  # noqa: PT004
    """Enable custom integrations in the test harness."""
    yield
