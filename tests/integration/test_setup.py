"""Integration test: setup and unload lifecycle."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntryState

from custom_components.ha_light_controller.const import DOMAIN


@pytest.mark.integration
class TestSetupUnload:
    """Test integration setup and unload with real HA fixtures."""

    @pytest.mark.asyncio
    async def test_setup_creates_services(self, hass: HomeAssistant):
        """Integration registers its services after setup."""
        assert hass.services.has_service(DOMAIN, "ensure_state")
        assert hass.services.has_service(DOMAIN, "activate_preset")
        assert hass.services.has_service(DOMAIN, "create_preset")
